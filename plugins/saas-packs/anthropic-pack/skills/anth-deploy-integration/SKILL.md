---
name: anth-deploy-integration
description: |
  Deploy Claude API integrations to production cloud environments.
  Use when deploying Claude-powered services to Docker, Cloud Run, ECS,
  or Kubernetes with proper secret management and health checks.
  Trigger with phrases like "deploy anthropic", "claude production deploy",
  "ship claude integration", "anthropic cloud deployment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Deploy Integration

## Overview

Deploy Claude API integrations with proper secret management, health checks, and rollback procedures across Docker, GCP Cloud Run, and Kubernetes.

## Docker Deployment

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
ENV ANTHROPIC_API_KEY=""
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```python
# src/main.py
from fastapi import FastAPI, HTTPException
import anthropic

app = FastAPI()
client = anthropic.Anthropic()

@app.get("/health")
async def health():
    try:
        count = client.messages.count_tokens(
            model="claude-haiku-4-20250514",
            messages=[{"role": "user", "content": "ping"}]
        )
        return {"status": "healthy", "api": "connected"}
    except Exception as e:
        raise HTTPException(503, detail=str(e))
```

## GCP Cloud Run

```bash
echo -n "sk-ant-api03-..." | gcloud secrets create anthropic-key --data-file=-

gcloud run deploy claude-service \
  --image gcr.io/my-project/claude-service \
  --set-secrets ANTHROPIC_API_KEY=anthropic-key:latest \
  --min-instances 1 --max-instances 10 \
  --memory 512Mi --timeout 120s
```

## Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: claude-service }
spec:
  replicas: 3
  strategy: { type: RollingUpdate, rollingUpdate: { maxUnavailable: 1 } }
  template:
    spec:
      containers:
        - name: app
          env:
            - name: ANTHROPIC_API_KEY
              valueFrom:
                secretKeyRef: { name: anthropic-secrets, key: api-key }
          livenessProbe:
            httpGet: { path: /health, port: 8000 }
            periodSeconds: 30
```

## Rollback

```bash
# Cloud Run
gcloud run services update-traffic claude-service --to-revisions=PREVIOUS=100

# Kubernetes
kubectl rollout undo deployment/claude-service
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Container crash on start | Missing API key env var | Verify secret binding |
| Health check fails | Key invalid in prod | Test key with curl |
| 429 after scaling up | More replicas = more RPM | Shared rate limiter (Redis) |

## Resources

- [API Getting Started](https://docs.anthropic.com/en/api/getting-started)
- [API Status](https://status.anthropic.com)

## Next Steps

For event-driven patterns, see `anth-webhooks-events`.
