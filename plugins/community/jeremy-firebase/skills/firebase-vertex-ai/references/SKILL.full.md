---
name: firebase-vertex-ai
description: |
  Firebase platform expert with Vertex AI Gemini integration for Authentication, Firestore, Storage, Functions, Hosting, and AI-powered features. Use when asked to "setup firebase", "deploy to firebase", or "integrate vertex ai with firebase". Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Firebase Vertex Ai

This skill provides automated assistance for firebase vertex ai tasks.

## What This Skill Does

Production-ready Firebase platform operations specialist with deep Vertex AI Gemini integration expertise. Handles complete Firebase lifecycle including setup, development, deployment, security configuration, and AI-powered feature implementation.

### Core Capabilities

1. **Firebase Project Setup**: Initialize and configure Firebase projects with best practices
2. **Authentication Management**: Configure Auth providers (Email/Password, Google, GitHub, custom)
3. **Firestore Operations**: Database design, security rules, indexes, and queries
4. **Cloud Storage**: File uploads, security rules, signed URLs, and CDN
5. **Cloud Functions**: TypeScript/JavaScript serverless functions with triggers
6. **Firebase Hosting**: Static site deployment with custom domains and SSL
7. **Vertex AI Integration**: Gemini API for embeddings, chat, content analysis
8. **Security & Compliance**: Security rules, IAM, audit logging, data protection

## When This Skill Activates

### Trigger Phrases
- "Setup Firebase project"
- "Deploy to Firebase Hosting"
- "Create Firestore security rules"
- "Integrate Vertex AI with Firebase"
- "Deploy Cloud Functions"
- "Configure Firebase Authentication"
- "Generate embeddings with Gemini"
- "Build Firebase RAG system"
- "Optimize Firebase performance"
- "Firebase CI/CD pipeline"

### Use Cases
- Setting up new Firebase projects from scratch
- Migrating from other platforms (Supabase, AWS) to Firebase
- Building AI-powered applications with Vertex AI + Firebase
- Implementing RAG systems with Firestore vector search
- Deploying full-stack applications
- Setting up production security rules
- Optimizing Firebase costs and performance

## How It Works

### Phase 1: Project Initialization

**Firebase CLI Setup**:
```bash
# Install Firebase CLI


## Overview

This skill provides automated assistance for the described functionality.

## Prerequisites

- Appropriate file access permissions
- Required dependencies installed

## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps

## Examples

Example usage patterns will be demonstrated in context.
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize project
firebase init

# Select features:
# - Hosting
# - Functions
# - Firestore
# - Storage
# - Emulators
```

**Project Structure**:
```
firebase-project/
├── firebase.json                # Firebase configuration
├── .firebaserc                  # Project aliases
├── firestore.rules             # Firestore security rules
├── firestore.indexes.json      # Firestore indexes
├── storage.rules               # Storage security rules
├── functions/                  # Cloud Functions
│   ├── src/
│   │   ├── index.ts
│   │   ├── auth/              # Auth triggers
│   │   ├── firestore/         # Firestore triggers
│   │   └── vertex/            # Vertex AI functions
│   ├── package.json
│   └── tsconfig.json
├── public/                     # Hosting files (or dist/)
├── .env.local                  # Environment variables
└── README.md
```

### Phase 2: Firebase Authentication

**Setup Auth Providers**:
```javascript
// functions/src/auth/setup-auth.ts
import * as admin from 'firebase-admin';

admin.initializeApp();

// Create custom claims for role-based access
export const setUserRole = functions.https.onCall(async (data, context) => {
  if (!context.auth?.token.admin) {
    throw new functions.https.HttpsError(
      'permission-denied',
      'Only admins can set user roles'
    );
  }

  await admin.auth().setCustomUserClaims(data.userId, {
    role: data.role
  });

  return { success: true };
});

// Auth trigger: Create user profile on signup
export const onUserCreate = functions.auth.user().onCreate(async (user) => {
  const userDoc = {
    email: user.email,
    displayName: user.displayName,
    photoURL: user.photoURL,
    createdAt: admin.firestore.FieldValue.serverTimestamp(),
    role: 'user'
  };

  await admin.firestore()
    .collection('users')
    .doc(user.uid)
    .set(userDoc);
});
```

### Phase 3: Firestore Database Design

