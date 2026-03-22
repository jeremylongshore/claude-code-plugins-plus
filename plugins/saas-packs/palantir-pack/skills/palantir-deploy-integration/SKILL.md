---
name: palantir-deploy-integration
description: |
  Deploy Palantir Foundry integrations to cloud platforms with secrets management.
  Use when deploying Foundry-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy palantir", "foundry deploy",
  "palantir production deploy", "foundry Cloud Run".
allowed-tools: Read, Write, Edit, Bash(gcloud:*), Bash(docker:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, deployment, cloud]
compatible-with: claude-code, codex, openclaw
---

# Palantir Deploy Integration

## Overview
Deploy Foundry-integrated applications to cloud platforms (GCP Cloud Run, AWS Lambda, Docker) with proper secrets management and health checks.

## Prerequisites
- Passing CI tests: `palantir-ci-integration`
- Production OAuth2 credentials from Developer Console
- Cloud platform CLI configured (gcloud, aws, etc.)

## Instructions

### Step 1: Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 2: Deploy to Google Cloud Run
```bash
set -euo pipefail
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="foundry-integration"
REGION="us-central1"

# Build and push container
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Deploy with secrets from Secret Manager
gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
  --region "$REGION" \
  --set-secrets "FOUNDRY_HOSTNAME=foundry-hostname:latest" \
  --set-secrets "FOUNDRY_CLIENT_ID=foundry-client-id:latest" \
  --set-secrets "FOUNDRY_CLIENT_SECRET=foundry-client-secret:latest" \
  --min-instances 1 \
  --max-instances 10 \
  --timeout 60 \
  --allow-unauthenticated
```

### Step 3: Health Check Endpoint
```python
# src/main.py
from fastapi import FastAPI
import foundry, os

app = FastAPI()

@app.get("/health")
async def health():
    try:
        client = get_foundry_client()
        list(client.ontologies.Ontology.list())
        return {"status": "healthy", "foundry": "connected"}
    except Exception as e:
        return {"status": "degraded", "foundry": str(e)}, 503
```

### Step 4: Environment-Specific Configuration
```python
# src/config.py
import os
from dataclasses import dataclass

@dataclass
class FoundryConfig:
    hostname: str
    client_id: str
    client_secret: str
    scopes: list[str]

    @classmethod
    def from_env(cls) -> "FoundryConfig":
        env = os.environ.get("ENVIRONMENT", "development")
        scopes_map = {
            "development": ["api:read-data"],
            "staging": ["api:read-data", "api:write-data"],
            "production": ["api:read-data", "api:write-data", "api:ontology-read"],
        }
        return cls(
            hostname=os.environ["FOUNDRY_HOSTNAME"],
            client_id=os.environ["FOUNDRY_CLIENT_ID"],
            client_secret=os.environ["FOUNDRY_CLIENT_SECRET"],
            scopes=scopes_map.get(env, ["api:read-data"]),
        )
```

## Output
- Containerized Foundry integration deployed to cloud platform
- Secrets injected via cloud secrets manager
- Health check endpoint verifying Foundry connectivity
- Environment-specific scope configuration

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| Container fails to start | Missing env vars | Verify all secrets are mounted |
| Health check fails | Foundry unreachable | Check VPC/firewall rules |
| Cold start timeout | SDK initialization slow | Set min-instances to 1 |
| Secret rotation breaks app | Old secret revoked | Deploy new secret before revoking old |

## Resources
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Foundry Authentication](https://www.palantir.com/docs/foundry/api/general/overview/authentication)

## Next Steps
For observability setup, see `palantir-observability`.
