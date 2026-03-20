---
name: apollo-deploy-integration
description: |
  Deploy Apollo.io integrations to production.
  Use when deploying Apollo integrations, configuring production environments,
  or setting up deployment pipelines.
  Trigger with phrases like "deploy apollo", "apollo production deploy",
  "apollo deployment pipeline", "apollo to production".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Deploy Integration

## Overview
Deploy Apollo.io integrations to production with platform-specific configurations for Vercel, GCP Cloud Run, AWS Lambda, and Kubernetes. Includes health check endpoints, pre-deployment validation, and rollback procedures.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup
- Target platform CLI installed (vercel, gcloud, aws, or kubectl)

## Instructions

### Step 1: Create a Health Check Endpoint
```typescript
// src/health.ts
import axios from 'axios';
import express from 'express';

const app = express();

app.get('/health', async (req, res) => {
  const checks: Record<string, string> = {};

  // Check Apollo API connectivity
  try {
    const start = Date.now();
    await axios.post(
      'https://api.apollo.io/v1/people/search',
      { q_organization_domains: ['apollo.io'], per_page: 1 },
      { params: { api_key: process.env.APOLLO_API_KEY }, timeout: 5000 },
    );
    checks.apollo = `ok (${Date.now() - start}ms)`;
  } catch (err: any) {
    checks.apollo = `error: ${err.response?.status ?? err.message}`;
  }

  // Check env vars
  checks.apiKey = process.env.APOLLO_API_KEY ? 'set' : 'MISSING';
  checks.nodeEnv = process.env.NODE_ENV ?? 'not set';

  const healthy = checks.apollo.startsWith('ok') && checks.apiKey === 'set';
  res.status(healthy ? 200 : 503).json({ status: healthy ? 'healthy' : 'unhealthy', checks });
});
```

### Step 2: Deploy to Vercel
```json
{
  "name": "apollo-integration",
  "builds": [{ "src": "src/index.ts", "use": "@vercel/node" }],
  "routes": [{ "src": "/(.*)", "dest": "src/index.ts" }],
  "env": {
    "APOLLO_API_KEY": "@apollo-api-key",
    "NODE_ENV": "production"
  }
}
```

```bash
# Store the secret in Vercel
vercel secrets add apollo-api-key "$APOLLO_API_KEY"

# Deploy
vercel --prod
```

### Step 3: Deploy to GCP Cloud Run
```dockerfile
# Dockerfile
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY package*.json ./
EXPOSE 8080
CMD ["node", "dist/index.js"]
```

```bash
# Deploy to Cloud Run with secrets from Secret Manager
gcloud run deploy apollo-integration \
  --source . \
  --region us-central1 \
  --set-secrets "APOLLO_API_KEY=apollo-api-key:latest" \
  --set-env-vars "NODE_ENV=production" \
  --min-instances 1 \
  --max-instances 10 \
  --port 8080
```

### Step 4: Deploy to Kubernetes
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apollo-integration
spec:
  replicas: 2
  selector:
    matchLabels:
      app: apollo-integration
  template:
    metadata:
      labels:
        app: apollo-integration
    spec:
      containers:
        - name: apollo-integration
          image: gcr.io/my-project/apollo-integration:latest
          ports:
            - containerPort: 8080
          envFrom:
            - secretRef:
                name: apollo-credentials
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
```

### Step 5: Pre-Deployment Validation Script
```typescript
// src/scripts/pre-deploy.ts
async function preDeployCheck() {
  const checks: { name: string; pass: boolean; detail: string }[] = [];

  // 1. API key is set
  checks.push({
    name: 'API key configured',
    pass: !!process.env.APOLLO_API_KEY,
    detail: process.env.APOLLO_API_KEY ? 'Set' : 'MISSING',
  });

  // 2. API is reachable
  try {
    await axios.post(
      'https://api.apollo.io/v1/people/search',
      { per_page: 1 },
      { params: { api_key: process.env.APOLLO_API_KEY }, timeout: 10_000 },
    );
    checks.push({ name: 'Apollo API reachable', pass: true, detail: 'OK' });
  } catch (err: any) {
    checks.push({ name: 'Apollo API reachable', pass: false, detail: err.message });
  }

  // 3. Build succeeds
  try {
    const { execSync } = await import('child_process');
    execSync('npm run build', { stdio: 'pipe' });
    checks.push({ name: 'Build succeeds', pass: true, detail: 'OK' });
  } catch {
    checks.push({ name: 'Build succeeds', pass: false, detail: 'Build failed' });
  }

  // 4. Tests pass
  try {
    const { execSync } = await import('child_process');
    execSync('npm test', { stdio: 'pipe' });
    checks.push({ name: 'Tests pass', pass: true, detail: 'OK' });
  } catch {
    checks.push({ name: 'Tests pass', pass: false, detail: 'Tests failed' });
  }

  // Report
  const allPass = checks.every((c) => c.pass);
  for (const check of checks) {
    console.log(`${check.pass ? 'PASS' : 'FAIL'} ${check.name}: ${check.detail}`);
  }
  console.log(`\nDeploy ${allPass ? 'READY' : 'BLOCKED'}`);
  process.exit(allPass ? 0 : 1);
}

preDeployCheck();
```

## Output
- Health check endpoint reporting Apollo API connectivity and config status
- Vercel deployment config with encrypted secret reference
- GCP Cloud Run deploy command with Secret Manager integration
- Kubernetes deployment manifest with liveness/readiness probes
- Pre-deployment validation script (API key, connectivity, build, tests)

## Error Handling
| Issue | Resolution |
|-------|------------|
| Secret not found | Verify secret name matches platform config (Vercel/GCP/K8s) |
| Health check fails | Check Apollo API key and network egress rules |
| Deployment timeout | Increase timeout, check container startup logs |
| Rollback needed | `vercel rollback`, `gcloud run deploy --revision`, or `kubectl rollout undo` |

## Examples

### Blue-Green Deployment with Kubernetes
```bash
# Deploy new version as "green"
kubectl apply -f k8s/deployment-green.yaml

# Verify health
kubectl exec deploy/apollo-integration-green -- curl -s localhost:8080/health

# Switch traffic
kubectl patch service apollo-integration -p '{"spec":{"selector":{"version":"green"}}}'

# If issues, rollback
kubectl patch service apollo-integration -p '{"spec":{"selector":{"version":"blue"}}}'
```

## Resources
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## Next Steps
Proceed to `apollo-webhooks-events` for webhook implementation.
