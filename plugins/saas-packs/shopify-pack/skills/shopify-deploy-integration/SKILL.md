---
name: shopify-deploy-integration
description: |
  Deploy Shopify apps to Vercel, Fly.io, Railway, and Cloud Run with proper environment configuration.
  Use when deploying Shopify-powered applications to production,
  configuring platform-specific secrets, or setting up hosting.
  Trigger with phrases like "deploy shopify", "shopify hosting",
  "shopify Vercel", "shopify production deploy", "shopify Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*), Bash(shopify:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Deploy Integration

## Overview

Deploy Shopify apps to popular hosting platforms. Covers environment configuration, webhook URL setup, and Shopify CLI deployment for extensions.

## Prerequisites

- Shopify app tested locally with `shopify app dev`
- Platform CLI installed (vercel, fly, or gcloud)
- Production API credentials ready
- `shopify.app.toml` configured

## Instructions

### Step 1: Deploy App with Shopify CLI

```bash
# Shopify CLI handles extension deployment and app config sync
shopify app deploy

# This uploads:
# - Theme app extensions
# - Function extensions
# - App configuration (URLs, scopes, webhooks)
# But NOT your web app — you host that separately
```

### Step 2: Vercel Deployment

```bash
# Set environment variables
vercel env add SHOPIFY_API_KEY production
vercel env add SHOPIFY_API_SECRET production
vercel env add SHOPIFY_SCOPES production
vercel env add SHOPIFY_APP_URL production

# Deploy
vercel --prod
```

```json
// vercel.json
{
  "framework": "remix",
  "env": {
    "SHOPIFY_API_KEY": "@shopify-api-key",
    "SHOPIFY_API_SECRET": "@shopify-api-secret"
  },
  "headers": [
    {
      "source": "/webhooks(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" }
      ]
    }
  ],
  "functions": {
    "app/**/*.ts": { "maxDuration": 25 }
  }
}
```

Update `shopify.app.toml` with your Vercel URL:

```toml
[auth]
redirect_urls = [
  "https://your-app.vercel.app/auth/callback"
]

application_url = "https://your-app.vercel.app"
```

### Step 3: Fly.io Deployment

```toml
# fly.toml
app = "my-shopify-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"
  SHOPIFY_API_VERSION = "2024-10"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 1

[checks]
  [checks.health]
    port = 3000
    type = "http"
    interval = "15s"
    timeout = "2s"
    path = "/health"
```

```bash
# Set secrets (never in fly.toml)
fly secrets set \
  SHOPIFY_API_KEY="your_key" \
  SHOPIFY_API_SECRET="your_secret" \
  SHOPIFY_ACCESS_TOKEN="shpat_xxx"

# Deploy
fly deploy

# Check health
fly status
curl https://my-shopify-app.fly.dev/health
```

### Step 4: Google Cloud Run Deployment

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
COPY --from=builder /app/package*.json ./
RUN npm ci --production
COPY --from=builder /app/build ./build
EXPOSE 3000
CMD ["npm", "start"]
```

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/shopify-app

gcloud run deploy shopify-app \
  --image gcr.io/$PROJECT_ID/shopify-app \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 3000 \
  --set-secrets="SHOPIFY_API_KEY=shopify-api-key:latest,SHOPIFY_API_SECRET=shopify-api-secret:latest" \
  --min-instances=1 \
  --max-instances=10

# Update app URL in Shopify
# Use the Cloud Run service URL in shopify.app.toml
```

### Step 5: Post-Deploy Verification

```bash
#!/bin/bash
APP_URL="https://your-app.example.com"

echo "=== Post-Deploy Verification ==="

# Health check
echo -n "Health: "
curl -sf "$APP_URL/health" | jq '.status'

# Webhook endpoint reachable
echo -n "Webhook endpoint: "
curl -sf -o /dev/null -w "%{http_code}" -X POST "$APP_URL/webhooks"
echo " (expected 401 — no HMAC)"

# OAuth start
echo -n "OAuth: "
curl -sf -o /dev/null -w "%{http_code}" "$APP_URL/auth?shop=test.myshopify.com"
echo ""

# Run shopify app config sync
echo "Syncing app config..."
shopify app deploy --force
```

## Output

- App deployed to production hosting
- Environment variables securely configured
- Webhook endpoints accessible via HTTPS
- Health check passing
- App URLs synced to Shopify Partner Dashboard

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| OAuth redirect mismatch | App URL not updated | Update `redirect_urls` in `shopify.app.toml` and deploy |
| Webhooks not received | URL not HTTPS or unreachable | Verify public URL, check DNS |
| Cold start timeout | Serverless function slow | Set min instances to 1 |
| CSP frame-ancestors error | Missing header | Add CSP header for `*.myshopify.com` |
| `shopify app deploy` fails | CLI token invalid | Regenerate at partners.shopify.com |

## Examples

### Environment Variable Checklist

```bash
# Required for all deployments:
SHOPIFY_API_KEY=           # From Partner Dashboard
SHOPIFY_API_SECRET=        # From Partner Dashboard
SHOPIFY_SCOPES=            # e.g., "read_products,write_products"
SHOPIFY_APP_URL=           # Your deployed app URL

# For custom/private apps:
SHOPIFY_ACCESS_TOKEN=      # shpat_xxx

# Optional:
SHOPIFY_API_VERSION=       # Default: latest stable
SESSION_SECRET=            # For cookie signing
DATABASE_URL=              # Session storage
```

## Resources

- [Shopify App Deployment](https://shopify.dev/docs/apps/build/cli-for-apps/deploy)
- [Vercel Remix Deployment](https://vercel.com/guides/deploying-remix-with-vercel)
- [Fly.io Node.js](https://fly.io/docs/languages-and-frameworks/node/)
- [Cloud Run Quickstart](https://cloud.google.com/run/docs/quickstarts)

## Next Steps

For webhook handling, see `shopify-webhooks-events`.