**Security Rules**:
```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Helper functions
    function isAuthenticated() {
      return request.auth != null;
    }

    function isOwner(userId) {
      return isAuthenticated() && request.auth.uid == userId;
    }

    function hasRole(role) {
      return isAuthenticated() &&
             get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == role;
    }

    // User profiles
    match /users/{userId} {
      allow read: if isAuthenticated();
      allow write: if isOwner(userId) || hasRole('admin');
    }

    // Public content
    match /posts/{postId} {
      allow read: if true;
      allow create: if isAuthenticated() &&
                       request.resource.data.authorId == request.auth.uid;
      allow update, delete: if isOwner(resource.data.authorId) || hasRole('admin');
    }

    // AI embeddings (for RAG)
    match /embeddings/{embeddingId} {
      allow read: if isAuthenticated();
      allow write: if hasRole('admin');
    }
  }
}
```

**Indexes Configuration**:
```json
// firestore.indexes.json
{
  "indexes": [
    {
      "collectionGroup": "posts",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "authorId", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "embeddings",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "category", "order": "ASCENDING" },
        { "fieldPath": "vector", "mode": "VECTOR", "dimensions": 768 }
      ]
    }
  ]
}
```

### Phase 4: Vertex AI Gemini Integration

**Embeddings Generation**:
```typescript
// functions/src/vertex/generate-embeddings.ts
import { VertexAI } from '@google-cloud/vertexai';
import * as admin from 'firebase-admin';
import * as functions from 'firebase-functions';

const vertex = new VertexAI({
  project: process.env.GCP_PROJECT_ID!,
  location: 'us-central1'
});

// Generate embeddings when document is created
export const generateEmbeddings = functions.firestore
  .document('posts/{postId}')
  .onCreate(async (snap, context) => {
    const post = snap.data();
    const text = post.title + ' ' + post.content;

    // Generate embedding with Vertex AI
    const model = vertex.getGenerativeModel({ model: 'text-embedding-004' });
    const result = await model.embedText({ text });

    // Store embedding in Firestore
    await admin.firestore()
      .collection('embeddings')
      .doc(context.params.postId)
      .set({
        postId: context.params.postId,
        vector: result.embedding.values,
        createdAt: admin.firestore.FieldValue.serverTimestamp()
      });
  });
```

**AI Content Analysis**:
```typescript
// functions/src/vertex/analyze-content.ts
import { VertexAI } from '@google-cloud/vertexai';

const vertex = new VertexAI({
  project: process.env.GCP_PROJECT_ID!,
  location: 'us-central1'
});

export const analyzeContent = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated');
  }

  const model = vertex.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });

  const prompt = `
Analyze this content for:
- Sentiment (positive/negative/neutral)
- Category (technology/business/entertainment/etc)
- Summary (1-2 sentences)
- Key topics (up to 5)

Content:
${data.content}

Return as JSON with keys: sentiment, category, summary, topics
  `;

  const result = await model.generateContent(prompt);
  const analysis = JSON.parse(result.response.text());

  return analysis;
});
```

**RAG System Implementation**:
```typescript
// functions/src/vertex/rag-query.ts
export const ragQuery = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'Authentication required');
  }

  // 1. Generate query embedding
  const queryModel = vertex.getGenerativeModel({ model: 'text-embedding-004' });
  const queryEmbedding = await queryModel.embedText({ text: data.query });

  // 2. Find similar documents in Firestore
  const embeddingsRef = admin.firestore().collection('embeddings');
  const similarDocs = await embeddingsRef
    .where('vector', 'near', {
      vector: queryEmbedding.embedding.values,
      distanceMeasure: 'COSINE',
      limit: 5
    })
    .get();

  // 3. Get full documents
  const documents = await Promise.all(
    similarDocs.docs.map(async (doc) => {
      const postDoc = await admin.firestore()
        .collection('posts')
        .doc(doc.data().postId)
        .get();
      return postDoc.data();
    })
  );

  // 4. Generate answer with Gemini using retrieved context
  const genModel = vertex.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });

  const contextText = documents
    .map(doc => `${doc.title}: ${doc.content}`)
    .join('\n\n');

  const prompt = `
Based on the following context, answer the user's question:

Context:
${contextText}

Question: ${data.query}

Provide a comprehensive answer based on the context. If the context doesn't contain enough information, say so.
  `;

  const result = await genModel.generateContent(prompt);

  return {
    answer: result.response.text(),
    sources: documents.map(doc => ({ title: doc.title, id: doc.id }))
  };
});
```

### Phase 5: Cloud Storage Operations

**Security Rules**:
```javascript
// storage.rules
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // User uploads
    match /users/{userId}/{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if request.auth.uid == userId &&
                      request.resource.size < 10 * 1024 * 1024 && // 10MB limit
                      request.resource.contentType.matches('image/.*');
    }

    // Public files
    match /public/{allPaths=**} {
      allow read: if true;
      allow write: if request.auth != null &&
                      request.auth.token.admin == true;
    }
  }
}
```

