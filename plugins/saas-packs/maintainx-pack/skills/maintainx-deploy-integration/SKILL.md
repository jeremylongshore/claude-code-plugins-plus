---
name: maintainx-deploy-integration
description: |
  Deploy MaintainX integrations to production environments.
  Use when deploying to cloud platforms, configuring production environments,
  or automating deployment pipelines for MaintainX integrations.
  Trigger with phrases like "deploy maintainx", "maintainx deployment",
  "maintainx cloud deploy", "maintainx kubernetes", "maintainx docker".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Deploy Integration

## Overview
Deploy MaintainX integrations to production using Docker, Google Cloud Run, and Kubernetes with proper health checks and secret management.

## Prerequisites
- MaintainX integration tested and passing CI
- Docker installed
- Cloud platform account (GCP recommended)
- `MAINTAINX_API_KEY` for production environment

## Instructions

### Step 1: Dockerfile

```dockerfile
# Dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

FROM node:20-slim
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./
USER app
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

### Step 2: Health Check Endpoint

```typescript
// src/health.ts
import express from 'express';
import { MaintainXClient } from './client';

const app = express();

app.get('/health', async (req, res) => {
  const checks: Record<string, string> = {
    server: 'ok',
    apiKey: process.env.MAINTAINX_API_KEY ? 'configured' : 'missing',
  };

  try {
    const client = new MaintainXClient();
    await client.getUsers({ limit: 1 });
    checks.maintainxApi = 'ok';
  } catch (err: any) {
    checks.maintainxApi = `error: ${err.response?.status || err.message}`;
  }

  const allOk = Object.values(checks).every((v) => v === 'ok' || v === 'configured');
  res.status(allOk ? 200 : 503).json({
    status: allOk ? 'healthy' : 'degraded',
    checks,
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

app.get('/ready', (req, res) => {
  res.status(process.env.MAINTAINX_API_KEY ? 200 : 503).json({
    ready: !!process.env.MAINTAINX_API_KEY,
  });
});

export { app };
```

### Step 3: Deploy to Google Cloud Run

```bash
# Build and push container
PROJECT_ID="your-gcp-project"
REGION="us-central1"
SERVICE="maintainx-integration"

gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE

# Deploy with secrets
gcloud run deploy $SERVICE \
  --image gcr.io/$PROJECT_ID/$SERVICE \
  --region $REGION \
  --platform managed \
  --set-secrets "MAINTAINX_API_KEY=maintainx-api-key:latest" \
  --min-instances 1 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1 \
  --port 3000 \
  --allow-unauthenticated  # Only if webhook endpoint
```

### Step 4: Docker Compose for Multi-Service

```yaml
# docker-compose.yml
services:
  maintainx-sync:
    build: .
    env_file: .env.production
    ports: ["3000:3000"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: ["redis-data:/data"]

volumes:
  redis-data:
```

### Step 5: Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maintainx-integration
spec:
  replicas: 2
  selector:
    matchLabels:
      app: maintainx-integration
  template:
    metadata:
      labels:
        app: maintainx-integration
    spec:
      containers:
        - name: app
          image: gcr.io/your-project/maintainx-integration:latest
          ports:
            - containerPort: 3000
          env:
            - name: MAINTAINX_API_KEY
              valueFrom:
                secretKeyRef:
                  name: maintainx-secrets
                  key: api-key
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: maintainx-integration
spec:
  selector:
    app: maintainx-integration
  ports:
    - port: 80
      targetPort: 3000
  type: ClusterIP
```

```bash
# Create secret and deploy
kubectl create secret generic maintainx-secrets \
  --from-literal=api-key="$MAINTAINX_API_KEY"

kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/maintainx-integration
```

## Output
- Multi-stage Dockerfile with non-root user and health check
- `/health` and `/ready` endpoints for container orchestration
- Google Cloud Run deployment with Secret Manager integration
- Docker Compose setup for local production testing
- Kubernetes manifests with probes, secrets, and resource limits

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Container crashes on start | Missing `MAINTAINX_API_KEY` | Verify secret is mounted correctly |
| Health check fails | API key expired or network issue | Check `/health` response, rotate key |
| High memory usage | Unbounded caching or data retention | Set memory limits, add cache eviction |
| Cold start latency | Cloud Run scaling from zero | Set `min-instances: 1` |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Docker Best Practices](https://docs.docker.com/build/building/best-practices/)

## Next Steps
For webhook integration, see `maintainx-webhooks-events`.

## Examples

**AWS Lambda deployment (serverless)**:

```typescript
// lambda.ts
import { APIGatewayProxyHandler } from 'aws-lambda';
import { MaintainXClient } from './client';

export const handler: APIGatewayProxyHandler = async (event) => {
  const client = new MaintainXClient(process.env.MAINTAINX_API_KEY);

  if (event.path === '/webhook' && event.httpMethod === 'POST') {
    const body = JSON.parse(event.body || '{}');
    await processWebhook(body);
    return { statusCode: 200, body: '{"ok":true}' };
  }

  return { statusCode: 404, body: '{"error":"not found"}' };
};
```
