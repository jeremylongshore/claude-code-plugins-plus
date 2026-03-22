---
name: hubspot-security-basics
description: |
  Apply HubSpot security best practices for tokens, scopes, and webhook verification.
  Use when securing private app tokens, implementing least privilege scopes,
  or validating HubSpot webhook signatures.
  Trigger with phrases like "hubspot security", "hubspot token rotation",
  "secure hubspot", "hubspot scopes", "hubspot webhook verify".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Security Basics

## Overview

Security best practices for HubSpot private app tokens, OAuth scopes, webhook signature verification, and secret management.

## Prerequisites

- HubSpot private app or OAuth app configured
- Understanding of environment variables and secret management

## Instructions

### Step 1: Least-Privilege Scopes

Only request the scopes your integration actually uses:

| Use Case | Required Scopes |
|----------|----------------|
| Read contacts | `crm.objects.contacts.read` |
| Write contacts | `crm.objects.contacts.read`, `crm.objects.contacts.write` |
| Read/write deals | `crm.objects.deals.read`, `crm.objects.deals.write` |
| Marketing emails | `content` |
| Forms | `forms` |
| Contact lists | `crm.lists.read`, `crm.lists.write` |
| Properties | `crm.schemas.contacts.read` |
| Custom objects | `crm.objects.custom.read`, `crm.objects.custom.write`, `crm.schemas.custom.read` |
| Webhooks | `automation` |

**Never use:** Do not grant `all` scopes. If you regenerate a private app token, the old token is immediately revoked.

### Step 2: Token Storage

```bash
# .env (NEVER commit)
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
HUBSPOT_WEBHOOK_SECRET=your-webhook-secret

# .gitignore
.env
.env.local
.env.*.local
```

```typescript
// Validate token is present at startup
function validateConfig(): void {
  if (!process.env.HUBSPOT_ACCESS_TOKEN) {
    throw new Error('HUBSPOT_ACCESS_TOKEN is required. See .env.example');
  }
  // Never log the token
  console.log('HubSpot: Token configured', {
    prefix: process.env.HUBSPOT_ACCESS_TOKEN.substring(0, 8) + '...',
  });
}
```

### Step 3: Webhook Signature Verification (v3)

HubSpot sends webhooks with signature verification headers:

```typescript
import crypto from 'crypto';
import express from 'express';

// HubSpot v3 signature verification
// Header: X-HubSpot-Signature-v3
function verifyHubSpotSignatureV3(
  requestBody: string,
  signature: string,
  timestamp: string,
  clientSecret: string,
  requestUri: string,
  method: string = 'POST'
): boolean {
  // Reject if timestamp is older than 5 minutes (replay protection)
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - parseInt(timestamp)) > 300) {
    console.warn('HubSpot webhook timestamp too old');
    return false;
  }

  // v3: HMAC SHA-256 of method + URI + body + timestamp
  const sourceString = `${method}${requestUri}${requestBody}${timestamp}`;
  const expectedSignature = crypto
    .createHmac('sha256', clientSecret)
    .update(sourceString)
    .digest('base64');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

// Express middleware
const webhookRouter = express.Router();
webhookRouter.post('/hubspot',
  express.raw({ type: 'application/json' }),
  (req, res) => {
    const signature = req.headers['x-hubspot-signature-v3'] as string;
    const timestamp = req.headers['x-hubspot-request-timestamp'] as string;
    const requestUri = `https://${req.headers.host}${req.originalUrl}`;

    if (!verifyHubSpotSignatureV3(
      req.body.toString(), signature, timestamp,
      process.env.HUBSPOT_WEBHOOK_SECRET!, requestUri
    )) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const events = JSON.parse(req.body.toString());
    // Process events...
    res.status(200).json({ received: true });
  }
);
```

### Step 4: Token Rotation Procedure

```bash
# 1. Generate new token in HubSpot
#    Settings > Integrations > Private Apps > [Your App] > Auth tab
#    Click "Rotate token" (old token revoked immediately)

# 2. Update in your secret manager
# AWS Secrets Manager
aws secretsmanager update-secret --secret-id hubspot/production \
  --secret-string '{"access_token":"pat-na1-NEW_TOKEN"}'

# GCP Secret Manager
echo -n "pat-na1-NEW_TOKEN" | gcloud secrets versions add hubspot-token --data-file=-

# 3. Restart/redeploy your application to pick up new token

# 4. Verify new token works
curl -s https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" | jq .status
```

### Step 5: Git Secret Scanning

```yaml
# .github/workflows/secret-scan.yml
name: Secret Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for HubSpot tokens
        run: |
          if grep -rE "pat-[a-z]{2}[0-9]-[a-f0-9-]{36}" --include="*.ts" --include="*.js" --include="*.json" .; then
            echo "ERROR: HubSpot access token found in source code"
            exit 1
          fi
```

## Output

- Minimal scopes configured per use case
- Tokens stored in environment variables, never in code
- Webhook signatures verified with replay protection
- Token rotation procedure documented
- CI scanning for leaked tokens

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Token in git history | `git log -p --all -S "pat-na1"` | Rotate token immediately |
| Excessive scopes | Audit in Settings > Private Apps | Remove unneeded scopes |
| Unverified webhooks | Security audit | Add signature verification |
| Token never rotated | Track creation date | Schedule quarterly rotation |

## Resources

- [HubSpot Webhook Signatures](https://developers.hubspot.com/docs/guides/api/webhooks/overview)
- [Private Apps Guide](https://developers.hubspot.com/docs/guides/apps/private-apps/overview)
- [OAuth Scopes Reference](https://developers.hubspot.com/docs/guides/apps/authentication/scopes)

## Next Steps

For production deployment, see `hubspot-prod-checklist`.
