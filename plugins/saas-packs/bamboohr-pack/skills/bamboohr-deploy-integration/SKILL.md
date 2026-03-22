---
name: bamboohr-deploy-integration
description: |
  Deploy BambooHR integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying BambooHR-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy bamboohr", "bamboohr Vercel",
  "bamboohr production deploy", "bamboohr Cloud Run", "bamboohr Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, deployment]
compatible-with: claude-code
---

# BambooHR Deploy Integration

## Overview

Deploy BambooHR-powered applications to cloud platforms with proper secrets management, health checks, and webhook endpoint configuration. Covers Vercel (serverless), Fly.io (containers), and Google Cloud Run.

## Prerequisites

- BambooHR integration tested locally and in staging
- Production API key and company domain ready
- Platform CLI installed (`vercel`, `fly`, or `gcloud`)

## Instructions

### Vercel Deployment (Serverless)

```bash
# Set BambooHR secrets in Vercel
vercel env add BAMBOOHR_API_KEY production
vercel env add BAMBOOHR_COMPANY_DOMAIN production
vercel env add BAMBOOHR_WEBHOOK_SECRET production
```

**vercel.json:**

```json
{
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  },
  "crons": [{
    "path": "/api/bamboohr/sync",
    "schedule": "0 */6 * * *"
  }]
}
```

**Webhook endpoint (Vercel serverless):**

```typescript
// api/webhooks/bamboohr.ts
import { verifyBambooHRWebhook } from '../../src/bamboohr/security';

export const config = { api: { bodyParser: false } };

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') return res.status(405).end();

  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk);
  const rawBody = Buffer.concat(chunks);

  const sig = req.headers['x-bamboohr-signature'];
  const ts = req.headers['x-bamboohr-timestamp'];

  if (!verifyBambooHRWebhook(rawBody, sig, ts, process.env.BAMBOOHR_WEBHOOK_SECRET!)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const event = JSON.parse(rawBody.toString());
  // Process webhook asynchronously
  await processWebhookEvent(event);

  return res.status(200).json({ received: true });
}
```

**Deploy:**

```bash
vercel --prod
# Webhook URL: https://your-app.vercel.app/api/webhooks/bamboohr
```

### Fly.io Deployment (Containers)

**fly.toml:**

```toml
app = "my-bamboohr-sync"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true
  min_machines_running = 1

[[services.http_checks]]
  interval = "30s"
  timeout = "5s"
  path = "/api/health"
  method = "GET"
```

```bash
# Set secrets
fly secrets set BAMBOOHR_API_KEY="your-prod-key"
fly secrets set BAMBOOHR_COMPANY_DOMAIN="yourcompany"
fly secrets set BAMBOOHR_WEBHOOK_SECRET="your-secret"

# Deploy
fly deploy

# Verify
fly status
curl -s https://my-bamboohr-sync.fly.dev/api/health | jq .
```

### Google Cloud Run Deployment

**Dockerfile:**

```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

ENV NODE_ENV=production
EXPOSE 8080
CMD ["node", "dist/index.js"]
```

```bash
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE="bamboohr-integration"
REGION="us-central1"

# Store secrets in GCP Secret Manager
echo -n "your-api-key" | gcloud secrets create bamboohr-api-key --data-file=-
echo -n "yourcompany" | gcloud secrets create bamboohr-company-domain --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE

gcloud run deploy $SERVICE \
  --image gcr.io/$PROJECT_ID/$SERVICE \
  --region $REGION \
  --platform managed \
  --set-secrets="BAMBOOHR_API_KEY=bamboohr-api-key:latest,BAMBOOHR_COMPANY_DOMAIN=bamboohr-company-domain:latest" \
  --min-instances=1 \
  --max-instances=10 \
  --timeout=30s \
  --allow-unauthenticated
```

### Health Check Endpoint (All Platforms)

```typescript
// src/api/health.ts
import { BambooHRClient } from '../bamboohr/client';

export async function handleHealthCheck(client: BambooHRClient) {
  const start = Date.now();

  try {
    // Light-weight check: fetch employee 0 (current user)
    await client.getEmployee(0, ['firstName']);
    return {
      status: 'healthy',
      bamboohr: { connected: true, latencyMs: Date.now() - start },
      timestamp: new Date().toISOString(),
    };
  } catch (err) {
    return {
      status: 'degraded',
      bamboohr: {
        connected: false,
        latencyMs: Date.now() - start,
        error: (err as Error).message,
      },
      timestamp: new Date().toISOString(),
    };
  }
}
```

### Webhook Registration via API

```typescript
// Register a webhook programmatically via BambooHR API
// POST /webhooks/
const webhook = await client.request('POST', '/webhooks/', {
  name: 'Employee Sync',
  monitorFields: ['firstName', 'lastName', 'department', 'jobTitle', 'status'],
  postFields: {
    firstName: 'firstName',
    lastName: 'lastName',
    department: 'department',
    jobTitle: 'jobTitle',
    status: 'status',
  },
  url: 'https://your-app.example.com/api/webhooks/bamboohr',
  format: 'json',
  frequency: { every: 0 }, // Immediate
  limit: { enabled: false },
});

console.log(`Webhook registered: ${webhook.id}`);
```

## Output

- Application deployed to production cloud platform
- BambooHR secrets securely configured via platform secrets
- Health check endpoint responding
- Webhook endpoint configured and registered
- Auto-scaling and health monitoring active

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found at runtime | Missing env var configuration | Re-add via platform CLI |
| Webhook 401 from BambooHR | Signature verification failing | Check webhook secret matches |
| Cold start timeout | Serverless function too slow | Pre-initialize client outside handler |
| Health check failing after deploy | Wrong API key for environment | Verify secrets are production values |

## Resources

- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [Fly.io Documentation](https://fly.io/docs)
- [Google Cloud Run](https://cloud.google.com/run/docs)
- [BambooHR Webhooks](https://documentation.bamboohr.com/docs/webhooks)

## Next Steps

For webhook handling, see `bamboohr-webhooks-events`.
