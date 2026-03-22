---
name: adobe-security-basics
description: |
  Apply Adobe security best practices for OAuth credentials, secret rotation,
  I/O Events webhook signature verification, and least-privilege scoping.
  Use when securing API credentials, implementing webhook validation,
  or auditing Adobe security configuration.
  Trigger with phrases like "adobe security", "adobe secrets",
  "secure adobe", "adobe credential rotation", "adobe webhook signature".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Security Basics

## Overview

Security best practices for Adobe OAuth Server-to-Server credentials, I/O Events webhook signature verification, and least-privilege access control across Adobe APIs.

## Prerequisites

- Adobe Developer Console access
- Understanding of OAuth 2.0 client_credentials flow
- Access to secret management solution (Vault, AWS Secrets Manager, GCP Secret Manager)

## Instructions

### Step 1: Secure Credential Storage

```bash
# .env (NEVER commit to git)
ADOBE_CLIENT_ID=abc123def456
ADOBE_CLIENT_SECRET=p8_XYZ_your_secret_here
ADOBE_SCOPES=openid,AdobeID,firefly_api

# .gitignore — MUST include these
.env
.env.local
.env.*.local
*.pem
*.key
```

```bash
# Production: use your cloud provider's secret manager
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name adobe/production/credentials \
  --secret-string '{"client_id":"...","client_secret":"..."}'

# GCP Secret Manager
echo -n "your-client-secret" | gcloud secrets create adobe-client-secret --data-file=-

# HashiCorp Vault
vault kv put secret/adobe/prod client_id="..." client_secret="..."
```

### Step 2: Credential Rotation

Adobe OAuth Server-to-Server credentials support multiple client secrets simultaneously, enabling zero-downtime rotation:

```bash
# 1. In Adobe Developer Console, generate a NEW client_secret
#    (old secret remains valid)

# 2. Update your secret manager with the new secret
aws secretsmanager update-secret \
  --secret-id adobe/production/credentials \
  --secret-string '{"client_id":"...","client_secret":"NEW_SECRET"}'

# 3. Deploy application with new secret

# 4. Verify new secret works
curl -X POST 'https://ims-na1.adobelogin.com/ims/token/v3' \
  -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${NEW_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}"

# 5. Delete old client_secret in Developer Console
```

### Step 3: Least-Privilege Scope Selection

| Scope | Grants | Use When |
|-------|--------|----------|
| `openid` | Basic identity | Always required |
| `AdobeID` | Adobe identity info | Always required |
| `firefly_api` | Firefly image generation | Firefly workflows only |
| `ff_apis` | Firefly Services (Photoshop, Lightroom) | Creative API workflows |
| `read_organizations` | Org info access | Multi-tenant apps |

```typescript
// Per-environment scope restriction
const SCOPES_BY_ENV: Record<string, string> = {
  development: 'openid,AdobeID',                     // Minimal for testing
  staging: 'openid,AdobeID,firefly_api',              // Only APIs being tested
  production: 'openid,AdobeID,firefly_api,ff_apis',   // Full production access
};
```

### Step 4: I/O Events Webhook Signature Verification

Adobe I/O Events uses RSA-SHA256 digital signatures, not HMAC. The public keys are served from `static.adobeioevents.com`:

```typescript
// src/adobe/webhook-verify.ts
import crypto from 'crypto';

interface AdobeWebhookHeaders {
  'x-adobe-digital-signature-1': string;
  'x-adobe-digital-signature-2': string;
  'x-adobe-public-key1-path': string;
  'x-adobe-public-key2-path': string;
}

// Cache public keys (they rotate infrequently)
const publicKeyCache = new Map<string, string>();

async function getPublicKey(keyPath: string): Promise<string> {
  if (publicKeyCache.has(keyPath)) return publicKeyCache.get(keyPath)!;

  const response = await fetch(`https://static.adobeioevents.com${keyPath}`);
  const publicKey = await response.text();
  publicKeyCache.set(keyPath, publicKey);
  return publicKey;
}

export async function verifyAdobeWebhookSignature(
  rawBody: Buffer,
  headers: Record<string, string>
): Promise<boolean> {
  // Try both signatures (Adobe sends two for key rotation)
  for (const i of [1, 2]) {
    const signature = headers[`x-adobe-digital-signature-${i}`];
    const keyPath = headers[`x-adobe-public-key${i}-path`];

    if (!signature || !keyPath) continue;

    try {
      const publicKey = await getPublicKey(keyPath);
      const verifier = crypto.createVerify('RSA-SHA256');
      verifier.update(rawBody);
      if (verifier.verify(publicKey, signature, 'base64')) {
        return true;
      }
    } catch (err) {
      console.warn(`Signature ${i} verification failed:`, err);
    }
  }

  return false;
}

// Express middleware
import express from 'express';

app.post('/webhooks/adobe',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    // Handle challenge verification (registration handshake)
    if (req.query.challenge) {
      return res.json({ challenge: req.query.challenge });
    }

    // Verify digital signature
    if (!await verifyAdobeWebhookSignature(req.body, req.headers as any)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());
    await processEvent(event);
    res.status(200).json({ received: true });
  }
);
```

### Step 5: Git Secret Scanning

```yaml
# .github/workflows/secret-scan.yml
name: Adobe Secret Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan for Adobe credentials
        run: |
          # Client secrets start with p8_ (OAuth Server-to-Server)
          if grep -rE "p8_[A-Za-z0-9_-]{20,}" --include="*.ts" --include="*.js" --include="*.py" .; then
            echo "ERROR: Potential Adobe client secret found in source code"
            exit 1
          fi
          echo "No Adobe secrets detected"
```

## Security Checklist

- [ ] OAuth credentials in secret manager, not source code
- [ ] `.env` files in `.gitignore`
- [ ] Different credentials per environment (dev/staging/prod)
- [ ] Minimal scopes per environment
- [ ] Webhook signatures verified with RSA-SHA256
- [ ] Secret rotation procedure documented and tested
- [ ] Git secret scanning enabled in CI
- [ ] Access tokens cached (not re-generated per request)

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Exposed client_secret | Git scanning alert | Rotate in Developer Console immediately |
| Wrong scopes | `invalid_scope` error | Review product profile assignments |
| Unverified webhooks | Missing signature check | Implement RSA-SHA256 verification |
| Stale credentials | Auth failures in monitoring | Schedule periodic rotation |

## Resources

- [Adobe I/O Events Signature Verification](https://developer.adobe.com/events/docs/guides/sdk/sdk_signature_verification/)
- [OAuth Server-to-Server Guide](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/implementation)
- [Adobe Admin Console Roles](https://helpx.adobe.com/enterprise/using/roles.html)

## Next Steps

For production deployment, see `adobe-prod-checklist`.
