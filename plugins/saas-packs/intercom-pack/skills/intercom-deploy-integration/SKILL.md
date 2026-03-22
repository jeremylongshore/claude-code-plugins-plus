---
name: intercom-deploy-integration
description: |
  Deploy Intercom integrations to Vercel, Fly.io, and Cloud Run with proper secrets.
  Use when deploying Intercom-powered applications to production,
  configuring platform-specific secrets, or setting up webhook endpoints.
  Trigger with phrases like "deploy intercom", "intercom Vercel",
  "intercom production deploy", "intercom Cloud Run", "intercom Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Deploy Integration

## Overview

Deploy Intercom-powered applications to Vercel, Fly.io, or Google Cloud Run with proper secret management, webhook endpoint configuration, and health checks.

## Prerequisites

- Intercom production access token
- Platform CLI installed (`vercel`, `flyctl`, or `gcloud`)
- Application with Intercom integration ready for deployment

## Instructions

### Step 1: Vercel Deployment

```bash
# Add Intercom secrets to Vercel
vercel env add INTERCOM_ACCESS_TOKEN production
vercel env add INTERCOM_WEBHOOK_SECRET production

# Deploy to production
vercel --prod
```

**API Route for Webhooks (Vercel Serverless):**

```typescript
// api/webhooks/intercom.ts (Vercel serverless function)
import crypto from "crypto";

export const config = { api: { bodyParser: false } };

export default async function handler(req: any, res: any) {
  if (req.method !== "POST") return res.status(405).end();

  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk);
  const body = Buffer.concat(chunks);

  // Verify signature
  const signature = req.headers["x-hub-signature"] as string;
  const expected = "sha1=" + crypto
    .createHmac("sha1", process.env.INTERCOM_WEBHOOK_SECRET!)
    .update(body)
    .digest("hex");

  if (!crypto.timingSafeEqual(Buffer.from(signature || ""), Buffer.from(expected))) {
    return res.status(401).json({ error: "Invalid signature" });
  }

  const event = JSON.parse(body.toString());
  console.log(`Intercom webhook: ${event.topic}`);

  // Process within 5s (Intercom timeout)
  // For long processing, queue the event and return immediately
  res.status(200).json({ received: true });
}
```

**vercel.json:**

```json
{
  "functions": {
    "api/webhooks/intercom.ts": {
      "maxDuration": 10
    }
  }
}
```

### Step 2: Fly.io Deployment

```toml
# fly.toml
app = "my-intercom-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = false   # Keep running for webhooks
  auto_start_machines = true

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  path = "/health"
  timeout = "5s"
```

```bash
# Set secrets
fly secrets set INTERCOM_ACCESS_TOKEN="dG9rOi4uLg=="
fly secrets set INTERCOM_WEBHOOK_SECRET="your-secret"

# Deploy
fly deploy

# Verify health
fly status
curl https://my-intercom-app.fly.dev/health
```

### Step 3: Google Cloud Run

```bash
#!/bin/bash
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE="intercom-service"
REGION="us-central1"

# Store secrets in Secret Manager
echo -n "$INTERCOM_ACCESS_TOKEN" | \
  gcloud secrets create intercom-token --data-file=- --replication-policy=automatic
echo -n "$INTERCOM_WEBHOOK_SECRET" | \
  gcloud secrets create intercom-webhook-secret --data-file=- --replication-policy=automatic

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE

gcloud run deploy $SERVICE \
  --image gcr.io/$PROJECT_ID/$SERVICE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="INTERCOM_ACCESS_TOKEN=intercom-token:latest,INTERCOM_WEBHOOK_SECRET=intercom-webhook-secret:latest" \
  --min-instances=1 \
  --timeout=60
```

### Step 4: Health Check Endpoint

```typescript
// src/routes/health.ts
import { IntercomClient, IntercomError } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

export async function healthCheck(): Promise<{
  status: string;
  services: { intercom: { connected: boolean; latencyMs: number; error?: string } };
}> {
  const start = Date.now();
  try {
    await client.admins.list();
    return {
      status: "healthy",
      services: {
        intercom: { connected: true, latencyMs: Date.now() - start },
      },
    };
  } catch (err) {
    const latencyMs = Date.now() - start;
    const error = err instanceof IntercomError
      ? `${err.statusCode}: ${err.message}`
      : (err as Error).message;
    return {
      status: "degraded",
      services: {
        intercom: { connected: false, latencyMs, error },
      },
    };
  }
}
```

### Step 5: Register Webhook URL

After deploying, configure the webhook URL in Intercom:

1. Go to Developer Hub > Webhooks
2. Set endpoint URL: `https://your-domain.com/api/webhooks/intercom`
3. Select topics: `conversation.user.created`, `contact.created`, etc.
4. Copy the webhook signing secret to your platform secrets
5. Send a test notification to verify

## Webhook Topics Reference

| Topic | Fires When |
|-------|-----------|
| `conversation.user.created` | New conversation from contact |
| `conversation.user.replied` | Contact replies |
| `conversation.admin.replied` | Admin replies |
| `conversation.admin.closed` | Conversation closed |
| `contact.created` | New contact created |
| `contact.signed_up` | Lead converts to user |
| `contact.tag.created` | Tag applied to contact |
| `user.created` | New user (legacy topic) |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook 401 | Signature mismatch | Verify secret matches Developer Hub |
| Cold start timeout | Serverless spin-up | Set min instances > 0 |
| Secret not found | Missing config | Verify secrets with platform CLI |
| Health check failing | Token invalid in prod | Verify production token |
| Webhook delivery fails | 5s timeout exceeded | Queue events, process async |

## Resources

- [Webhook Setup](https://developers.intercom.com/docs/webhooks/setting-up-webhooks)
- [Webhook Topics](https://developers.intercom.com/docs/references/webhooks/webhook-models)
- [Vercel Docs](https://vercel.com/docs)
- [Fly.io Docs](https://fly.io/docs)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

## Next Steps

For webhook handling patterns, see `intercom-webhooks-events`.
