# Firebase Vertex AI: Implementation Guide

## Firebase Project Structure

```
project-root/
├── firebase.json                 # Service config, rewrites, emulators
├── .firebaserc                   # Project aliases (dev/staging/prod)
├── firestore.rules               # Security rules (version controlled)
├── firestore.indexes.json        # Composite indexes
├── storage.rules                 # Storage security rules
├── functions/
│   ├── package.json              # @google-cloud/vertexai, firebase-admin
│   ├── tsconfig.json             # strict: true, target: es2022
│   └── src/
│       ├── index.ts              # Barrel file: exports all functions
│       ├── config.ts             # Secret definitions, shared constants
│       ├── vertex/               # chat.ts, embeddings.ts, moderation.ts
│       ├── middleware/            # auth.ts, validation.ts
│       └── triggers/             # on-user-create.ts, on-post-create.ts
├── public/ or dist/              # Hosting static assets
└── .gitignore                    # Must include: .env*, serviceAccount*.json
```

## Cloud Functions + Vertex AI Pattern

### Singleton Client

Create one VertexAI instance per cold start, not per request:

```typescript
// functions/src/vertex/client.ts
import { VertexAI, GenerativeModel } from "@google-cloud/vertexai";
let _vertex: VertexAI | null = null;

export function getVertex(projectId: string): VertexAI {
  if (!_vertex) _vertex = new VertexAI({ project: projectId, location: "us-central1" });
  return _vertex;
}
export function getChatModel(projectId: string): GenerativeModel {
  return getVertex(projectId).getGenerativeModel({ model: "gemini-2.5-flash" });
}
```

### Secret Management

```typescript
// functions/src/config.ts — define at module scope
import { defineSecret } from "firebase-functions/params";
export const gcpProjectId = defineSecret("GCP_PROJECT_ID");
// Provision: firebase functions:secrets:set GCP_PROJECT_ID

// functions/src/vertex/chat.ts — reference in function options
export const chat = onCall(
  { secrets: [gcpProjectId], memory: "512MiB", timeoutSeconds: 120 },
  async (req) => { const model = getChatModel(gcpProjectId.value()); /* ... */ }
);
```

### Error Handling with Retry

```typescript
async function callWithRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try { return await fn(); }
    catch (err: any) {
      const retryable = ["INTERNAL", "DEADLINE_EXCEEDED", "RESOURCE_EXHAUSTED"];
      if (attempt === maxRetries || !retryable.includes(err.code)) throw err;
      await new Promise((r) => setTimeout(r, Math.pow(2, attempt) * 1000 + Math.random() * 500));
    }
  }
  throw new Error("Unreachable");
}
```

## Security Rules Design

Deny by default, allowlist per collection:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} { allow read, write: if false; }

    function isAuth() { return request.auth != null; }
    function isOwner(uid) { return isAuth() && request.auth.uid == uid; }
    function hasRole(role) {
      return isAuth() && get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == role;
    }

    match /users/{userId} {
      allow read: if isOwner(userId) || hasRole('admin');
      allow create: if isOwner(userId);
      allow update: if isOwner(userId) &&
        !request.resource.data.diff(resource.data).affectedKeys().hasAny(['role', 'createdAt']);
    }
    match /posts/{postId} {
      allow read: if true;
      allow create: if isAuth() && request.resource.data.authorId == request.auth.uid
        && request.resource.data.keys().hasAll(['title', 'content', 'authorId'])
        && request.resource.data.title is string && request.resource.data.title.size() <= 200;
      allow update: if isOwner(resource.data.authorId);
      allow delete: if isOwner(resource.data.authorId) || hasRole('admin');
    }
    match /embeddings/{id} { allow read: if isAuth(); allow write: if hasRole('admin'); }
    match /users/{userId}/conversations/{convId} { allow read, write: if isOwner(userId); }
  }
}
```

## Emulator Testing Strategy

### Configuration

```json
{ "emulators": {
  "auth": { "port": 9099 }, "functions": { "port": 5001 },
  "firestore": { "port": 8080 }, "hosting": { "port": 5000 },
  "storage": { "port": 9199 }, "ui": { "enabled": true, "port": 4000 }
}}
```

### Rules Unit Tests

```typescript
import { initializeTestEnvironment, assertSucceeds, assertFails } from "@firebase/rules-unit-testing";
const testEnv = await initializeTestEnvironment({
  projectId: "demo-test",
  firestore: { rules: readFileSync("firestore.rules", "utf8") },
});

const alice = testEnv.authenticatedContext("alice");
await assertSucceeds(alice.firestore().collection("users").doc("alice").get());
const unauth = testEnv.unauthenticatedContext();
await assertFails(unauth.firestore().collection("users").doc("alice").get());
```

### Smoke Test

```bash
firebase emulators:start --only auth,functions,firestore &
sleep 5
curl -sf http://localhost:5001/demo-project/us-central1/health || { echo "FAIL"; exit 1; }
echo "PASS"
```

## Deployment Pipeline

Deploy in dependency order to avoid broken rewrites:

1. `firebase deploy --only firestore:rules` -- security rules first
2. `firebase deploy --only firestore:indexes` -- indexes (may take minutes)
3. `firebase deploy --only storage:rules` -- storage security
4. `firebase deploy --only functions` -- backend logic
5. `firebase deploy --only hosting` -- frontend (depends on function rewrites)

### CI/CD with GitHub Actions

```yaml
name: Deploy Firebase
on: { push: { branches: [main] } }
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci && cd functions && npm ci && npm run build && cd .. && npm run build && npm test
      - uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: ${{ secrets.GITHUB_TOKEN }}
          firebaseServiceAccount: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
          projectId: ${{ secrets.FIREBASE_PROJECT_ID }}
          channelId: live
```

## Environment Management

### .firebaserc

```json
{ "projects": { "default": "myapp-dev", "staging": "myapp-staging", "prod": "myapp-prod" } }
```

### Switching and Deploying

```bash
firebase use staging && firebase deploy --only functions
firebase use prod && firebase deploy --only functions
```

### Per-Environment Secrets

Each Firebase project has its own Secret Manager. Set secrets per project:

```bash
firebase use staging && firebase functions:secrets:set GCP_PROJECT_ID
firebase use prod && firebase functions:secrets:set GCP_PROJECT_ID
```

### Non-Secret Environment Config

Use `defineString` for non-secret values, set via `functions/.env.<project>`:

```typescript
import { defineString } from "firebase-functions/params";
const environment = defineString("ENVIRONMENT", { default: "dev" });
```

```
# functions/.env.myapp-staging
ENVIRONMENT=staging
VERTEX_REGION=us-central1
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
