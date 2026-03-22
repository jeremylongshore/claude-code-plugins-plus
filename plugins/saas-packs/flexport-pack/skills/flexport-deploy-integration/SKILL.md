---
name: flexport-deploy-integration
description: |
  Deploy Flexport logistics integrations to Vercel, Fly.io, and Cloud Run.
  Use when deploying shipment tracking dashboards, webhook receivers,
  or supply chain automation services to production infrastructure.
  Trigger: "deploy flexport", "flexport hosting", "flexport Cloud Run".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(fly:*), Bash(gcloud:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Deploy Integration

## Overview

Deploy Flexport-powered applications to production. Webhook receivers need always-on hosting. Dashboards can use serverless. Background sync workers suit containers.

## Instructions

### Option A: Vercel (Dashboard + Webhook Routes)

```typescript
// app/api/webhooks/flexport/route.ts (Next.js App Router)
import crypto from 'crypto';

export async function POST(req: Request) {
  const body = await req.text();
  const sig = req.headers.get('x-hub-signature') || '';
  const expected = 'sha256=' + crypto.createHmac('sha256', process.env.FLEXPORT_WEBHOOK_SECRET!)
    .update(body).digest('hex');
  if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) {
    return new Response('Invalid signature', { status: 401 });
  }
  const event = JSON.parse(body);
  // Process milestone, booking, invoice events
  return new Response('OK');
}
```

### Option B: Fly.io (Always-On Webhook Receiver)

```toml
# fly.toml
app = "flexport-webhooks"
primary_region = "iad"
[http_service]
  internal_port = 3000
  force_https = true
  min_machines_running = 1
```

```bash
fly secrets set FLEXPORT_API_KEY="key" FLEXPORT_WEBHOOK_SECRET="secret"
fly deploy
```

### Option C: Cloud Run (Shipment Sync Worker)

```bash
gcloud run deploy flexport-sync \
  --source . --region us-central1 \
  --set-secrets "FLEXPORT_API_KEY=flexport-key:latest" \
  --min-instances 1 --timeout 300
```

## Post-Deploy Verification

```bash
curl -X POST https://your-app.fly.dev/webhooks/flexport \
  -H "X-Hub-Signature: sha256=invalid" -d '{"type":"test"}'
# Expected: 401 (signature verification working)
```

## Resources

- [Flexport Webhooks API](https://apidocs.flexport.com/v2/tag/Webhook-Endpoints/)
- [Fly.io Docs](https://fly.io/docs/)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

## Next Steps

For webhook event handling, see `flexport-webhooks-events`.
