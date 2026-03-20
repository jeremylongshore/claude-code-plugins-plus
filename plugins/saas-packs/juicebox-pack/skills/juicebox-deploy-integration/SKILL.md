---
name: juicebox-deploy-integration
description: |
  Deploy Juicebox integrations to production.
  Use when deploying to cloud platforms, configuring production environments,
  or setting up infrastructure for Juicebox.
  Trigger with phrases like "deploy juicebox", "juicebox production deploy",
  "juicebox infrastructure", "juicebox cloud setup".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Deploy Integration

## Overview
Deploy a Juicebox-powered people search application to production with proper secret management, Docker containerization, health checks, and post-deployment verification. Covers AWS Secrets Manager and GCP Secret Manager for credential storage, plus pre-flight and post-deployment validation against the Juicebox API. Auth uses `Authorization: token {username}:{api_token}`.

## Prerequisites
- Juicebox production API credentials (username + token from https://juicebox.ai/settings)
- Docker installed locally
- Cloud provider CLI authenticated (`aws` or `gcloud`)
- Container registry access (ECR, GCR, or Docker Hub)
- Kubernetes cluster or Docker Compose target environment

## Instructions

### Step 1: Configure Secret Management

Store Juicebox credentials in a cloud secret manager. Never bake tokens into container images.

#### AWS Secrets Manager
```bash
# Create the secret
aws secretsmanager create-secret \
  --name juicebox/prod-credentials \
  --secret-string '{"username":"your-username","apiToken":"jb_tok_prod_xxxxxxxxxxxx"}'

# Verify it was created
aws secretsmanager describe-secret --secret-id juicebox/prod-credentials
```

```typescript
// lib/secrets.ts
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

interface JuiceboxCredentials {
  username: string;
  apiToken: string;
}

const client = new SecretsManagerClient({ region: process.env.AWS_REGION || 'us-east-1' });

export async function getJuiceboxCredentials(): Promise<JuiceboxCredentials> {
  const command = new GetSecretValueCommand({ SecretId: 'juicebox/prod-credentials' });
  const result = await client.send(command);
  if (!result.SecretString) {
    throw new Error('Juicebox credentials secret is empty');
  }
  return JSON.parse(result.SecretString);
}

export async function buildAuthHeader(): Promise<Record<string, string>> {
  const creds = await getJuiceboxCredentials();
  return {
    'Authorization': `token ${creds.username}:${creds.apiToken}`,
    'Content-Type': 'application/json',
  };
}
```

#### GCP Secret Manager
```bash
# Create secrets
echo -n "your-username" | gcloud secrets create juicebox-username --data-file=-
echo -n "jb_tok_prod_xxxxxxxxxxxx" | gcloud secrets create juicebox-api-token --data-file=-

# Grant the service account access
gcloud secrets add-iam-policy-binding juicebox-api-token \
  --member="serviceAccount:YOUR_SA@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

```typescript
// lib/secrets-gcp.ts
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

const client = new SecretManagerServiceClient();
const project = process.env.GOOGLE_CLOUD_PROJECT!;

async function getSecret(name: string): Promise<string> {
  const [version] = await client.accessSecretVersion({
    name: `projects/${project}/secrets/${name}/versions/latest`,
  });
  return version.payload!.data!.toString();
}

export async function buildAuthHeader(): Promise<Record<string, string>> {
  const [username, apiToken] = await Promise.all([
    getSecret('juicebox-username'),
    getSecret('juicebox-api-token'),
  ]);
  return {
    'Authorization': `token ${username}:${apiToken}`,
    'Content-Type': 'application/json',
  };
}
```

### Step 2: Create Docker Deployment Configuration

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN addgroup -g 1001 appgroup && adduser -u 1001 -G appgroup -s /bin/sh -D appuser
COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/dist/ ./dist/

# Credentials come from secret manager at runtime, not ENV
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

```yaml
# docker-compose.yml
services:
  juicebox-app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - AWS_REGION=us-east-1
      # Credentials fetched from Secrets Manager at runtime
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
      restart_policy:
        condition: on-failure
        max_attempts: 3
```

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: juicebox-app
  labels:
    app: juicebox-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: juicebox-app
  template:
    metadata:
      labels:
        app: juicebox-app
    spec:
      serviceAccountName: juicebox-app-sa
      containers:
        - name: app
          image: your-registry/juicebox-app:latest
          ports:
            - containerPort: 3000
          env:
            - name: NODE_ENV
              value: "production"
            - name: AWS_REGION
              value: "us-east-1"
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
```

### Step 3: Implement Health Check Endpoint

The liveness probe checks the server is running. The readiness probe validates Juicebox API connectivity.

```typescript
// src/routes/health.ts
import { Router, Request, Response } from 'express';
import { buildAuthHeader } from '../lib/secrets';

const router = Router();
const JUICEBOX_API = 'https://api.juicebox.ai/v1';

// Liveness: is the process alive?
router.get('/health', (_req: Request, res: Response) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

// Readiness: can we reach the Juicebox API?
router.get('/health/ready', async (_req: Request, res: Response) => {
  try {
    const headers = await buildAuthHeader();
    const response = await fetch(`${JUICEBOX_API}/me`, { headers });
    if (!response.ok) {
      throw new Error(`Juicebox returned HTTP ${response.status}`);
    }
    const user = await response.json();
    res.json({
      status: 'ready',
      juicebox: 'connected',
      account: user.username,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(503).json({
      status: 'not ready',
      juicebox: 'disconnected',
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
    });
  }
});

export default router;
```

### Step 4: Create Deployment Script with Pre-Flight Validation

```bash
#!/bin/bash
# scripts/deploy.sh — Build, validate, and deploy Juicebox integration
set -euo pipefail

ENVIRONMENT="${1:-staging}"
VERSION=$(git rev-parse --short HEAD)
REGISTRY="${CONTAINER_REGISTRY:-your-registry}"
IMAGE="${REGISTRY}/juicebox-app:${VERSION}"

echo "=== Deploying juicebox-app v${VERSION} to ${ENVIRONMENT} ==="

# ---- Pre-flight: validate Juicebox credentials ----
echo "[1/5] Validating Juicebox API credentials..."
if [ -z "${JUICEBOX_USERNAME:-}" ] || [ -z "${JUICEBOX_API_TOKEN:-}" ]; then
  echo "ERROR: JUICEBOX_USERNAME and JUICEBOX_API_TOKEN must be set"
  exit 1
fi

AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  https://api.juicebox.ai/v1/me)
if [ "$AUTH_STATUS" != "200" ]; then
  echo "ERROR: Juicebox auth failed (HTTP ${AUTH_STATUS})"
  exit 1
fi
echo "  Juicebox credentials valid"

# ---- Build ----
echo "[2/5] Building application..."
npm run build

echo "[3/5] Building and pushing container image..."
docker build -t "${IMAGE}" .
docker push "${IMAGE}"

# ---- Deploy ----
echo "[4/5] Rolling out to ${ENVIRONMENT}..."
kubectl set image "deployment/juicebox-app" \
  "app=${IMAGE}" \
  --namespace "${ENVIRONMENT}"
kubectl rollout status "deployment/juicebox-app" \
  --namespace "${ENVIRONMENT}" \
  --timeout=300s

# ---- Post-deploy verification ----
echo "[5/5] Running post-deployment verification..."
APP_URL=$(kubectl get svc juicebox-app -n "${ENVIRONMENT}" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Wait for readiness
for i in {1..10}; do
  HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "http://${APP_URL}/health/ready" 2>/dev/null || true)
  if [ "$HEALTH" = "200" ]; then
    echo "  Health check passed"
    break
  fi
  echo "  Waiting for readiness (attempt ${i}/10)..."
  sleep 5
done

if [ "$HEALTH" != "200" ]; then
  echo "ERROR: Post-deploy health check failed. Initiating rollback..."
  kubectl rollout undo deployment/juicebox-app --namespace "${ENVIRONMENT}"
  exit 1
fi

echo "=== Deployment complete: juicebox-app v${VERSION} → ${ENVIRONMENT} ==="
```

### Step 5: Post-Deployment Verification

Run targeted checks against the deployed application to confirm search, enrichment, and webhook connectivity.

```typescript
// scripts/verify-deployment.ts
const APP_URL = process.env.APP_URL || 'http://localhost:3000';
const JUICEBOX_API = 'https://api.juicebox.ai/v1';

interface CheckResult {
  name: string;
  passed: boolean;
  detail: string;
}

async function runChecks(): Promise<void> {
  const results: CheckResult[] = [];

  // Check 1: App health
  const healthRes = await fetch(`${APP_URL}/health/ready`);
  const health = await healthRes.json();
  results.push({
    name: 'App Health',
    passed: health.status === 'ready',
    detail: `status=${health.status}, juicebox=${health.juicebox}`,
  });

  // Check 2: Search via the app
  const searchRes = await fetch(`${APP_URL}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: 'engineer', limit: 1 }),
  });
  results.push({
    name: 'Search Endpoint',
    passed: searchRes.ok,
    detail: `HTTP ${searchRes.status}`,
  });

  // Check 3: Enrichment via the app
  const enrichRes = await fetch(`${APP_URL}/api/enrich`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: 'CTO fintech', limit: 1 }),
  });
  results.push({
    name: 'Enrichment Endpoint',
    passed: enrichRes.ok,
    detail: `HTTP ${enrichRes.status}`,
  });

  // Check 4: Webhook endpoint accepts POST
  const webhookRes = await fetch(`${APP_URL}/webhooks/juicebox`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ event: 'test', data: {} }),
  });
  results.push({
    name: 'Webhook Endpoint',
    passed: webhookRes.status !== 404,
    detail: `HTTP ${webhookRes.status}`,
  });

  // Report
  console.log('\n=== Post-Deployment Verification ===');
  let allPassed = true;
  for (const r of results) {
    const icon = r.passed ? 'PASS' : 'FAIL';
    console.log(`  [${icon}] ${r.name}: ${r.detail}`);
    if (!r.passed) allPassed = false;
  }

  if (!allPassed) {
    console.log('\nDeployment verification FAILED. Check logs above.');
    process.exit(1);
  }
  console.log('\nAll post-deployment checks passed.');
}

