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
tags: [saas, apollo, deployment]

---
# Apollo Deploy Integration

## Overview
Deploy Apollo.io integrations to production with configurations for Vercel, GCP Cloud Run, and Kubernetes. All configurations use `x-api-key` header auth, health check endpoints verifying Apollo connectivity, and secret management best practices.

## Prerequisites
- Valid Apollo master API key
- Node.js 18+
- Target platform CLI installed (vercel, gcloud, or kubectl)

## Instructions

### Step 1: Health Check Endpoint
Every deployment needs a health endpoint that verifies Apollo API connectivity.

```typescript
// src/health.ts
import axios from 'axios';
import { Router } from 'express';

export const healthRouter = Router();

healthRouter.get('/health', async (req, res) => {
  const checks: Record<string, string> = {
    apiKey: process.env.APOLLO_API_KEY ? 'set' : 'MISSING',
    nodeEnv: process.env.NODE_ENV ?? 'not set',
  };

  try {
    const start = Date.now();
    const resp = await axios.get('https://api.apollo.io/api/v1/auth/health', {
      headers: { 'x-api-key': process.env.APOLLO_API_KEY! },
      timeout: 5000,
    });
    checks.apollo = resp.data.is_logged_in ? `ok (${Date.now() - start}ms)` : 'invalid key';
  } catch (err: any) {
    checks.apollo = `error: ${err.response?.status ?? err.message}`;
  }

  const healthy = checks.apollo.startsWith('ok') && checks.apiKey === 'set';
  res.status(healthy ? 200 : 503).json({ status: healthy ? 'healthy' : 'unhealthy', checks });
});
```

### Step 2: Deploy to GCP Cloud Run
```dockerfile
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
# Store API key in GCP Secret Manager
echo -n "$APOLLO_API_KEY" | gcloud secrets create apollo-api-key --data-file=-

# Deploy with secret injection
gcloud run deploy apollo-integration \
  --source . \
  --region us-central1 \
  --set-secrets "APOLLO_API_KEY=apollo-api-key:latest" \
  --set-env-vars "NODE_ENV=production" \
  --min-instances 1 --max-instances 10 \
  --port 8080
```

### Step 3: Deploy to Vercel
```json
{
  "name": "apollo-integration",
  "builds": [{ "src": "src/index.ts", "use": "@vercel/node" }],
  "routes": [{ "src": "/(.*)", "dest": "src/index.ts" }],
  "env": { "APOLLO_API_KEY": "@apollo-api-key", "NODE_ENV": "production" }
}
```

```bash
vercel secrets add apollo-api-key "$APOLLO_API_KEY"
vercel --prod
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
    matchLabels: { app: apollo-integration }
  template:
    metadata:
      labels: { app: apollo-integration }
    spec:
      containers:
        - name: apollo
          image: gcr.io/my-project/apollo-integration:latest
          ports: [{ containerPort: 8080 }]
          envFrom:
            - secretRef: { name: apollo-credentials }
          env:
            - { name: NODE_ENV, value: "production" }
          livenessProbe:
            httpGet: { path: /health, port: 8080 }
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet: { path: /health, port: 8080 }
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests: { memory: "128Mi", cpu: "100m" }
            limits: { memory: "256Mi", cpu: "500m" }
---
apiVersion: v1
kind: Secret
metadata:
  name: apollo-credentials
type: Opaque
stringData:
  APOLLO_API_KEY: "your-master-key-here"
```

### Step 5: Pre-Deploy Validation
```typescript
// src/scripts/pre-deploy.ts
async function preDeployCheck() {
  const checks: Array<{ name: string; pass: boolean }> = [];

  // API key set
  checks.push({ name: 'APOLLO_API_KEY set', pass: !!process.env.APOLLO_API_KEY });

  // Auth works
  try {
    const resp = await axios.get('https://api.apollo.io/api/v1/auth/health', {
      headers: { 'x-api-key': process.env.APOLLO_API_KEY! },
    });
    checks.push({ name: 'Apollo auth valid', pass: resp.data.is_logged_in });
  } catch { checks.push({ name: 'Apollo auth valid', pass: false }); }

  // Build succeeds
  try {
    const { execSync } = await import('child_process');
    execSync('npm run build', { stdio: 'pipe' });
    checks.push({ name: 'Build succeeds', pass: true });
  } catch { checks.push({ name: 'Build succeeds', pass: false }); }

  const allPass = checks.every((c) => c.pass);
  checks.forEach((c) => console.log(`${c.pass ? 'PASS' : 'FAIL'} ${c.name}`));
  console.log(`\nDeploy: ${allPass ? 'READY' : 'BLOCKED'}`);
  process.exit(allPass ? 0 : 1);
}
preDeployCheck();
```

## Output
- Express health check endpoint verifying Apollo connectivity
- GCP Cloud Run deployment with Secret Manager integration
- Vercel deployment with encrypted secrets
- Kubernetes manifests with liveness/readiness probes
- Pre-deploy validation script

## Error Handling
| Issue | Resolution |
|-------|------------|
| Health check 503 | Check APOLLO_API_KEY secret is mounted correctly |
| Container crash loop | Review startup logs, verify secret names match |
| Rollback needed | `gcloud run deploy --revision`, `vercel rollback`, or `kubectl rollout undo` |
| Secret rotation | Update secret, redeploy — health check confirms new key works |

## Resources
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## Next Steps
Proceed to `apollo-webhooks-events` for webhook implementation.
