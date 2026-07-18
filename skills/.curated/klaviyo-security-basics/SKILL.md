---
name: klaviyo-security-basics
description: 'Apply Klaviyo security best practices for API key management and access
  control.

  Use when securing API keys, configuring OAuth scopes, implementing webhook

  signature verification, or auditing Klaviyo security configuration.

  Trigger with phrases like "klaviyo security", "klaviyo secrets",

  "secure klaviyo", "klaviyo API key security", "klaviyo OAuth".

  '
allowed-tools: Read, Write, Edit, Grep
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
# Klaviyo Security Basics

## Overview

Security best practices for Klaviyo: API key types, OAuth scopes, webhook HMAC-SHA256 signature verification, and secret rotation procedures.

## Prerequisites

- Klaviyo account with API key access
- Understanding of environment variables and secret management
- Access to Klaviyo dashboard (Settings > API Keys)

## Instructions

### Step 1: Understand Key Types

| Key Type | Format | Use Case | Sensitivity |
|----------|--------|----------|-------------|
| Private API Key | `pk_*` (40+ chars) | Server-side REST API | **CRITICAL** -- never expose client-side |
| Public API Key | 6 alphanumeric chars | Client-side Track/Identify only | Low -- safe in browser JS |

Private keys authenticate via `Authorization: Klaviyo-API-Key pk_***` header. Public keys pass as `company_id` query parameter.

### Step 2: Store Keys in Environment Variables

Keep every private key and the webhook signing secret out of source: load them
from `.env` (git-ignored) through a validated config loader that throws on a
missing secret, so misconfiguration fails at boot instead of at first API call.

```typescript
// src/config/klaviyo.ts -- validated config loader (skeleton)
export const klaviyoConfig = {
  privateKey: requireEnv('KLAVIYO_PRIVATE_KEY'),        // throws if absent
  publicKey: process.env.KLAVIYO_PUBLIC_KEY || '',
  webhookSecret: process.env.KLAVIYO_WEBHOOK_SIGNING_SECRET || '',
};
```

Full `.env` template, `.gitignore` entries, and the `requireEnv` helper:
[implementation.md → Environment Variable Configuration](references/implementation.md#environment-variable-configuration).

### Step 3: Scope Keys per Environment (Least Privilege)

Issue a separate key for each environment with only the scopes that environment
needs — read-only in dev and CI, full read/write in staging, the exact production
scope set in prod — so a leaked key has the smallest possible blast radius. Scope
table and per-environment env-var layout:
[implementation.md → Least-Privilege API Key Scopes](references/implementation.md#least-privilege-api-key-scopes).

### Step 4: Verify Webhook Signatures (HMAC-SHA256)

Klaviyo signs each webhook payload with your signing secret. Recompute the
HMAC-SHA256 digest over the raw body and compare with `crypto.timingSafeEqual`
to defeat timing attacks; reject anything that does not match with `401`.

```typescript
const expected = crypto.createHmac('sha256', secret)
  .update(rawBody).digest('base64');
return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
```

Full verifier plus the Express raw-body middleware that returns
`401 Invalid signature`:
[implementation.md → Webhook Signature Verification](references/implementation.md#webhook-signature-verification-hmac-sha256)
and [Express Webhook Middleware](references/implementation.md#express-webhook-middleware).

### Step 5: Rotate Keys with Zero Downtime

Rotate private keys on a schedule (quarterly) or immediately on suspected leak:
generate a replacement with identical scopes, deploy it to the secret store,
verify with a `curl` against `/api/accounts/`, then revoke the old key and watch
logs for `401`s. Full five-step runbook with per-platform commands:
[implementation.md → API Key Rotation Procedure](references/implementation.md#api-key-rotation-procedure).

## Security Checklist

- [ ] Private API keys stored in environment variables / secret manager
- [ ] `.env` files in `.gitignore`
- [ ] Different API keys per environment (dev/staging/prod)
- [ ] Minimal scopes per environment
- [ ] Webhook signatures verified with HMAC-SHA256
- [ ] API key rotation scheduled (quarterly recommended)
- [ ] No private keys in client-side code
- [ ] CI/CD uses read-only key for tests
- [ ] Git history scanned for leaked keys (`git log -p | grep pk_`)

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Leaked private key | Git scanning, `trufflehog` | Revoke immediately, rotate |
| Excessive scopes | Scope audit | Reduce to minimum required |
| Missing webhook verification | Code review | Add HMAC check |
| Key not rotated | Age > 90 days | Schedule rotation |
| 401s after rotation | Log monitoring | Verify all services updated |

## Output

Applying this skill produces a hardened Klaviyo integration:

- A git-ignored `.env` plus a `src/config/klaviyo.ts` loader that fails fast on a
  missing private key.
- Environment-scoped API keys (dev/staging/prod/CI) each holding minimum scopes.
- A webhook endpoint that returns `200 { "received": true }` only for payloads
  whose HMAC-SHA256 signature verifies, and `401 { "error": "Invalid signature" }`
  for everything else.
- A documented, zero-downtime rotation runbook and a completed security checklist.

## Examples

Three worked scenarios — validated config loader, rejecting a forged webhook, and
zero-downtime key rotation — with inputs and expected results are in
[examples.md](references/examples.md). Quick sketch of the webhook case:

```text
POST /webhooks/klaviyo  (tampered body, original signature)
  → verifyKlaviyoWebhookSignature() recomputes HMAC → mismatch
  → 401 { "error": "Invalid signature" }, logged as rejected
```

See [examples.md](references/examples.md) for the full walkthrough of each.

## Resources

- [Authenticate API Requests](https://developers.klaviyo.com/en/docs/authenticate_)
- [OAuth Setup](https://developers.klaviyo.com/en/docs/set_up_oauth)
- [Webhooks API Overview](https://developers.klaviyo.com/en/reference/webhooks_api_overview)
- [implementation.md](references/implementation.md) — full copy-paste code for every step
- [examples.md](references/examples.md) — end-to-end worked scenarios

## Next Steps

For production hardening beyond secrets — rate limits, monitoring, and deploy
gates — see the `klaviyo-prod-checklist` skill in this pack.