runChecks();
```

## Output
- `lib/secrets.ts` — Secret manager integration (AWS or GCP) returning Juicebox auth headers
- `Dockerfile` — Multi-stage production build with health check
- `docker-compose.yml` — Local production simulation
- `k8s/deployment.yaml` — Kubernetes deployment with liveness and readiness probes
- `src/routes/health.ts` — Health check endpoints (`/health` and `/health/ready`)
- `scripts/deploy.sh` — End-to-end deployment script with pre-flight validation and rollback
- `scripts/verify-deployment.ts` — Post-deployment verification (search, enrichment, webhooks)

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `Juicebox credentials secret is empty` | Secret exists but has no value | Re-create with `aws secretsmanager put-secret-value` or `gcloud secrets versions add` |
| `AccessDeniedException` on secret fetch | IAM policy missing | Grant `secretsmanager:GetSecretValue` (AWS) or `secretmanager.secretAccessor` (GCP) to the service account |
| Readiness probe returns 503 | App cannot reach Juicebox API | Check network policies, security groups, and DNS resolution from the pod |
| Docker build OOM | Node runs out of memory during build | Add `--max-old-space-size=4096` to the build command or increase Docker memory limit |
| Rollout timeout | New pods failing to start | Check `kubectl describe pod` for image pull errors or crash loops; verify the image tag exists in the registry |
| Post-deploy webhook 404 | Webhook route not registered | Ensure the webhook router is mounted in `app.use('/webhooks/juicebox', ...)` |

## Examples

### Quick Local Deploy Test
```bash
# Build and run locally with Docker Compose
export JUICEBOX_USERNAME="your-username"
export JUICEBOX_API_TOKEN="jb_tok_xxxxxxxxxxxx"

docker compose up --build -d

# Verify health
curl http://localhost:3000/health/ready | jq .

# Test search through the app
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"VP Engineering at Series B startups","limit":5}' | jq .
```

### Deploying to Staging Then Production
```bash
# Deploy to staging first
./scripts/deploy.sh staging

# Run verification against staging
APP_URL=https://staging.yourapp.com npx tsx scripts/verify-deployment.ts

# If staging passes, deploy to production
./scripts/deploy.sh production
APP_URL=https://yourapp.com npx tsx scripts/verify-deployment.ts
```

## Resources
- [Juicebox API Documentation](https://juicebox.ai/docs/api)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Kubernetes Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## Next Steps
After deploying, use `juicebox-prod-checklist` to validate production readiness before routing live traffic.
