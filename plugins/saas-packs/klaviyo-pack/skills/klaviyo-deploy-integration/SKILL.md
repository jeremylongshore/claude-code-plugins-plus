---
name: klaviyo-deploy-integration
description: |
  Deploy Klaviyo integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Klaviyo-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy klaviyo", "klaviyo Vercel",
  "klaviyo production deploy", "klaviyo Cloud Run", "klaviyo Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Deploy Integration

## Overview

Deploy Klaviyo-powered applications to Vercel, Fly.io, and Google Cloud Run with proper secrets management and health checks.

## Prerequisites

- Klaviyo production API key (`pk_*`)
- Platform CLI installed (`vercel`, `fly`, or `gcloud`)
- Application tested with `klaviyo-api` SDK
- `klaviyo-prod-checklist` completed

## Instructions

### Vercel Deployment

```bash
# 1. Add secrets to Vercel project
vercel env add KLAVIYO_PRIVATE_KEY production
# Paste your pk_*** key when prompted

vercel env add KLAVIYO_WEBHOOK_SIGNING_SECRET production
# Paste your whsec_*** secret

# 2. Configure vercel.json
```

```json
{
  "env": {
    "KLAVIYO_PRIVATE_KEY": "@klaviyo_private_key"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  },
  "rewrites": [
    { "source": "/webhooks/klaviyo", "destination": "/api/webhooks/klaviyo" }
  ]
}
```

```bash
# 3. Deploy
vercel --prod

# 4. Verify health
curl -s https://your-app.vercel.app/api/health | jq '.services.klaviyo'
```

#### Vercel Webhook Handler (Edge-compatible)

```typescript
// api/webhooks/klaviyo.ts (Vercel serverless function)
import crypto from 'crypto';

export const config = { api: { bodyParser: false } };

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') return res.status(405).end();

  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk);
  const body = Buffer.concat(chunks);

  // Verify HMAC-SHA256 signature
  const signature = req.headers['klaviyo-webhook-signature'];
  const expected = crypto
    .createHmac('sha256', process.env.KLAVIYO_WEBHOOK_SIGNING_SECRET!)
    .update(body)
    .digest('base64');

  if (!crypto.timingSafeEqual(Buffer.from(signature || ''), Buffer.from(expected))) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const event = JSON.parse(body.toString());
  // Process event...
  console.log('Klaviyo webhook:', event.type);

  res.status(200).json({ received: true });
}
```

### Fly.io Deployment

```toml
# fly.toml
app = "my-klaviyo-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 1

[[services.http_checks]]
  interval = 30000
  timeout = 5000
  path = "/health"
  method = "GET"
```

```bash
# 1. Set secrets
fly secrets set KLAVIYO_PRIVATE_KEY=pk_***
fly secrets set KLAVIYO_WEBHOOK_SIGNING_SECRET=whsec_***

# 2. Deploy
fly deploy

# 3. Verify
fly status
curl -s https://my-klaviyo-app.fly.dev/health | jq
```

### Google Cloud Run Deployment

```dockerfile
# Dockerfile
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
COPY --from=builder /app/package.json .
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```bash
# 1. Store secret in GCP Secret Manager
echo -n "pk_***" | gcloud secrets create klaviyo-private-key --data-file=-
echo -n "whsec_***" | gcloud secrets create klaviyo-webhook-secret --data-file=-

# 2. Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding klaviyo-private-key \
  --member="serviceAccount:YOUR_SA@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3. Deploy to Cloud Run
gcloud run deploy klaviyo-service \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets=KLAVIYO_PRIVATE_KEY=klaviyo-private-key:latest,KLAVIYO_WEBHOOK_SIGNING_SECRET=klaviyo-webhook-secret:latest \
  --min-instances=1 \
  --max-instances=10

# 4. Verify
gcloud run services describe klaviyo-service --region=us-central1 --format="value(status.url)"
```

### Universal Health Check

```typescript
// src/health.ts -- works on all platforms
import { ApiKeySession, AccountsApi } from 'klaviyo-api';

export async function healthCheck(): Promise<{
  status: string;
  services: { klaviyo: { connected: boolean; latencyMs: number } };
}> {
  const start = Date.now();
  try {
    const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
    const api = new AccountsApi(session);
    await api.getAccounts();
    return {
      status: 'healthy',
      services: { klaviyo: { connected: true, latencyMs: Date.now() - start } },
    };
  } catch {
    return {
      status: 'degraded',
      services: { klaviyo: { connected: false, latencyMs: Date.now() - start } },
    };
  }
}
```

## Output

- Application deployed with Klaviyo secrets configured
- Health check endpoint verifying Klaviyo connectivity
- Webhook endpoint with HMAC signature verification
- Platform-specific best practices applied

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found at runtime | Missing env config | Verify secret binding in platform |
| Cold start timeout | Klaviyo API slow on first call | Set `min_instances=1` |
| Webhook 401 | Wrong signing secret | Verify secret matches Klaviyo dashboard |
| Health check fails | Wrong API key per env | Separate keys for staging/prod |

## Resources

- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Fly.io Secrets](https://fly.io/docs/apps/secrets/)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Klaviyo API Reference](https://developers.klaviyo.com/en/reference/api_overview)

## Next Steps

For webhook handling, see `klaviyo-webhooks-events`.
