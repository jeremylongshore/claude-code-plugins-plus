---
name: miro-deploy-integration
description: |
  Deploy Miro REST API v2 integrations to Vercel, Fly.io, and Cloud Run
  with proper OAuth token management and webhook configuration.
  Trigger with phrases like "deploy miro", "miro Vercel",
  "miro production deploy", "miro Cloud Run", "miro Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, deployment, cloud]
compatible-with: claude-code
---

# Miro Deploy Integration

## Overview

Deploy Miro REST API v2 integrations to popular platforms with proper OAuth 2.0 token management, webhook endpoint setup, and health monitoring.

## Prerequisites

- Miro app configured with production OAuth credentials
- Access token with required scopes
- Platform CLI installed (vercel, fly, or gcloud)

## Vercel Deployment

### Environment Variables

```bash
# Add Miro secrets to Vercel
vercel env add MIRO_CLIENT_ID production
vercel env add MIRO_CLIENT_SECRET production
vercel env add MIRO_ACCESS_TOKEN production
vercel env add MIRO_WEBHOOK_SECRET production
```

### API Route: Webhook Handler

```typescript
// api/webhooks/miro.ts (Vercel serverless function)
import crypto from 'crypto';

export const config = { api: { bodyParser: false } };

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk);
  const rawBody = Buffer.concat(chunks);

  // Verify Miro webhook signature
  const signature = req.headers['x-miro-signature'] as string;
  const expected = crypto.createHmac('sha256', process.env.MIRO_WEBHOOK_SECRET!)
    .update(rawBody).digest('hex');

  if (!signature || !crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const event = JSON.parse(rawBody.toString());

  // Handle board subscription events
  switch (event.event) {
    case 'board_subscription_changed':
      console.log(`Board ${event.boardId}: item ${event.item?.type} ${event.type}`);
      break;
  }

  res.status(200).json({ received: true });
}
```

### API Route: OAuth Callback

```typescript
// api/auth/miro/callback.ts
export default async function handler(req, res) {
  const { code } = req.query;

  const tokenResponse = await fetch('https://api.miro.com/v1/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: process.env.MIRO_CLIENT_ID!,
      client_secret: process.env.MIRO_CLIENT_SECRET!,
      code: code as string,
      redirect_uri: `${process.env.VERCEL_URL}/api/auth/miro/callback`,
    }),
  });

  const tokens = await tokenResponse.json();
  // Store tokens securely (database, not env vars)
  // tokens.access_token, tokens.refresh_token, tokens.expires_in (3599s)

  res.redirect('/dashboard?connected=miro');
}
```

### vercel.json

```json
{
  "functions": {
    "api/webhooks/miro.ts": { "maxDuration": 10 },
    "api/auth/miro/callback.ts": { "maxDuration": 10 }
  },
  "headers": [
    {
      "source": "/api/health",
      "headers": [{ "key": "Cache-Control", "value": "no-store" }]
    }
  ]
}
```

## Fly.io Deployment

### fly.toml

```toml
app = "my-miro-integration"
primary_region = "iad"

[env]
  NODE_ENV = "production"
  MIRO_API_BASE = "https://api.miro.com/v2"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true
  min_machines_running = 1        # Keep 1 running for webhook delivery

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"
```

### Deploy

```bash
# Set secrets
fly secrets set MIRO_CLIENT_ID=your_client_id
fly secrets set MIRO_CLIENT_SECRET=your_client_secret
fly secrets set MIRO_ACCESS_TOKEN=your_token
fly secrets set MIRO_WEBHOOK_SECRET=your_webhook_secret

# Deploy
fly deploy

# Verify health
fly ssh console -C "curl -s http://localhost:3000/health | jq '.miro'"
```

## Google Cloud Run

### Deploy Script

```bash
#!/bin/bash
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE_NAME="miro-integration"
REGION="us-central1"

# Store secrets in Secret Manager
echo -n "$MIRO_CLIENT_SECRET" | gcloud secrets create miro-client-secret --data-file=-
echo -n "$MIRO_ACCESS_TOKEN" | gcloud secrets create miro-access-token --data-file=-
echo -n "$MIRO_WEBHOOK_SECRET" | gcloud secrets create miro-webhook-secret --data-file=-

# Build and deploy
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 1 \
  --set-env-vars "MIRO_CLIENT_ID=$MIRO_CLIENT_ID,MIRO_API_BASE=https://api.miro.com/v2" \
  --set-secrets "MIRO_CLIENT_SECRET=miro-client-secret:latest,MIRO_ACCESS_TOKEN=miro-access-token:latest,MIRO_WEBHOOK_SECRET=miro-webhook-secret:latest"
```

## Health Check Endpoint

```typescript
// src/health.ts — works on any platform
export async function healthCheck(): Promise<HealthResponse> {
  const checks: Record<string, unknown> = {};

  // Miro API connectivity
  const start = Date.now();
  try {
    const response = await fetch('https://api.miro.com/v2/boards?limit=1', {
      headers: { 'Authorization': `Bearer ${process.env.MIRO_ACCESS_TOKEN}` },
      signal: AbortSignal.timeout(5000),
    });

    checks.miro = {
      status: response.ok ? 'healthy' : 'degraded',
      latencyMs: Date.now() - start,
      rateLimitRemaining: response.headers.get('X-RateLimit-Remaining'),
      httpStatus: response.status,
    };
  } catch (err) {
    checks.miro = { status: 'unhealthy', error: err.message };
  }

  return {
    status: Object.values(checks).every((c: any) => c.status === 'healthy') ? 'healthy' : 'degraded',
    services: checks,
    timestamp: new Date().toISOString(),
  };
}
```

## Webhook URL Registration via API

After deploying, register your webhook endpoint programmatically:

```typescript
// Register board subscription webhook
// POST https://api.miro.com/v2-experimental/webhooks/board_subscriptions
const subscription = await fetch(
  'https://api.miro.com/v2-experimental/webhooks/board_subscriptions',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.MIRO_ACCESS_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      boardId: 'your-board-id',
      callbackUrl: 'https://your-app.com/api/webhooks/miro',
      status: 'enabled',
    }),
  }
);
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook delivery fails | URL not HTTPS | Ensure force_https is enabled |
| Token expires in production | No refresh logic | Implement scheduled token refresh |
| Cold start misses webhook | Min instances = 0 | Set min_machines_running = 1 |
| Secret rotation breaks deploy | Old secret cached | Restart service after secret update |

## Resources

- [Miro OAuth 2.0](https://developers.miro.com/docs/getting-started-with-oauth)
- [Miro Webhooks Setup](https://developers.miro.com/docs/getting-started-with-webhooks)
- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)

## Next Steps

For webhook handling patterns, see `miro-webhooks-events`.
