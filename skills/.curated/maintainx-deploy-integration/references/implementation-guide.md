# MaintainX Deploy Integration - Implementation Guide

> Full implementation details and code examples for the `maintainx-deploy-integration` skill.

# MaintainX Deploy Integration

## Overview

Deploy MaintainX integrations to production environments with Docker, Kubernetes, and cloud platform configurations.

## Prerequisites

- MaintainX integration tested and ready
- Docker installed
- Cloud platform account (GCP, AWS, or Azure)
- Kubernetes cluster (optional)

## Instructions

### Step 1: Dockerfile

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

# Production image
FROM node:20-alpine AS production

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Copy built artifacts
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

EXPOSE 3000

CMD ["node", "dist/index.js"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  maintainx-integration:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - MAINTAINX_API_KEY=${MAINTAINX_API_KEY}
      - LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

### Step 2: Kubernetes Manifests

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: maintainx-integration
---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: maintainx-secrets
  namespace: maintainx-integration
type: Opaque
stringData:
  MAINTAINX_API_KEY: "your-api-key-here"  # Use external secrets in production
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: maintainx-config
  namespace: maintainx-integration
data:
  NODE_ENV: "production"
  LOG_LEVEL: "info"
  MAINTAINX_BASE_URL: "https://api.getmaintainx.com/v1"
---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maintainx-integration
  namespace: maintainx-integration
  labels:
    app: maintainx-integration
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
        - name: maintainx-integration
          image: your-registry/maintainx-integration:latest
          ports:
            - containerPort: 3000
          envFrom:
            - configMapRef:
                name: maintainx-config
            - secretRef:
                name: maintainx-secrets
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
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
---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: maintainx-integration
  namespace: maintainx-integration
spec:
  selector:
    app: maintainx-integration
  ports:
    - protocol: TCP
      port: 80
      targetPort: 3000
  type: ClusterIP
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: maintainx-integration
  namespace: maintainx-integration
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - maintainx.your-domain.com
      secretName: maintainx-tls
  rules:
    - host: maintainx.your-domain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: maintainx-integration
                port:
                  number: 80
```

### Step 3: Google Cloud Run Deployment

```yaml
# cloudbuild.yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/maintainx-integration:$COMMIT_SHA', '.']

  # Push the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/maintainx-integration:$COMMIT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'maintainx-integration'
      - '--image'
      - 'gcr.io/$PROJECT_ID/maintainx-integration:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-secrets'
      - 'MAINTAINX_API_KEY=maintainx-api-key:latest'

images:
  - 'gcr.io/$PROJECT_ID/maintainx-integration:$COMMIT_SHA'
```

```bash
# Deploy script for Cloud Run
#!/bin/bash
# scripts/deploy-cloudrun.sh

set -e

PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="maintainx-integration"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Building image..."
docker build -t ${IMAGE}:latest .

echo "Pushing image..."
docker push ${IMAGE}:latest

echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE}:latest \
  --region ${REGION} \
  --platform managed \
  --set-secrets MAINTAINX_API_KEY=maintainx-api-key:latest \
  --set-env-vars NODE_ENV=production,LOG_LEVEL=info \
  --min-instances 1 \
  --max-instances 10 \
  --memory 256Mi \
  --cpu 1 \
  --timeout 60s \
  --concurrency 80

echo "Deployment complete!"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)'
```

### Step 4: AWS Lambda Deployment

```yaml
# serverless.yml
service: maintainx-integration

provider:
  name: aws
  runtime: nodejs20.x
  region: us-east-1
  memorySize: 256
  timeout: 30
  environment:
    NODE_ENV: production
    LOG_LEVEL: info

functions:
  api:
    handler: dist/lambda.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
    environment:
      MAINTAINX_API_KEY: ${ssm:/maintainx/api-key~true}

plugins:
  - serverless-offline

custom:
  serverless-offline:
    httpPort: 3000
```

```typescript
// src/lambda.ts
import serverless from 'serverless-http';
import { app } from './app';  // Your Express app

export const handler = serverless(app);
```

### Step 5: Health Check Endpoint

```typescript
// src/routes/health.ts
import { Router } from 'express';
import { MaintainXClient } from '../api/maintainx-client';

const router = Router();

// Basic health check
router.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
  });
});

// Readiness check (includes dependency checks)
router.get('/ready', async (req, res) => {
  const checks = {
    api: false,
    timestamp: new Date().toISOString(),
  };

  try {
    const client = new MaintainXClient();
    await client.getUsers({ limit: 1 });
    checks.api = true;
  } catch (error) {
    console.error('MaintainX API health check failed:', error);
  }

  const isReady = Object.values(checks).every(v => v === true || typeof v === 'string');

  res.status(isReady ? 200 : 503).json({
    status: isReady ? 'ready' : 'not_ready',
    checks,
  });
});

export { router as healthRouter };
```

### Step 6: GitHub Actions Deploy Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

env:
  PROJECT_ID: your-gcp-project
  REGION: us-central1
  SERVICE: maintainx-integration

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker
        run: gcloud auth configure-docker

      - name: Build and Push
        run: |
          docker build -t gcr.io/$PROJECT_ID/$SERVICE:$GITHUB_SHA .
          docker push gcr.io/$PROJECT_ID/$SERVICE:$GITHUB_SHA

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy $SERVICE \
            --image gcr.io/$PROJECT_ID/$SERVICE:$GITHUB_SHA \
            --region $REGION \
            --platform managed

      - name: Verify Deployment
        run: |
          URL=$(gcloud run services describe $SERVICE --region $REGION --format='value(status.url)')
          curl -f "$URL/health" || exit 1
```

## Output

- Dockerfile and docker-compose configured
- Kubernetes manifests created
- Cloud Run deployment configured
- Health check endpoints implemented
- CI/CD deploy workflow ready

## Deployment Checklist

- [ ] Docker image builds successfully
- [ ] Health check endpoint responds
- [ ] Secrets configured in target platform
- [ ] TLS/HTTPS enabled
- [ ] Scaling parameters set
- [ ] Monitoring configured
- [ ] Rollback procedure tested

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Google Cloud Run](https://cloud.google.com/run/docs)
- [AWS Lambda](https://docs.aws.amazon.com/lambda/)

## Next Steps

For webhook integration, see `maintainx-webhooks-events`.
