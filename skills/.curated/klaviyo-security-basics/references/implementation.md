# Klaviyo Security — Full Implementation

Complete, copy-paste-ready code for the workflow summarized in `SKILL.md`. Each
section maps to a step in the skill body.

## Environment Variable Configuration

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

## Least-Privilege API Key Scopes

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

## Webhook Signature Verification (HMAC-SHA256)

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

## Express Webhook Middleware

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

## API Key Rotation Procedure

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
