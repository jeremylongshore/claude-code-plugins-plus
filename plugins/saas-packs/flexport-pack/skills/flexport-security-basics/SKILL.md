---
name: flexport-security-basics
description: |
  Apply Flexport API security best practices including webhook signature verification,
  API key rotation, and least-privilege access patterns.
  Trigger: "flexport security", "flexport webhook signature", "secure flexport API key".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Security Basics

## Overview

Security practices for Flexport API integrations: key management, webhook signature validation with `X-Hub-Signature`, and least-privilege access patterns for supply chain data.

## Instructions

### Step 1: Webhook Signature Verification

Flexport signs webhook payloads with HMAC-SHA256 using your webhook secret. The signature is in the `X-Hub-Signature` header.

```typescript
import crypto from 'crypto';

function verifyFlexportWebhook(
  payload: string | Buffer,
  signature: string,
  secret: string
): boolean {
  const expected = 'sha256=' + crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

// Express middleware
app.post('/webhooks/flexport', express.raw({ type: '*/*' }), (req, res) => {
  const sig = req.headers['x-hub-signature'] as string;
  if (!verifyFlexportWebhook(req.body, sig, process.env.FLEXPORT_WEBHOOK_SECRET!)) {
    return res.status(401).send('Invalid signature');
  }
  const event = JSON.parse(req.body.toString());
  // Process event...
  res.status(200).send('OK');
});
```

### Step 2: API Key Management

```bash
# Environment separation (NEVER share keys across environments)
# .env.development
FLEXPORT_API_KEY=your_dev_key
FLEXPORT_WEBHOOK_SECRET=your_dev_webhook_secret

# .env.production
FLEXPORT_API_KEY=your_prod_key
FLEXPORT_WEBHOOK_SECRET=your_prod_webhook_secret

# .gitignore — mandatory entries
.env
.env.*
!.env.example
```

### Step 3: Key Rotation Procedure

```bash
# 1. Generate new key in Flexport Portal > Settings > Developer
# 2. Deploy new key to production (dual-key period)
# 3. Verify new key works
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $NEW_FLEXPORT_API_KEY" \
  -H "Flexport-Version: 2" \
  https://api.flexport.com/shipments?per=1
# 4. Revoke old key in Portal
# 5. Remove old key from all environments
```

### Step 4: Least Privilege Access

| Role | API Scope | Use Case |
|------|-----------|----------|
| Read-only | `GET /shipments`, `GET /products` | Dashboards, reporting |
| Booking manager | `POST /bookings`, `PATCH /purchase_orders` | Operations team |
| Full access | All endpoints | Admin, CI/CD pipelines |

### Security Checklist

- [ ] API keys stored in environment variables or secret manager
- [ ] `.env` files in `.gitignore`
- [ ] Webhook signatures verified on every request
- [ ] Different keys for dev/staging/prod
- [ ] Key rotation scheduled quarterly
- [ ] Git history scanned for leaked keys
- [ ] HTTPS enforced for all API calls
- [ ] Request/response logging redacts auth headers

## Resources

- [Flexport Webhooks](https://apidocs.flexport.com/v2/tag/Webhook-Endpoints/)
- [Flexport Developer Portal](https://developers.flexport.com/)

## Next Steps

For production deployment, see `flexport-prod-checklist`.
