#!/bin/bash
# init-firebase.sh - Initialize Firebase project with Vertex AI

set -euo pipefail

PROJECT_NAME="${1:-firebase-project}"

echo "Initializing Firebase Project with Vertex AI Integration"
echo "Project: $PROJECT_NAME"
echo ""

mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Check Firebase CLI
if ! command -v firebase &> /dev/null; then
    echo "Installing Firebase CLI..."
    npm install -g firebase-tools
fi

# Initialize Firebase project
echo "Initializing Firebase..."
firebase init

# Create project structure
mkdir -p functions/src/{auth,firestore,vertex,storage}
mkdir -p public

# Create .env.local
cat > .env.local <<'EOF'
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
EOF

# Create Vertex AI integration template
cat > functions/src/vertex/embeddings.ts <<'EOF'
import { VertexAI } from '@google-cloud/vertexai';
import * as admin from 'firebase-admin';
import * as functions from 'firebase-functions';

const vertex = new VertexAI({
  project: process.env.GCP_PROJECT_ID!,
  location: 'us-central1'
});

export const generateEmbeddings = functions.firestore
  .document('posts/{postId}')
  .onCreate(async (snap, context) => {
    const post = snap.data();
    const text = post.title + ' ' + post.content;

    const model = vertex.getGenerativeModel({ model: 'text-embedding-004' });
    const result = await model.embedText({ text });

    await admin.firestore()
      .collection('embeddings')
      .doc(context.params.postId)
      .set({
        postId: context.params.postId,
        vector: result.embedding.values,
        createdAt: admin.firestore.FieldValue.serverTimestamp()
      });
  });
EOF

echo "✓ Firebase project initialized with Vertex AI integration"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_NAME"
echo "  npm install --prefix functions"
echo "  firebase deploy"
