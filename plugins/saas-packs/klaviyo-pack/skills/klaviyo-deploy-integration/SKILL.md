---
name: klaviyo-deploy-integration
description: 'Deploy Klaviyo integrations to Vercel, Fly.io, and Cloud Run platforms.

  Use when deploying Klaviyo-powered applications to production,

  configuring platform-specific secrets, or setting up deployment pipelines.

  Trigger with phrases like "deploy klaviyo", "klaviyo Vercel",

  "klaviyo production deploy", "klaviyo Cloud Run", "klaviyo Fly.io".

  '
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Deploy Integration

## Overview

Deploy Klaviyo-powered applications to Vercel, Fly.io, and Google Cloud Run
with proper secrets management and health checks. Every platform follows the
same shape — store the private key + webhook secret, wire a config file,
deploy, verify. The lean skeleton lives here; full per-platform recipes live
in [references/platform-deployments.md](references/platform-deployments.md).

## Prerequisites

- Klaviyo production API key (`pk_*`)
- Platform CLI installed (`vercel`, `fly`, or `gcloud`)
- Application tested with `klaviyo-api` SDK
- `klaviyo-prod-checklist` completed

## Instructions

The workflow is identical across platforms; only the CLI verbs change. Read
the target platform's section in
[references/platform-deployments.md](references/platform-deployments.md), then:

1. **Store secrets** — inject `KLAVIYO_PRIVATE_KEY` and
   `KLAVIYO_WEBHOOK_SIGNING_SECRET` via the platform's secret store
   (`vercel env add`, `fly secrets set`, or `gcloud secrets create`). Never
   commit these to the repo.
2. **Write the platform config** — use Write/Edit to create `vercel.json`,
   `fly.toml`, or a `Dockerfile` that binds the secrets and exposes a health
   path. See the reference for the exact file contents.
3. **Add the universal health check** — expose `src/health.ts` (identical on
   all platforms) at the path each platform probes (`/api/health` on Vercel,
   `/health` on Fly.io and Cloud Run).
4. **Deploy** — run `vercel --prod`, `fly deploy`, or `gcloud run deploy`.
5. **Verify** — `curl` the health endpoint and confirm
   `services.klaviyo.connected` is `true`.

### Vercel skeleton (first example)

```bash
vercel env add KLAVIYO_PRIVATE_KEY production          # paste pk_*** when prompted
vercel env add KLAVIYO_WEBHOOK_SIGNING_SECRET production
# configure vercel.json (see reference), then:
vercel --prod
curl -s https://your-app.vercel.app/api/health | jq '.services.klaviyo'
```

Fly.io (`fly secrets set` + `fly.toml` + `fly deploy`) and Cloud Run
(`gcloud secrets create` + `Dockerfile` + `gcloud run deploy --set-secrets`)
follow the same five steps — full commands and config files are in the
[reference walkthroughs](references/platform-deployments.md).

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

## Examples

**Deploy to Fly.io with a health check.** Set the two secrets, deploy, and
confirm connectivity:

```bash
fly secrets set KLAVIYO_PRIVATE_KEY=pk_*** \
  KLAVIYO_WEBHOOK_SIGNING_SECRET=whsec_***
fly deploy
curl -s https://my-klaviyo-app.fly.dev/health | jq '.services.klaviyo'
# → { "connected": true, "latencyMs": 142 }
```

**Verify a webhook signature (HMAC-SHA256).** Every platform's webhook route
must timing-safe-compare the `klaviyo-webhook-signature` header against an HMAC
of the raw body keyed with the signing secret — a 401 otherwise. The full
Vercel handler, `vercel.json`, `fly.toml`, the Cloud Run `Dockerfile`, and the
universal `src/health.ts` are in
[references/platform-deployments.md](references/platform-deployments.md).

For webhook event handling beyond signature verification, see the
`klaviyo-webhooks-events` skill.

## Resources

- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Fly.io Secrets](https://fly.io/docs/apps/secrets/)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Klaviyo API Reference](https://developers.klaviyo.com/en/reference/api_overview)
- [Full platform walkthroughs](references/platform-deployments.md) — verbatim commands, config files, and code for all three platforms
