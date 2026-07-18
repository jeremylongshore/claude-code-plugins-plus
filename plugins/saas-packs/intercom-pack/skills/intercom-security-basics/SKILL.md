---
name: intercom-security-basics
description: 'Apply Intercom security best practices for tokens, webhook verification,
  and scopes.

  Use when securing access tokens, implementing webhook signature validation,

  or configuring least-privilege OAuth scopes.

  Trigger with phrases like "intercom security", "intercom secrets",

  "secure intercom", "intercom webhook signature", "intercom token rotation".

  '
allowed-tools: Read, Write, Grep
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
# Intercom Security Basics

## Overview

Security best practices for Intercom access tokens, webhook signature
verification, Identity Verification (HMAC), and least-privilege OAuth scopes.

The full code for each control lives in `references/` so this file stays a fast,
high-level checklist you can follow end-to-end, then drill into for depth:

- [Implementation reference](references/implementation.md) — complete webhook,
  identity, rotation, and scope code.
- [Worked examples](references/examples.md) — four end-to-end walkthroughs.

## Prerequisites

- Intercom access token or OAuth credentials
- Understanding of HMAC cryptographic signatures
- Access to Intercom Developer Hub

## Instructions

### Step 1: Secure Token Storage

Store every secret in `.env` (or a secret manager) and never commit it.

```bash
# .env (NEVER commit to git)
INTERCOM_ACCESS_TOKEN=dG9rOmFiY2RlZmdoaQ==
INTERCOM_WEBHOOK_SECRET=your-webhook-signing-secret
INTERCOM_IDENTITY_SECRET=your-identity-verification-secret

# .gitignore (mandatory entries)
.env
.env.local
.env.*.local
```

Then scan history for anything already leaked — use `Grep` (or the shell) to
search committed content for token markers:

```bash
git log --all -p | grep -i "INTERCOM_ACCESS_TOKEN\|dG9r" | head -5
# If found: rotate the token immediately, then use git-filter-repo to remove it.
```

### Step 2: Webhook Signature Verification (X-Hub-Signature)

Intercom signs webhook notifications with HMAC-SHA1 using `X-Hub-Signature`.
Verify it on every incoming webhook against the **raw** request body, using a
timing-safe comparison, and reject mismatches with `401`:

```typescript
const expectedSignature = "sha1=" + crypto
  .createHmac("sha1", secret)
  .update(payload)   // payload = raw Buffer, not parsed JSON
  .digest("hex");
return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature));
```

Full Express handler: [implementation.md — Webhook Signature Verification](references/implementation.md).

### Step 3: Identity Verification (User Hash)

Identity Verification blocks impersonation by requiring an HMAC-SHA256 of the
user's identifier, generated **server-side only**:

```typescript
crypto.createHmac("sha256", process.env.INTERCOM_IDENTITY_SECRET!)
  .update(userId)
  .digest("hex");
```

Return this `user_hash` alongside `app_id` and `user_id` for Messenger boot. Full
code: [implementation.md — Identity Verification](references/implementation.md).

### Step 4: Least-Privilege OAuth Scopes

Only request the scopes your app actually uses — excess scopes widen the blast
radius of a leaked token. The full use-case → scope mapping is in
[implementation.md — Least-Privilege OAuth Scopes](references/implementation.md).
For example, a read-only contacts integration needs just `Read contacts`, not
full CRM read/write.

### Step 5: Token Rotation Procedure

Rotate by adding the new token to your secret manager and deploying **before**
revoking the old one, so no window exists without a live token. Full procedure
(AWS / GCP / Vault examples + verification `curl`): [implementation.md — Token Rotation Procedure](references/implementation.md).

## Output

Applying this skill produces:

- A `.env` (or secret-manager entry) holding `INTERCOM_ACCESS_TOKEN`,
  `INTERCOM_WEBHOOK_SECRET`, and `INTERCOM_IDENTITY_SECRET`, with `.env` patterns
  added to `.gitignore`.
- A webhook route that returns `200` for valid `X-Hub-Signature` deliveries and
  `401` for missing or forged signatures.
- Server-side `user_hash` generation wired into the Messenger boot settings.
- An OAuth app requesting only least-privilege scopes.
- A documented, tested token-rotation runbook.

The end state is the completed **Security Checklist** below, every box ticked.

## Security Checklist

- [ ] Access tokens stored in environment variables or secret manager
- [ ] `.env` files in `.gitignore`
- [ ] Different tokens for dev/staging/production workspaces
- [ ] Webhook signatures verified on every request (X-Hub-Signature)
- [ ] Identity Verification enabled (user_hash)
- [ ] OAuth scopes are minimal (least privilege)
- [ ] Token rotation procedure documented and tested
- [ ] Git history scanned for leaked credentials
- [ ] HTTPS enforced for all webhook endpoints

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Leaked token in git | `git log -p \| grep dG9r` | Rotate immediately, remove from history |
| Invalid webhook signature | 401 from verification | Check secret matches Developer Hub |
| Missing Identity Verification | Intercom dashboard warning | Implement user_hash on server |
| Excessive OAuth scopes | Scope audit | Remove unnecessary scopes |
| Token never rotated | Age tracking | Schedule quarterly rotation |

## Examples

Four end-to-end walkthroughs live in [references/examples.md](references/examples.md):

1. **Secure a fresh integration from zero** — store the three secrets in `.env`
   and prove none are staged.
2. **Scan an existing repo for a leaked token** — `git log --all -p | grep` for
   token markers before shipping.
3. **Add webhook verification to an Express app** — reject forged payloads with
   `401` via `X-Hub-Signature`.
4. **Turn on Identity Verification for the Messenger** — server-side `user_hash`
   to stop impersonation.

Quick sanity check that a rotated token is live:

```bash
curl -s https://api.intercom.io/me \
  -H "Authorization: Bearer $NEW_TOKEN" | jq '.type'
# Should return "admin"
```

## Resources

- [Authentication](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication)
- [OAuth Scopes](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication/oauth-scopes)
- [Webhook Notifications](https://developers.intercom.com/docs/webhooks/webhook-notifications)
- [Identity Verification](https://developers.intercom.com/installing-intercom/web/identity-verification)

## Next Steps

For production deployment hardening beyond these basics, see the
`intercom-prod-checklist` skill, which covers rate limiting, error monitoring,
and staged rollout for the same integration.
