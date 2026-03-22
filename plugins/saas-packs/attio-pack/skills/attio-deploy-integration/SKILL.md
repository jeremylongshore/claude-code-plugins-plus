---
name: attio-deploy-integration
description: |
  Deploy Attio integrations to Vercel, Fly.io, Railway, and Cloud Run
  with proper secrets, health checks, and webhook endpoint configuration.
  Trigger: "deploy attio", "attio Vercel", "attio production deploy",
  "attio Cloud Run", "attio Fly.io", "attio Railway".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*), Bash(railway:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Deploy Integration

## Overview

Deploy Attio-powered applications to production platforms. Covers secrets injection, health check endpoints, webhook URL configuration, and platform-specific configurations for the Attio REST API (`https://api.attio.com/v2`).

## Prerequisites

- Application code tested locally and in CI
- Production Attio token with minimal scopes
- Platform CLI installed

## Instructions

### Step 1: Vercel Deployment

```bash
# Add secrets
vercel env add ATTIO_API_KEY production
vercel env add ATTIO_WEBHOOK_SECRET production

# Deploy
vercel --prod
```

```json
// vercel.json
{
  "env": {
    "ATTIO_API_KEY": "@attio_api_key",
    "ATTIO_WEBHOOK_SECRET": "@attio_webhook_secret"
  },
  "functions": {
    "api/webhooks/attio.ts": {
      "maxDuration": 30
    }
  }
}
```

**Vercel webhook endpoint:**
```typescript
// api/webhooks/attio.ts (Vercel serverless function)
import type { VercelRequest, VercelResponse } from "@vercel/node";
import crypto from "crypto";

export const config = { api: { bodyParser: false } };

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") return res.status(405).end();

  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk as Buffer);
  const rawBody = Buffer.concat(chunks);

  // Verify webhook signature before processing
  const signature = req.headers["x-attio-signature"] as string;
  const timestamp = req.headers["x-attio-timestamp"] as string;
  if (!verifySignature(rawBody, signature, timestamp)) {
    return res.status(401).json({ error: "Invalid signature" });
  }

  const event = JSON.parse(rawBody.toString());
  // Process async -- return 200 immediately
  res.status(200).json({ received: true });

  // Handle event in background
  await processAttioEvent(event);
}
```

### Step 2: Fly.io Deployment

```toml
# fly.toml
app = "my-attio-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true

[[http_service.checks]]
  interval = "30s"
  timeout = "5s"
  grace_period = "10s"
  method = "GET"
  path = "/api/health"
```

```bash
# Set secrets
fly secrets set ATTIO_API_KEY=sk_prod_xyz
fly secrets set ATTIO_WEBHOOK_SECRET=whsec_prod_abc

# Deploy
fly deploy

# Verify
fly status
curl -s https://my-attio-app.fly.dev/api/health | jq .
```

### Step 3: Google Cloud Run

```bash
# Store secret in Secret Manager
echo -n "sk_prod_xyz" | gcloud secrets create attio-api-key --data-file=-
echo -n "whsec_prod_abc" | gcloud secrets create attio-webhook-secret --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/attio-service

gcloud run deploy attio-service \
  --image gcr.io/$PROJECT_ID/attio-service \
  --region us-central1 \
  --platform managed \
  --set-secrets="ATTIO_API_KEY=attio-api-key:latest,ATTIO_WEBHOOK_SECRET=attio-webhook-secret:latest" \
  --min-instances=1 \
  --max-instances=10 \
  --allow-unauthenticated
```

### Step 4: Health Check Endpoint

Every deployment should include an Attio health check:

```typescript
// api/health.ts
export async function GET(): Promise<Response> {
  const checks: Record<string, { status: string; latencyMs?: number }> = {};

  // Attio connectivity
  const start = Date.now();
  try {
    const res = await fetch("https://api.attio.com/v2/objects", {
      headers: { Authorization: `Bearer ${process.env.ATTIO_API_KEY}` },
      signal: AbortSignal.timeout(5000),
    });
    checks.attio = {
      status: res.ok ? "healthy" : `error_${res.status}`,
      latencyMs: Date.now() - start,
    };
  } catch {
    checks.attio = { status: "unreachable", latencyMs: Date.now() - start };
  }

  const overall = Object.values(checks).every((c) => c.status === "healthy")
    ? "healthy"
    : "degraded";

  return Response.json({ status: overall, checks, timestamp: new Date().toISOString() });
}
```

### Step 5: Register Webhook URL in Attio

After deploying, register your webhook endpoint via the API:

```typescript
// scripts/register-webhook.ts
const webhook = await fetch("https://api.attio.com/v2/webhooks", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.ATTIO_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    target_url: "https://my-attio-app.fly.dev/api/webhooks/attio",
    subscriptions: [
      { event_type: "record.created" },
      { event_type: "record.updated" },
      { event_type: "record.deleted" },
      {
        event_type: "list-entry.created",
        filter: { list: { $eq: "sales_pipeline" } },
      },
    ],
  }),
});

const result = await webhook.json();
console.log("Webhook registered:", result.data?.id?.webhook_id);
```

### Step 6: Environment Configuration Pattern

```typescript
// src/config.ts
interface AppConfig {
  attio: {
    apiKey: string;
    webhookSecret: string;
    baseUrl: string;
  };
  port: number;
  environment: string;
}

export function loadConfig(): AppConfig {
  const env = process.env.NODE_ENV || "development";
  return {
    attio: {
      apiKey: requireEnv("ATTIO_API_KEY"),
      webhookSecret: requireEnv("ATTIO_WEBHOOK_SECRET"),
      baseUrl: "https://api.attio.com/v2",
    },
    port: parseInt(process.env.PORT || "3000", 10),
    environment: env,
  };
}

function requireEnv(key: string): string {
  const val = process.env[key];
  if (!val) throw new Error(`Missing required env: ${key}`);
  return val;
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook never fires | Wrong URL or not registered | Verify with `GET /v2/webhooks` |
| 401 on health check | Token not injected | Check platform secrets config |
| Cold start timeout | Attio API slow on first call | Set `min-instances=1` |
| Webhook signature fails | Secret mismatch | Verify secret matches dashboard value |
| Deploy succeeds, API fails | Wrong env variable name | Check exact key name in platform UI |

## Resources

- [Attio Webhooks Guide](https://docs.attio.com/rest-api/guides/webhooks)
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)

## Next Steps

For webhook event handling, see `attio-webhooks-events`.
