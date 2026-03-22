---
name: salesloft-deploy-integration
description: |
  Deploy SalesLoft integrations to Vercel, Fly.io, and Cloud Run.
  Use when deploying SalesLoft-powered apps to production,
  configuring platform secrets, or setting up webhook endpoints.
  Trigger: "deploy salesloft", "salesloft Vercel", "salesloft Cloud Run".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Deploy Integration

## Overview

Deploy SalesLoft-powered applications to cloud platforms with proper secrets management, webhook endpoint configuration, and health checks. SalesLoft requires HTTPS webhook endpoints and OAuth tokens stored securely.

## Instructions

### Vercel Deployment

```bash
# Set secrets
vercel env add SALESLOFT_CLIENT_ID production
vercel env add SALESLOFT_CLIENT_SECRET production
vercel env add SALESLOFT_WEBHOOK_SECRET production

# Deploy
vercel --prod
```

```typescript
// api/webhooks/salesloft.ts (Vercel serverless function)
import { verifyWebhookSignature } from '../../lib/salesloft';

export const config = { api: { bodyParser: false } }; // Raw body for HMAC

export default async function handler(req: Request) {
  const body = await req.text();
  const sig = req.headers.get('x-salesloft-signature')!;
  const ts = req.headers.get('x-salesloft-timestamp')!;

  if (!verifyWebhookSignature(Buffer.from(body), sig, ts, process.env.SALESLOFT_WEBHOOK_SECRET!)) {
    return new Response('Invalid signature', { status: 401 });
  }

  const event = JSON.parse(body);
  // Process event...
  return new Response(JSON.stringify({ received: true }), { status: 200 });
}
```

### Fly.io Deployment

```toml
# fly.toml
app = "salesloft-sync"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[[services.http_checks]]
  interval = "30s"
  timeout = "5s"
  path = "/health"
```

```bash
fly secrets set SALESLOFT_CLIENT_ID=xxx SALESLOFT_CLIENT_SECRET=xxx
fly secrets set SALESLOFT_WEBHOOK_SECRET=xxx
fly deploy
```

### Cloud Run Deployment

```bash
# Store secrets in Secret Manager
echo -n "client-id" | gcloud secrets create salesloft-client-id --data-file=-
echo -n "client-secret" | gcloud secrets create salesloft-client-secret --data-file=-

# Deploy with secret mounts
gcloud run deploy salesloft-sync \
  --image gcr.io/$PROJECT_ID/salesloft-sync \
  --region us-central1 \
  --set-secrets=SALESLOFT_CLIENT_ID=salesloft-client-id:latest \
  --set-secrets=SALESLOFT_CLIENT_SECRET=salesloft-client-secret:latest \
  --allow-unauthenticated
```

### Health Check (All Platforms)

```typescript
app.get('/health', async (req, res) => {
  const start = Date.now();
  try {
    const { data } = await api.get('/me.json');
    res.json({
      status: 'healthy',
      salesloft: { user: data.data.email, latencyMs: Date.now() - start },
    });
  } catch (err: any) {
    res.status(503).json({
      status: 'degraded',
      salesloft: { error: err.message, latencyMs: Date.now() - start },
    });
  }
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook 401 | Wrong signing secret | Verify secret matches SalesLoft config |
| Cold start timeout | Webhook response > 30s | Process async, respond 200 immediately |
| Secret not found | Missing env var | Check platform secret configuration |
| Health check fails | Token expired | Ensure token refresh is automated |

## Resources

- [SalesLoft API Basics](https://developers.salesloft.com/docs/platform/api-basics/)
- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [Fly.io Docs](https://fly.io/docs)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

## Next Steps

For webhook handling, see `salesloft-webhooks-events`.
