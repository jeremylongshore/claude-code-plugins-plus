---
name: webflow-deploy-integration
description: |
  Deploy Webflow-powered applications to Vercel, Fly.io, and Google Cloud Run
  with proper secrets management and Webflow-specific health checks.
  Trigger with phrases like "deploy webflow", "webflow Vercel",
  "webflow production deploy", "webflow Cloud Run", "webflow Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Deploy Integration

## Overview

Deploy Webflow Data API v2 integrations to Vercel, Fly.io, or Google Cloud Run
with secure token management, health checks, and webhook endpoint configuration.

## Prerequisites

- Working Webflow integration (tested locally)
- Production API token with minimal scopes
- Platform CLI installed (`vercel`, `fly`, or `gcloud`)

## Instructions

### Vercel Deployment

```bash
# Store Webflow secrets in Vercel
vercel env add WEBFLOW_API_TOKEN production
vercel env add WEBFLOW_SITE_ID production
vercel env add WEBFLOW_WEBHOOK_SECRET production

# Link and deploy
vercel link
vercel --prod
```

```json
// vercel.json
{
  "env": {
    "WEBFLOW_API_TOKEN": "@webflow-api-token",
    "WEBFLOW_SITE_ID": "@webflow-site-id"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  },
  "headers": [
    {
      "source": "/api/webhooks/webflow",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "https://api.webflow.com" }
      ]
    }
  ]
}
```

Vercel serverless function for webhook endpoint:

```typescript
// api/webhooks/webflow.ts (Vercel Edge/Serverless)
import type { VercelRequest, VercelResponse } from "@vercel/node";
import crypto from "crypto";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  // Verify webhook signature
  const signature = req.headers["x-webflow-signature"] as string;
  const rawBody = JSON.stringify(req.body);
  const expected = crypto
    .createHmac("sha256", process.env.WEBFLOW_WEBHOOK_SECRET!)
    .update(rawBody)
    .digest("hex");

  if (signature !== expected) {
    return res.status(401).json({ error: "Invalid signature" });
  }

  const { triggerType, payload } = req.body;
  console.log(`Webhook received: ${triggerType}`);

  // Handle different trigger types
  switch (triggerType) {
    case "form_submission":
      await handleFormSubmission(payload);
      break;
    case "ecomm_new_order":
      await handleNewOrder(payload);
      break;
    case "site_publish":
      await handleSitePublish(payload);
      break;
  }

  res.status(200).json({ received: true });
}
```

### Fly.io Deployment

```toml
# fly.toml
app = "my-webflow-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"
  PORT = "3000"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true
  min_machines_running = 1

  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    path = "/api/health"
    timeout = "5s"
```

```bash
# Set Webflow secrets
fly secrets set WEBFLOW_API_TOKEN=your-prod-token
fly secrets set WEBFLOW_SITE_ID=your-site-id
fly secrets set WEBFLOW_WEBHOOK_SECRET=your-webhook-secret

# Deploy
fly deploy
fly status
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
COPY --from=builder /app/package.json ./

EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```bash
# Store secrets in GCP Secret Manager
echo -n "your-prod-token" | \
  gcloud secrets create webflow-api-token --data-file=-

echo -n "your-site-id" | \
  gcloud secrets create webflow-site-id --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/webflow-service

gcloud run deploy webflow-service \
  --image gcr.io/$PROJECT_ID/webflow-service \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="WEBFLOW_API_TOKEN=webflow-api-token:latest,WEBFLOW_SITE_ID=webflow-site-id:latest" \
  --min-instances=1 \
  --max-instances=10
```

### Register Webhook After Deployment

Once deployed, register your webhook URL with Webflow:

```bash
# Get your deployed URL
WEBHOOK_URL="https://your-app.vercel.app/api/webhooks/webflow"

# Register webhooks for the events you need
for TRIGGER in form_submission site_publish ecomm_new_order; do
  curl -X POST "https://api.webflow.com/v2/sites/$WEBFLOW_SITE_ID/webhooks" \
    -H "Authorization: Bearer $WEBFLOW_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"triggerType\": \"$TRIGGER\",
      \"url\": \"$WEBHOOK_URL\"
    }"
  echo " -> Registered $TRIGGER"
done

# Verify webhooks registered
curl -s "https://api.webflow.com/v2/sites/$WEBFLOW_SITE_ID/webhooks" \
  -H "Authorization: Bearer $WEBFLOW_API_TOKEN" | jq '.webhooks[].triggerType'
```

### Health Check Endpoint

```typescript
// api/health.ts — works on all platforms
import { WebflowClient } from "webflow-api";

export async function healthCheck() {
  const checks: Record<string, any> = {};
  const start = Date.now();

  // Webflow API connectivity
  try {
    const webflow = new WebflowClient({
      accessToken: process.env.WEBFLOW_API_TOKEN!,
    });
    const { sites } = await webflow.sites.list();
    checks.webflow = {
      status: "connected",
      sites: sites?.length,
      latencyMs: Date.now() - start,
    };
  } catch (error: any) {
    checks.webflow = {
      status: "disconnected",
      error: error.statusCode,
      latencyMs: Date.now() - start,
    };
  }

  return {
    status: checks.webflow.status === "connected" ? "healthy" : "degraded",
    services: checks,
    env: process.env.NODE_ENV,
    timestamp: new Date().toISOString(),
  };
}
```

## Output

- Application deployed to chosen platform
- Webflow API token securely stored as platform secret
- Webhook endpoints registered and verified
- Health check endpoint monitoring Webflow connectivity
- HTTPS enforced on all endpoints

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found at runtime | Wrong secret name | Verify with `fly secrets list` or `vercel env ls` |
| Webhook 401 | Signature mismatch | Check WEBFLOW_WEBHOOK_SECRET matches |
| Cold start timeout | Webflow API slow on first call | Set min instances > 0 |
| Health check fails | Token not loaded | Verify secret mounting in container |
| Deploy timeout | Large image | Use multi-stage Docker build |

## Resources

- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Webflow Webhooks](https://developers.webflow.com/data/docs/working-with-webhooks)

## Next Steps

For webhook handling patterns, see `webflow-webhooks-events`.
