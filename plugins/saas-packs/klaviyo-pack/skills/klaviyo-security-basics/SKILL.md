---
name: klaviyo-security-basics
description: |
  Apply Klaviyo security best practices for API key management and access control.
  Use when securing API keys, configuring OAuth scopes, implementing webhook
  signature verification, or auditing Klaviyo security configuration.
  Trigger with phrases like "klaviyo security", "klaviyo secrets",
  "secure klaviyo", "klaviyo API key security", "klaviyo OAuth".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
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

### Step 2: Environment Variable Configuration

```bash
# .env (NEVER commit)
KLAVIYO_PRIVATE_KEY=pk_***************************************
KLAVIYO_PUBLIC_KEY=UXxxXx
KLAVIYO_WEBHOOK_SIGNING_SECRET=whsec_*************************

# .gitignore -- mandatory entries
.env
.env.local
.env.*.local
```

```typescript
// src/config/klaviyo.ts -- validated config loader
function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required env: ${name}`);
  return value;
}

export const klaviyoConfig = {
  privateKey: requireEnv('KLAVIYO_PRIVATE_KEY'),
  publicKey: process.env.KLAVIYO_PUBLIC_KEY || '',
  webhookSecret: process.env.KLAVIYO_WEBHOOK_SIGNING_SECRET || '',
};
```

### Step 3: Least-Privilege API Key Scopes

Create separate API keys per environment with minimal scopes:

| Environment | Recommended Scopes | Rationale |
|-------------|-------------------|-----------|
| Development | `profiles:read`, `events:read`, `lists:read` | Read-only exploration |
| Staging | `profiles:read/write`, `events:write`, `lists:read/write` | Full test coverage |
| Production | Exact scopes your app needs | Minimize blast radius |
| CI/CD | `profiles:read`, `events:read` | Smoke tests only |

```bash
# Use separate env vars per environment
KLAVIYO_PRIVATE_KEY_DEV=pk_dev_***
KLAVIYO_PRIVATE_KEY_STAGING=pk_staging_***
KLAVIYO_PRIVATE_KEY_PROD=pk_prod_***
```

### Step 4: Webhook Signature Verification (HMAC-SHA256)

Klaviyo signs webhook payloads using HMAC-SHA256 with your webhook signing secret.

```typescript
// src/klaviyo/webhook-verify.ts
import crypto from 'crypto';

/**
 * Verify Klaviyo webhook signature.
 * Klaviyo uses the webhook signing secret (set when creating the webhook)
 * to compute an HMAC-SHA256 signature of the payload.
 */
export function verifyKlaviyoWebhookSignature(
  payload: Buffer | string,
  signature: string,
  secret: string
): boolean {
  if (!signature || !secret) return false;

  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(typeof payload === 'string' ? payload : payload.toString())
    .digest('base64');

  // Timing-safe comparison to prevent timing attacks
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  } catch {
    return false;  // Different lengths
  }
}
```

### Step 5: Express Webhook Middleware

```typescript
import express from 'express';

app.post('/webhooks/klaviyo',
  express.raw({ type: 'application/json' }),
  (req, res) => {
    const signature = req.headers['klaviyo-webhook-signature'] as string;

    if (!verifyKlaviyoWebhookSignature(
      req.body,
      signature,
      process.env.KLAVIYO_WEBHOOK_SIGNING_SECRET!
    )) {
      console.warn('[Security] Invalid webhook signature rejected');
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());
    // Process verified event...
    res.status(200).json({ received: true });
  }
);
```

### Step 6: API Key Rotation Procedure

```bash
# 1. Generate new key in Klaviyo dashboard (Settings > API Keys)
#    - Name it with date: "Production API Key 2025-03"
#    - Assign same scopes as the old key

# 2. Deploy new key (zero-downtime)
#    Update secret in your deployment platform:
#    - Vercel: vercel env add KLAVIYO_PRIVATE_KEY production
#    - AWS: aws secretsmanager update-secret --secret-id klaviyo-key --secret-string pk_new_***
#    - GCP: echo -n "pk_new_***" | gcloud secrets versions add klaviyo-key --data-file=-

# 3. Verify new key works
curl -s -w "%{http_code}" -o /dev/null \
  -H "Authorization: Klaviyo-API-Key pk_new_***" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/"

# 4. Revoke old key in Klaviyo dashboard
#    Settings > API Keys > Delete old key

# 5. Audit: check logs for any 401s after rotation
```

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

## Resources

- [Authenticate API Requests](https://developers.klaviyo.com/en/docs/authenticate_)
- [OAuth Setup](https://developers.klaviyo.com/en/docs/set_up_oauth)
- [Webhooks API Overview](https://developers.klaviyo.com/en/reference/webhooks_api_overview)

## Next Steps

For production deployment, see `klaviyo-prod-checklist`.
