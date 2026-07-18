---
name: intercom-deploy-integration
description: |
  Deploy Intercom integrations to Vercel, Fly.io, and Cloud Run with proper secrets.
  Use when deploying Intercom-powered applications to production, configuring
  platform-specific secrets, or setting up signed webhook endpoints and health checks.
  Trigger with phrases like "deploy intercom", "intercom Vercel",
  "intercom production deploy", "intercom Cloud Run", "intercom Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Deploy Integration

## Overview

Deploy Intercom-powered applications to Vercel, Fly.io, or Google Cloud Run with proper
secret management, signed webhook endpoints, and health checks. The workflow is the same
across platforms — provision two secrets, deploy, wire a `/health` probe, then register
the webhook URL — and each platform's copy-ready code lives in
[references/implementation.md](references/implementation.md).

## Prerequisites

- Intercom production access token
- Platform CLI installed (`vercel`, `flyctl`, or `gcloud`)
- Application with Intercom integration ready for deployment

## Authentication

Two secrets drive every deployment. `INTERCOM_ACCESS_TOKEN` authenticates API calls
(passed to the SDK as `new IntercomClient({ token })`); `INTERCOM_WEBHOOK_SECRET` is the
Developer Hub signing secret used to verify inbound webhook payloads (HMAC-SHA1 over the
raw body, compared against the `X-Hub-Signature` header). Store both in the platform's
secret store — never hardcode them: `vercel env add`, `fly secrets set`, or Cloud Run
Secret Manager. A mismatched webhook secret returns `401 Invalid signature`; an invalid
token surfaces as a `degraded` health check rather than a hard failure.

## Instructions

Pick the platform that matches your stack. Each step below shows the essential skeleton;
open [references/implementation.md](references/implementation.md) for the complete webhook
handler, `vercel.json`, `fly.toml`, Cloud Run deploy script, and shared health-check code.

### Step 1: Choose a platform and provision secrets

- **Vercel** (serverless): `vercel env add INTERCOM_ACCESS_TOKEN production` then
  `vercel env add INTERCOM_WEBHOOK_SECRET production`.
- **Fly.io** (long-running): `fly secrets set INTERCOM_ACCESS_TOKEN=... INTERCOM_WEBHOOK_SECRET=...`.
- **Cloud Run** (container): store both in Secret Manager and mount with `--set-secrets`.

### Step 2: Write the signed webhook handler

Read the raw request body (disable body parsing), recompute the HMAC-SHA1 signature, and
compare with `crypto.timingSafeEqual`. Return within 5 seconds — queue slower work:

```typescript
const expected = "sha1=" + crypto
  .createHmac("sha1", process.env.INTERCOM_WEBHOOK_SECRET!)
  .update(rawBody)
  .digest("hex");
if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) return res.status(401).end();
```

Write this to `api/webhooks/intercom.ts` (Vercel) or the equivalent route. Full handler,
including the raw-body read and the Vercel `config` export, is in the Vercel section of
[references/implementation.md](references/implementation.md).

### Step 3: Add a Intercom-aware health check

Expose a `/health` route that calls `client.admins.list()` and reports `healthy` /
`degraded` with latency. Edit your platform config to wire it as the liveness probe
(`fly.toml` checks block, or Cloud Run's default). Full code is in the Health Check
section of [references/implementation.md](references/implementation.md).

### Step 4: Deploy

Run the platform deploy command: `vercel --prod`, `fly deploy`, or the
`gcloud run deploy` script. Verify with `curl https://your-domain.com/health`.

### Step 5: Register the webhook URL

In Developer Hub > Webhooks, set the endpoint to `https://your-domain.com/api/webhooks/intercom`,
select topics (see the reference table below), copy the signing secret into your platform
secrets, and send a test notification to confirm a `200`.

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

## Output

A successful run produces a deployed service reachable over HTTPS with:

- Both `INTERCOM_ACCESS_TOKEN` and `INTERCOM_WEBHOOK_SECRET` stored in the platform's
  secret store (never in source).
- A signature-verifying webhook endpoint returning `200 { "received": true }` for valid
  payloads and `401` for bad signatures.
- A `/health` endpoint returning `{"status":"healthy","services":{"intercom":{"connected":true,"latencyMs":142}}}`.
- The webhook registered in Developer Hub with a passing test notification.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook 401 | Signature mismatch | Verify secret matches Developer Hub |
| Cold start timeout | Serverless spin-up | Set min instances > 0 |
| Secret not found | Missing config | Verify secrets with platform CLI |
| Health check failing | Token invalid in prod | Verify production token |
| Webhook delivery fails | 5s timeout exceeded | Queue events, process async |

## Examples

Start from the Vercel skeleton, then drill into the platform you're shipping to:

```bash
vercel env add INTERCOM_ACCESS_TOKEN production
vercel env add INTERCOM_WEBHOOK_SECRET production
vercel --prod
```

Full end-to-end walkthroughs for Vercel, Fly.io, and Cloud Run — including expected
output and how to read a failing test notification — are in
[references/examples.md](references/examples.md).

## Resources

- [Full implementation code](references/implementation.md)
- [Worked deploy examples](references/examples.md)
- [Webhook Setup](https://developers.intercom.com/docs/webhooks/setting-up-webhooks)
- [Webhook Topics](https://developers.intercom.com/docs/references/webhooks/webhook-models)
- [Vercel Docs](https://vercel.com/docs)
- [Fly.io Docs](https://fly.io/docs)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

## Next Steps

For webhook payload handling and event-processing patterns after deployment, see the
`intercom-webhooks-events` skill in this pack.
