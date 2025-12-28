#!/bin/bash
# setup-firestore.sh - Setup Firestore for Firebase/GCP project

set -euo pipefail

PROJECT_ID="${1:-${GCP_PROJECT_ID:-}}"

if [[ -z "$PROJECT_ID" ]]; then
    echo "Usage: $0 <PROJECT_ID>"
    echo "Setup Firestore database with security rules"
    exit 1
fi

echo "Setting up Firestore"
echo "Project: $PROJECT_ID"
echo ""

# Enable Firestore API
echo "Enabling Firestore API..."
gcloud services enable firestore.googleapis.com --project="$PROJECT_ID"

# Create Firestore database (Native mode)
echo "Creating Firestore database..."
gcloud firestore databases create \
    --location=us-central1 \
    --project="$PROJECT_ID" || echo "Database may already exist"

# Create security rules file
cat > firestore.rules <<'EOF'
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User documents
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Public documents
    match /public/{document=**} {
      allow read: if true;
      allow write: if request.auth != null;
    }

    // A2A agent communication
    function isServiceAccount() {
      return request.auth.token.email.matches('.*@.*\\.iam\\.gserviceaccount\\.com$');
    }

    match /agent_sessions/{sessionId} {
      allow read, write: if isServiceAccount();
    }

    match /agent_memory/{agentId}/{document=**} {
      allow read, write: if isServiceAccount();
    }
  }
}
EOF

echo "✓ Security rules created: firestore.rules"
echo ""
echo "Deploy security rules with:"
echo "  firebase deploy --only firestore:rules"
