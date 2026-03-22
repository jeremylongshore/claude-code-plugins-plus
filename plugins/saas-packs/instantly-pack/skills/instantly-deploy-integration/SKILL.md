---
name: instantly-deploy-integration
description: |
  Deploy Instantly.ai webhook receivers and API integrations to cloud platforms.
  Use when deploying to Vercel, Cloud Run, or Fly.io,
  or setting up production webhook endpoints.
  Trigger with phrases like "deploy instantly", "instantly cloud run",
  "instantly vercel", "instantly webhook deployment", "instantly production deploy".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, deployment, vercel, cloud-run]

---
# Instantly Deploy Integration

## Overview
Deploy Instantly API v2 integrations — primarily webhook receivers and automation services — to cloud platforms. Instantly webhooks require a public HTTPS endpoint that responds within 30 seconds (3 retries on failure). This skill covers Vercel serverless functions, Google Cloud Run containers, and Fly.io deployments.

## Prerequisites
- Completed `instantly-install-auth` setup
- Working Instantly integration tested locally (see `instantly-local-dev-loop`)
- Cloud platform account (Vercel, GCP, or Fly.io)
- Domain or HTTPS URL for webhook endpoint

## Instructions

### Option A: Vercel Serverless Functions
```typescript
// api/webhooks/instantly.ts — Vercel serverless function
import type { VercelRequest, VercelResponse } from "@vercel/node";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  // Validate webhook secret
  const secret = req.headers["x-webhook-secret"];
  if (secret !== process.env.INSTANTLY_WEBHOOK_SECRET) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  const { event_type, data } = req.body;

  // Respond immediately — Instantly expects 2xx within 30s
  res.status(200).json({ received: true });

  // Process event asynchronously
  try {
    switch (event_type) {
      case "reply_received":
        await syncReplyToCRM(data);
        break;
      case "email_bounced":
        await handleBounce(data);
        break;
      case "lead_interested":
        await notifySalesTeam(data);
        break;
      case "lead_unsubscribed":
        await addToBlockList(data);
        break;
    }
  } catch (err) {
    console.error(`Webhook processing error: ${event_type}`, err);
  }
}

async function addToBlockList(data: { lead_email: string }) {
  await fetch("https://api.instantly.ai/api/v2/block-lists-entries", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.INSTANTLY_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ bl_value: data.lead_email }),
  });
}
```

```bash
# Deploy to Vercel
vercel env add INSTANTLY_API_KEY
vercel env add INSTANTLY_WEBHOOK_SECRET
vercel deploy --prod
```

### Option B: Google Cloud Run
```dockerfile
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./
EXPOSE 8080
ENV PORT=8080
CMD ["node", "dist/server.js"]
```

```typescript
// src/server.ts — Express server for Cloud Run
import express from "express";
import { instantly } from "./instantly";

const app = express();
app.use(express.json());

app.get("/health", (_, res) => res.json({ status: "ok" }));

app.post("/webhooks/instantly", async (req, res) => {
  const secret = req.headers["x-webhook-secret"];
  if (secret !== process.env.INSTANTLY_WEBHOOK_SECRET) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  res.status(200).json({ received: true });

  const { event_type, data } = req.body;
  console.log(`Webhook: ${event_type}`, JSON.stringify(data).slice(0, 200));

  // Process based on event type
  if (event_type === "reply_received") {
    // Update lead interest status
    await instantly("/leads/update-interest-status", {
      method: "POST",
      body: JSON.stringify({
        lead_email: data.lead_email,
        campaign_id: data.campaign_id,
        interest_value: 1, // Interested
      }),
    });
  }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`Listening on port ${PORT}`));
```

```bash
set -euo pipefail
# Deploy to Cloud Run
gcloud run deploy instantly-webhooks \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "INSTANTLY_API_KEY=${INSTANTLY_API_KEY},INSTANTLY_WEBHOOK_SECRET=${INSTANTLY_WEBHOOK_SECRET}" \
  --min-instances 1 \
  --max-instances 10 \
  --memory 256Mi \
  --cpu 1
```

### Option C: Fly.io
```toml
# fly.toml
app = "instantly-webhooks"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[env]
  NODE_ENV = "production"
```

```bash
set -euo pipefail
fly launch --name instantly-webhooks
fly secrets set INSTANTLY_API_KEY="your-key" INSTANTLY_WEBHOOK_SECRET="your-secret"
fly deploy
```

### Step 2: Register Webhook After Deployment
```typescript
async function registerProductionWebhook(deployedUrl: string) {
  const webhook = await instantly<{ id: string; name: string }>("/webhooks", {
    method: "POST",
    body: JSON.stringify({
      name: "Production CRM Sync",
      target_hook_url: `${deployedUrl}/webhooks/instantly`,
      event_type: "all_events",
      headers: {
        "X-Webhook-Secret": process.env.INSTANTLY_WEBHOOK_SECRET,
      },
    }),
  });

  console.log(`Webhook registered: ${webhook.id}`);

  // Test the webhook
  await instantly(`/webhooks/${webhook.id}/test`, { method: "POST" });
  console.log("Test webhook sent — check your endpoint logs");
}
```

### Step 3: Post-Deploy Verification
```bash
set -euo pipefail
DEPLOY_URL="https://instantly-webhooks-abc123.run.app"

# Health check
curl -s ${DEPLOY_URL}/health | jq .

# Test webhook endpoint
curl -X POST ${DEPLOY_URL}/webhooks/instantly \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: ${INSTANTLY_WEBHOOK_SECRET}" \
  -d '{"event_type":"reply_received","data":{"lead_email":"test@example.com"}}'
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Webhook delivery fails | Endpoint returns non-2xx | Ensure 200 response before async processing |
| Cold start timeout | Serverless function too slow | Set `min-instances=1` or use always-on |
| Secret not available | Env var not set | Verify with `fly secrets list` or cloud console |
| Webhook retries flooding | Processing takes >30s | Return 200 immediately, process async |

## Resources
- [Instantly Webhooks API](https://developer.instantly.ai/api/v2/webhook)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Vercel Serverless Functions](https://vercel.com/docs/functions)

## Next Steps
For webhook event handling patterns, see `instantly-webhooks-events`.
