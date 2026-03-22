---
name: elevenlabs-security-basics
description: |
  Apply ElevenLabs security best practices for API keys, webhook HMAC validation,
  and voice data protection.
  Use when securing API keys, validating webhook signatures,
  or auditing ElevenLabs security configuration.
  Trigger: "elevenlabs security", "elevenlabs secrets",
  "secure elevenlabs", "elevenlabs API key security",
  "elevenlabs webhook signature", "elevenlabs HMAC".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, security, webhooks]
compatible-with: claude-code
---

# ElevenLabs Security Basics

## Overview

Security best practices for ElevenLabs API key management, webhook HMAC signature verification, and protecting cloned voice data. ElevenLabs uses a single API key (`xi-api-key`) and HMAC webhook authentication.

## Prerequisites

- ElevenLabs SDK installed
- Understanding of environment variables
- Access to ElevenLabs dashboard (Settings > API Keys)

## Instructions

### Step 1: API Key Management

```bash
# .env (NEVER commit to git)
ELEVENLABS_API_KEY=sk_your_key_here

# .gitignore — MUST include these
.env
.env.local
.env.*.local
```

**Git pre-commit hook** to prevent accidental key commits:
```bash
#!/bin/bash
# .git/hooks/pre-commit
if git diff --cached | grep -qE 'sk_[a-zA-Z0-9]{20,}'; then
  echo "ERROR: ElevenLabs API key detected in staged changes!"
  echo "Remove the key and use environment variables instead."
  exit 1
fi
```

### Step 2: Environment-Specific Keys

```typescript
// src/elevenlabs/config.ts
interface ElevenLabsSecurityConfig {
  apiKey: string;
  webhookSecret: string;
  environment: "development" | "staging" | "production";
}

export function getSecurityConfig(): ElevenLabsSecurityConfig {
  const env = (process.env.NODE_ENV || "development") as ElevenLabsSecurityConfig["environment"];

  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    throw new Error("ELEVENLABS_API_KEY is required");
  }

  // Warn if production key is used in dev
  if (env === "development" && apiKey.startsWith("sk_live_")) {
    console.warn("WARNING: Using production API key in development environment");
  }

  return {
    apiKey,
    webhookSecret: process.env.ELEVENLABS_WEBHOOK_SECRET || "",
    environment: env,
  };
}
```

### Step 3: Webhook HMAC Signature Verification

ElevenLabs webhooks include an `ElevenLabs-Signature` header for HMAC verification:

```typescript
// src/elevenlabs/webhook-verify.ts
import crypto from "crypto";

/**
 * Verify ElevenLabs webhook signature using HMAC-SHA256.
 * The shared secret is generated when you create a webhook in the dashboard.
 */
export function verifyWebhookSignature(
  payload: string | Buffer,
  signatureHeader: string,
  secret: string
): boolean {
  if (!signatureHeader || !secret) return false;

  // ElevenLabs signature format: t=<timestamp>,v1=<signature>
  const parts = signatureHeader.split(",");
  const timestamp = parts.find(p => p.startsWith("t="))?.slice(2);
  const signature = parts.find(p => p.startsWith("v1="))?.slice(3);

  if (!timestamp || !signature) return false;

  // Reject timestamps older than 5 minutes (replay protection)
  const age = Math.floor(Date.now() / 1000) - parseInt(timestamp);
  if (age > 300) {
    console.error("Webhook timestamp too old:", age, "seconds");
    return false;
  }

  // Compute expected HMAC
  const signedPayload = `${timestamp}.${payload.toString()}`;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(signedPayload)
    .digest("hex");

  // Timing-safe comparison to prevent timing attacks
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature, "hex"),
      Buffer.from(expected, "hex")
    );
  } catch {
    return false;
  }
}
```

### Step 4: Express Webhook Endpoint with Verification

```typescript
import express from "express";
import { verifyWebhookSignature } from "./webhook-verify";

const app = express();

// IMPORTANT: Must use raw body for signature verification
app.post("/webhooks/elevenlabs",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const signature = req.headers["elevenlabs-signature"] as string;
    const secret = process.env.ELEVENLABS_WEBHOOK_SECRET!;

    if (!verifyWebhookSignature(req.body, signature, secret)) {
      console.error("Webhook signature verification failed");
      return res.status(401).json({ error: "Invalid signature" });
    }

    const event = JSON.parse(req.body.toString());

    // Return 200 quickly to acknowledge receipt
    // Process asynchronously to avoid webhook timeout/disable
    res.status(200).json({ received: true });

    processWebhookAsync(event).catch(console.error);
  }
);
```

### Step 5: API Key Rotation Procedure

```bash
# 1. Generate new API key in ElevenLabs dashboard
#    Settings > API Keys > Create new key

# 2. Test new key before rotating
curl -s https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: sk_new_key_here" | jq '.subscription.tier'

# 3. Update in all environments
# Vercel:
vercel env add ELEVENLABS_API_KEY production

# Fly.io:
fly secrets set ELEVENLABS_API_KEY=sk_new_key_here

# GitHub Actions:
gh secret set ELEVENLABS_API_KEY --body "sk_new_key_here"

# 4. Deploy with new key
# 5. Verify production works
# 6. Delete old key in ElevenLabs dashboard
```

### Step 6: Voice Data Protection

```typescript
// Cloned voices contain biometric data — treat as PII
const voiceSecurityPolicy = {
  // Restrict who can create/delete cloned voices
  clonePermissions: "admin_only",

  // Log all voice cloning operations
  auditCloning: true,

  // Require consent documentation before cloning
  consentRequired: true,

  // Auto-delete test clones after N days
  testVoiceTtlDays: 30,
};

// Audit log for voice operations
function logVoiceOperation(operation: string, voiceId: string, userId: string) {
  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    type: "elevenlabs.voice.audit",
    operation,  // "clone", "delete", "use"
    voiceId,
    userId,
  }));
}
```

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

## Resources

- [ElevenLabs Webhooks](https://elevenlabs.io/docs/overview/administration/webhooks)
- [ElevenLabs API Keys](https://elevenlabs.io/app/settings/api-keys)
- [Voice Cloning Policy](https://elevenlabs.io/safety)

## Next Steps

For production deployment, see `elevenlabs-prod-checklist`.