**File Upload Function**:
```typescript
// functions/src/storage/process-upload.ts
export const processUpload = functions.storage
  .object()
  .onFinalize(async (object) => {
    const filePath = object.name!;
    const contentType = object.contentType;

    // Generate thumbnail for images
    if (contentType?.startsWith('image/')) {
      // Use Sharp or ImageMagick to create thumbnail
      // Store in /thumbnails/ folder
    }

    // Update Firestore with file metadata
    await admin.firestore()
      .collection('files')
      .add({
        name: object.name,
        size: object.size,
        contentType: object.contentType,
        url: `https://storage.googleapis.com/${object.bucket}/${object.name}`,
        uploadedAt: admin.firestore.FieldValue.serverTimestamp()
      });
  });
```

### Phase 6: Firebase Hosting Deployment

**Configuration**:
```json
// firebase.json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "/api/**",
        "function": "api"
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      }
    ]
  },
  "functions": {
    "source": "functions",
    "runtime": "nodejs20"
  },
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  },
  "storage": {
    "rules": "storage.rules"
  }
}
```

**Deploy Script**:
```bash
#!/bin/bash
# deploy.sh - Deploy to Firebase

set -e

echo "Building application..."
npm run build

echo "Deploying to Firebase..."
firebase deploy --only hosting,functions,firestore:rules,storage:rules

echo "Deployment complete!"
firebase hosting:channel:list  # Show preview channels
```

### Phase 7: CI/CD Pipeline

**GitHub Actions**:
```yaml
# .github/workflows/firebase-deploy.yml
name: Deploy to Firebase

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Deploy to Firebase
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: ${{ secrets.GITHUB_TOKEN }}
          firebaseServiceAccount: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
          projectId: ${{ secrets.FIREBASE_PROJECT_ID }}
          channelId: live
```

## Tool Permissions

- **Read**: Analyze Firebase configs, security rules, existing code
- **Write**: Create new functions, rules, deployment configs
- **Edit**: Modify existing Firebase configurations
- **Grep**: Search for integration points, API usage
- **Glob**: Find related Firebase files
- **Bash**: Deploy to Firebase, run emulators, install dependencies

## Best Practices

### Security
- Always use security rules (never allow unrestricted access)
- Validate all inputs in Cloud Functions
- Use custom claims for role-based access control
- Enable App Check for production applications
- Rotate service account keys regularly

### Performance
- Use Firestore batch operations (up to 500 writes)
- Implement pagination for large queries
- Use Firebase Hosting CDN for static assets
- Optimize Cloud Functions cold starts
- Cache frequently accessed data

### Cost Optimization
- Use Firestore wisely (reads/writes cost money)
- Implement Cloud Functions timeouts
- Use Firebase Hosting cache headers
- Archive old data to Cloud Storage
- Set up billing alerts

### Development Workflow
- Use Firebase Emulators for local testing
- Separate dev/staging/prod projects
- Version control security rules
- Test security rules with emulator
- Monitor Cloud Functions logs

## Common Commands

```bash
# Local development
firebase emulators:start --only functions,firestore,hosting

# Deploy everything
firebase deploy

# Deploy specific services
firebase deploy --only hosting
firebase deploy --only functions
firebase deploy --only firestore:rules

# Hosting preview channels
firebase hosting:channel:deploy preview-branch

# View logs
firebase functions:log --only functionName

# Test security rules
firebase emulators:exec --only firestore "npm test"
```

## Troubleshooting

### Issue: "Permission Denied" in Firestore
- Check security rules allow the operation
- Verify user is authenticated
- Check custom claims if using role-based access

### Issue: Cloud Function Timeout
- Increase timeout in firebase.json (max 540s)
- Optimize slow operations
- Use async/await properly

### Issue: CORS Errors
- Set CORS headers in Cloud Functions
- Use Firebase Hosting rewrites to proxy functions

### Issue: High Costs
- Review Firestore reads/writes
- Optimize queries (use indexes)
- Implement caching
- Set up billing alerts

## Example Projects

See `examples/` directory for:
- Full-stack app with Auth + Firestore
- RAG system with Vertex AI embeddings
- File upload with Storage
- CI/CD with GitHub Actions

## Resources

- **Firebase Documentation**: https://firebase.google.com/docs
- **Vertex AI Integration**: https://cloud.google.com/vertex-ai/docs
- **Firebase CLI Reference**: https://firebase.google.com/docs/cli
- **Security Rules**: https://firebase.google.com/docs/rules

## Version History

- **1.0.0** (2025): Initial release with Vertex AI Gemini integration, production patterns, CI/CD templates

---

This skill provides comprehensive Firebase platform expertise with deep Vertex AI integration for building production-ready applications.
