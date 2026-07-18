---
name: elevenlabs-security-basics
description: |
  Apply ElevenLabs security best practices for API keys, webhook HMAC
  validation, and voice data protection.
  Use when securing API keys, validating webhook signatures, or auditing
  ElevenLabs security configuration.
  Trigger with "elevenlabs security", "elevenlabs secrets", "secure elevenlabs",
  "elevenlabs API key security", "elevenlabs webhook signature",
  "elevenlabs HMAC".
allowed-tools: Read, Write, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- security
- webhooks
compatibility: Designed for Claude Code
---
# ElevenLabs Security Basics

## Overview

Security best practices for ElevenLabs API key management, webhook HMAC
signature verification, and protecting cloned voice data. ElevenLabs uses a
single API key (`xi-api-key`) and HMAC webhook authentication.

This SKILL.md carries the workflow at a high level with the essential
skeletons. Full production code for each step lives in
[references/implementation.md](references/implementation.md), and end-to-end
scenarios live in [references/examples.md](references/examples.md).

## Prerequisites

- ElevenLabs SDK installed
- Understanding of environment variables
- Access to ElevenLabs dashboard (Settings > API Keys)

## Instructions

### Step 1: API Key Management

Keep keys out of source, and add a hook that blocks accidental commits:

```bash
# .env (NEVER commit to git)
ELEVENLABS_API_KEY=sk_your_key_here

# .gitignore — MUST include these
.env
.env.local
.env.*.local
```

```bash
#!/bin/bash
# .git/hooks/pre-commit — reject staged ElevenLabs keys
if git diff --cached | grep -qE 'sk_[a-zA-Z0-9]{20,}'; then
  echo "ERROR: ElevenLabs API key detected in staged changes!"
  echo "Remove the key and use environment variables instead."
  exit 1
fi
```

### Step 2: Environment-Specific Keys

Load the key at startup, fail fast when it is missing, and warn if a production
key leaks into development. Full `getSecurityConfig()` implementation:
[references/implementation.md](references/implementation.md).

### Step 3: Webhook HMAC Signature Verification

ElevenLabs webhooks carry an `ElevenLabs-Signature` header formatted as
`t=TIMESTAMP,v1=SIGNATURE`. Verify it with HMAC-SHA256, reject timestamps older
than 5 minutes (replay protection), and use a timing-safe comparison. Full
`verifyWebhookSignature()` implementation:
[references/implementation.md](references/implementation.md).

### Step 4: Express Webhook Endpoint with Verification

Verify against the **raw** request body, respond 200 fast, then process
asynchronously so you never trip the webhook timeout. Full endpoint:
[references/implementation.md](references/implementation.md).

### Step 5: API Key Rotation Procedure

Generate the new key, validate it before cutover, push to every environment,
verify production, then revoke the old key — zero downtime. Full runbook:
[references/implementation.md](references/implementation.md).

### Step 6: Voice Data Protection

Cloned voices are biometric PII: restrict who can clone, audit-log every
operation, and require documented consent. Full policy and audit logger:
[references/implementation.md](references/implementation.md).

## Output

Applying this skill produces a hardened ElevenLabs integration:

- API keys stored only in environment variables, with `.env` gitignored and a
  pre-commit hook that blocks the `sk_` key pattern.
- A `verifyWebhookSignature()` helper and Express endpoint that reject invalid
  signatures (HTTP 401) and replayed requests (timestamp > 5 minutes).
- A documented, zero-downtime key rotation runbook.
- Structured audit logs (`elevenlabs.voice.audit`) for every voice clone,
  delete, and use, plus a completed Security Checklist below.

## Security Checklist

- [ ] API keys in environment variables (never in source code)
- [ ] `.env` files in `.gitignore`
- [ ] Different API keys for dev/staging/prod
- [ ] Pre-commit hook scanning for key patterns (`sk_`)
- [ ] Webhook signatures verified with HMAC-SHA256
- [ ] Replay protection on webhooks (5-minute timestamp check)
- [ ] Webhook failures monitored (auto-disabled after 10 consecutive failures)
- [ ] Voice cloning operations audit-logged
- [ ] Cloned voice consent documented
- [ ] API key rotation scheduled quarterly

## Webhook Failure Policy

ElevenLabs auto-disables webhooks after:

- 10+ consecutive delivery failures, AND
- Last successful delivery was 7+ days ago (or never delivered)

Always return HTTP 200 quickly from your webhook handler.

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Exposed API key | Git scanning, CI check | Rotate immediately, revoke old key |
| Invalid webhook signature | `verifyWebhookSignature()` returns false | Log and reject (HTTP 401) |
| Replay attack | Timestamp > 5 minutes old | Reject with timestamp check |
| Unauthorized voice cloning | Audit logs | Restrict clone permissions |

## Examples

Worked, end-to-end scenarios live in
[references/examples.md](references/examples.md):

- **Block a key commit before it happens** — the pre-commit hook aborts a
  commit containing `sk_...`.
- **Reject a replayed webhook** — a correct HMAC still fails on a 6-minute-old
  timestamp.
- **Rotate a leaked production key with zero downtime** — validate the new key,
  cut over, then revoke.
- **Audit a voice-clone operation** — structured JSON proving who cloned a
  voice and whether consent was on file.

## Resources

- [ElevenLabs Webhooks](https://elevenlabs.io/docs/product-guides/administration/webhooks)
- [ElevenLabs API Keys](https://elevenlabs.io/app/settings/api-keys)
- [Voice Cloning Policy](https://elevenlabs.io/safety)

## Next Steps

Once these basics are in place, harden the wider deployment: apply the
`elevenlabs-prod-checklist` skill for production readiness, schedule the
quarterly key rotation from Step 5, and wire the voice audit logs into your
central logging or SIEM so cloning activity is reviewable.
