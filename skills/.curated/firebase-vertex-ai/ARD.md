# ARD: Firebase Vertex AI Skill

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

This skill operates within the Firebase ecosystem on Google Cloud Platform. The primary integration points are:

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐
│  Client App  │────▶│  Firebase Hosting │────▶│ Cloud Functions│
│  (Browser)   │     │  (CDN + Rewrites) │     │  (Node.js 20)  │
└─────────────┘     └──────────────────┘     └───────┬───────┘
                                                      │
                    ┌──────────────────┐              │
                    │  Firebase Auth    │◀─────────────┤
                    │  (Identity)       │              │
                    └──────────────────┘              │
                                                      ├──▶ Vertex AI (Gemini)
                    ┌──────────────────┐              │
                    │  Cloud Firestore  │◀─────────────┤
                    │  (Document DB)    │              │
                    └──────────────────┘              │
                                                      │
                    ┌──────────────────┐              │
                    │  Secret Manager   │◀─────────────┘
                    │  (Credentials)    │
                    └──────────────────┘
```

### External Systems

| System | Role | Interface |
|--------|------|-----------|
| Firebase Auth | Identity provider, JWT token issuer | Admin SDK `auth()`, client SDK `signInWith*` |
| Cloud Firestore | Document database, security rules engine | Admin SDK `firestore()`, REST API |
| Cloud Functions | Serverless compute, HTTP/event triggers | `firebase-functions` SDK, HTTPS callable |
| Firebase Hosting | Static asset CDN, function rewrites | `firebase.json` rewrites config |
| Vertex AI | Gemini model inference (chat, embeddings) | `@google-cloud/vertexai` SDK |
| Secret Manager | API key and credential storage | `firebase-functions` secrets config |
| Cloud Storage | File storage with security rules | Admin SDK `storage()` |

## Data Flow

### Primary Flow: Client Request to Gemini Response

```
1. Client sends authenticated request to /api/chat
2. Firebase Hosting rewrites /api/** to Cloud Function
3. Cloud Function verifies Firebase Auth token (context.auth)
4. Function reads user context from Firestore (optional)
5. Function calls Vertex AI Gemini with prompt + context
6. Gemini returns generated content
7. Function stores result in Firestore (optional)
8. Function returns structured JSON to client
```

### Initialization Flow

```
1. firebase init → select Functions, Firestore, Hosting, Emulators
2. Install @google-cloud/vertexai in functions/
3. Configure secrets: firebase functions:secrets:set VERTEX_API_KEY
4. Write firestore.rules with auth helpers
5. Write firestore.indexes.json for any composite queries
6. firebase emulators:start → verify locally
7. firebase deploy --only hosting,functions,firestore → production
```

### Embedding + RAG Flow

```
1. Document created in Firestore (posts/{postId})
2. Firestore onCreate trigger fires Cloud Function
3. Function calls Vertex AI text-embedding-004 model
4. Embedding vector stored in embeddings/{postId}
5. Query: user sends search text
6. Function generates query embedding
7. Firestore vector search finds nearest documents
8. Function calls Gemini with retrieved context + question
9. Gemini returns grounded answer with source references
```

## Design Decisions

### DD-1: Cloud Functions as AI Backend

**Decision**: All Vertex AI calls run in Cloud Functions, never from client-side code.

**Rationale**: Client-side Gemini calls would expose API keys in browser network traffic. Cloud Functions authenticate via service account identity (Application Default Credentials), eliminating key exposure. Functions also enable input validation, rate limiting, and structured logging before the model call.

**Trade-off**: Adds ~100ms network latency for the function hop. Acceptable given Gemini inference takes 1-4 seconds.

### DD-2: Secret Manager for API Keys

**Decision**: Use `defineSecret()` from `firebase-functions/v2` to bind secrets from Secret Manager at function deploy time.

**Rationale**: Environment variables in `.env` files risk being committed to version control. Firebase's `defineSecret()` integration provisions secrets in Secret Manager and injects them at runtime without filesystem exposure.

**Example**:

```typescript
import { defineSecret } from "firebase-functions/params";
const vertexKey = defineSecret("VERTEX_API_KEY");

export const chat = onCall({ secrets: [vertexKey] }, async (req) => {
  // vertexKey.value() available at runtime
});
```

### DD-3: Emulator-First Development

**Decision**: All generated code includes emulator configuration and local smoke test commands.

**Rationale**: Firebase Emulator Suite replicates Auth, Firestore, Functions, and Hosting locally. Testing against emulators avoids production data corruption, eliminates billing during development, and provides sub-second feedback. The `firebase.json` emulators block is generated with fixed ports to avoid conflicts.

**Configuration**:

```json
{
  "emulators": {
    "auth": { "port": 9099 },
    "functions": { "port": 5001 },
    "firestore": { "port": 8080 },
    "hosting": { "port": 5000 },
    "ui": { "enabled": true, "port": 4000 }
  }
}
```

### DD-4: Locked-Down Security Rules by Default

**Decision**: Generated `firestore.rules` deny all access by default. Each collection gets explicit, minimal rules.

**Rationale**: Firebase's default rules allow open access for 30 days after project creation, then lock down. Many tutorials leave rules open. This skill generates production-grade rules from the start with helper functions for `isAuthenticated()`, `isOwner()`, and `hasRole()`.

### DD-5: TypeScript for Cloud Functions

**Decision**: All generated Cloud Functions use TypeScript with strict mode.

**Rationale**: TypeScript catches type errors at build time (especially important for Vertex AI response parsing), provides better IDE support, and is the default for `firebase init functions` since Firebase CLI v12. The `functions/tsconfig.json` enables `strict: true` and targets `es2022`.

### DD-6: Gemini Model Selection

**Decision**: Default to `gemini-2.5-flash` for general use; recommend `gemini-2.5-pro` for complex reasoning tasks.

**Rationale**: Flash provides the best latency/cost ratio for most Firebase use cases (chat, content analysis, moderation). Pro is reserved for multi-step reasoning or large-context RAG queries where quality matters more than speed.

## Component Design

### Cloud Function Structure

```
functions/
├── src/
│   ├── index.ts              # Function exports (barrel file)
│   ├── config.ts             # Project config, secret definitions
│   ├── middleware/
│   │   ├── auth.ts           # Token verification helpers
│   │   └── validation.ts     # Input schema validation (zod)
│   ├── vertex/
│   │   ├── client.ts         # VertexAI client singleton
│   │   ├── chat.ts           # Chat completion function
│   │   ├── embeddings.ts     # Embedding generation
│   │   └── moderation.ts     # Content moderation
│   └── triggers/
│       ├── on-user-create.ts # Auth trigger: profile creation
│       └── on-post-create.ts # Firestore trigger: auto-embed
├── package.json
└── tsconfig.json
```

### Security Rules Architecture

Rules use a layered approach:

1. **Global helpers**: `isAuthenticated()`, `isOwner(uid)`, `hasRole(role)`
2. **Collection rules**: Each collection match block references helpers
3. **Field validation**: `request.resource.data` checks enforce schema at the rules layer
4. **Admin override**: `hasRole('admin')` provides emergency access without rule changes

### Environment Strategy

| Environment | Firebase Project | Vertex AI Region | Purpose |
|-------------|-----------------|------------------|---------|
| local | demo-project (emulator) | N/A (mocked) | Development |
| dev | myapp-dev | us-central1 | Integration testing |
| staging | myapp-staging | us-central1 | Pre-production validation |
| prod | myapp-prod | us-central1 | Production traffic |

Project aliases managed via `.firebaserc`:

```json
{
  "projects": {
    "default": "myapp-dev",
    "staging": "myapp-staging",
    "prod": "myapp-prod"
  }
}
```

## Failure Modes and Recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Vertex AI quota exceeded | HTTP 429 from Gemini API | Exponential backoff with jitter; fallback to cached response |
| Function cold start > 10s | Cloud Monitoring latency metric | Set `minInstances: 1` for critical functions |
| Firestore write contention | ABORTED error on transaction | Retry with exponential backoff (Admin SDK auto-retries) |
| Auth token expired | 401 from callable function | Client SDK auto-refreshes; function returns clear error |
| Secret not found | Function fails to start | `firebase functions:secrets:set` before deploy |
| Missing composite index | Firestore FAILED_PRECONDITION | Deploy `firestore.indexes.json`; error message includes exact index URL |

## Observability

### Structured Logging

```typescript
import { logger } from "firebase-functions/v2";

logger.info("Gemini call completed", {
  model: "gemini-2.5-flash",
  inputTokens: usage.promptTokenCount,
  outputTokens: usage.candidatesTokenCount,
  latencyMs: Date.now() - startTime,
  userId: context.auth?.uid,
});
```

### Key Metrics to Monitor

- `function/execution_count` by function name and status
- `function/execution_times` p50/p95/p99
- Vertex AI `aiplatform.googleapis.com/prediction/online/prediction_count`
- Firestore `firestore.googleapis.com/document/read_count` and `write_count`
- Billing alerts at 50%, 80%, 100% of monthly budget
