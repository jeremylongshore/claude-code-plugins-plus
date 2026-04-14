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

Set environment variables, configure `vercel.json` for webhooks and function timeouts, and update `shopify.app.toml` with the Vercel URL.

See [Vercel Deployment](references/vercel-deployment.md) for the complete configuration.

### Step 3: Fly.io Deployment

Configure `fly.toml` with health checks and min-machines, set secrets via `fly secrets set`, and deploy.

See [Fly.io Deployment](references/flyio-deployment.md) for the complete configuration.

### Step 4: Google Cloud Run Deployment

Use a multi-stage Dockerfile for minimal image size, deploy with `gcloud run deploy`, and configure secrets via Secret Manager.

See [Cloud Run Deployment](references/cloud-run-deployment.md) for Dockerfile and deploy commands.

### Step 5: Post-Deploy Verification

Run health checks, verify webhook endpoints return 401 (no HMAC), test OAuth start, and sync app config.

See [Post-Deploy Verification](references/post-deploy-verification.md) for the complete verification script.

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
SHOPIFY_API_VERSION=       # Default: latest stable. Update quarterly — see shopify.dev/docs/api/usage/versioning
SESSION_SECRET=            # For cookie signing
DATABASE_URL=              # Session storage
```

## Resources

- [Shopify App Deployment](https://shopify.dev/docs/apps/build/cli-for-apps/deploy)
- [Vercel Remix Deployment](https://vercel.com/guides/deploying-remix-with-vercel)
- [Fly.io Node.js](https://fly.io/docs/languages-and-frameworks/node/)
- [Cloud Run Quickstart](https://cloud.google.com/run/docs/quickstarts)
