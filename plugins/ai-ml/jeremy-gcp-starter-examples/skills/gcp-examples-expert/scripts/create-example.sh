#!/bin/bash
# create-example.sh - Create GCP starter example project

set -euo pipefail

EXAMPLE_TYPE="${1:-}"
PROJECT_NAME="${2:-gcp-example}"

usage() {
    cat <<EOF
Usage: $0 <EXAMPLE_TYPE> [PROJECT_NAME]

Create GCP starter example projects with best practices.

Example Types:
    cloud-run       - Cloud Run service with CI/CD
    gke             - GKE cluster with workloads
    vertex-ai       - Vertex AI model deployment
    bigquery        - BigQuery data pipeline
    functions       - Cloud Functions
    genkit          - Firebase Genkit app
    adk             - Agent Development Kit

Example:
    $0 cloud-run my-service
    $0 vertex-ai ml-model

EOF
    exit 1
}

if [[ -z "$EXAMPLE_TYPE" ]]; then
    usage
fi

echo "Creating GCP Starter Example"
echo "Type: $EXAMPLE_TYPE"
echo "Project: $PROJECT_NAME"
echo ""

mkdir -p "$PROJECT_NAME"

case "$EXAMPLE_TYPE" in
    cloud-run)
        cat > "$PROJECT_NAME/Dockerfile" <<'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 8080
CMD ["npm", "start"]
EOF
        cat > "$PROJECT_NAME/app.js" <<'EOF'
const express = require('express');
const app = express();
const port = process.env.PORT || 8080;

app.get('/', (req, res) => {
  res.json({ message: 'Hello from Cloud Run!' });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
EOF
        echo "✓ Cloud Run example created"
        ;;

    vertex-ai)
        cat > "$PROJECT_NAME/train.py" <<'EOF'
from google.cloud import aiplatform

aiplatform.init(project='your-project', location='us-central1')

model = aiplatform.Model.upload(
    display_name='my-model',
    artifact_uri='gs://your-bucket/model',
    serving_container_image_uri='gcr.io/cloud-aiplatform/prediction/tf2-cpu.2-8:latest'
)
print(f"Model deployed: {model.resource_name}")
EOF
        echo "✓ Vertex AI example created"
        ;;

    *)
        echo "Unknown example type: $EXAMPLE_TYPE"
        usage
        ;;
esac

echo ""
echo "Example created in: $PROJECT_NAME/"
