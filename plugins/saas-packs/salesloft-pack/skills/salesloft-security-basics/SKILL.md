---
name: salesloft-security-basics
description: |
  Secure SalesLoft OAuth tokens, API keys, and webhook signatures.
  Use when implementing token rotation, securing webhook endpoints,
  or auditing SalesLoft API access controls.
  Trigger: "salesloft security", "salesloft secrets", "secure salesloft", "salesloft token rotation".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Security Basics

## Overview

Secure SalesLoft API integrations: OAuth token management, webhook signature verification, secret storage, and scope-based access control. SalesLoft uses OAuth 2.0 bearer tokens and HMAC-SHA256 webhook signatures.

## Instructions

### Step 1: Secret Storage

```bash
# .gitignore -- NEVER commit credentials
.env
.env.local
.env.*.local

# .env
SALESLOFT_CLIENT_ID=app-client-id
SALESLOFT_CLIENT_SECRET=app-secret
SALESLOFT_WEBHOOK_SECRET=webhook-signing-secret
```

```typescript
// Validate secrets at startup
const required = ['SALESLOFT_CLIENT_ID', 'SALESLOFT_CLIENT_SECRET'];
for (const key of required) {
  if (!process.env[key]) throw new Error(`Missing required env: ${key}`);
}
```

### Step 2: Token Lifecycle Management

```typescript
// Store tokens securely with expiry tracking
interface TokenStore {
  accessToken: string;
  refreshToken: string;
  expiresAt: number; // Unix timestamp
}

async function getValidToken(store: TokenStore): Promise<string> {
  // Refresh 5 minutes before expiry
  if (Date.now() > (store.expiresAt - 300) * 1000) {
    const refreshed = await refreshAccessToken(store.refreshToken);
    store.accessToken = refreshed.access_token;
    store.refreshToken = refreshed.refresh_token;
    store.expiresAt = Math.floor(Date.now() / 1000) + refreshed.expires_in;
    await persistTokenStore(store); // Save to DB or secret manager
  }
  return store.accessToken;
}
```

### Step 3: Webhook Signature Verification

```typescript
import crypto from 'crypto';

function verifyWebhookSignature(
  rawBody: Buffer,
  signature: string,
  timestamp: string,
  secret: string,
): boolean {
  // Reject stale webhooks (replay attack prevention)
  const age = Math.abs(Date.now() / 1000 - parseInt(timestamp));
  if (age > 300) return false; // 5-minute window

  const expected = crypto
    .createHmac('sha256', secret)
    .update(`${timestamp}.${rawBody.toString()}`)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature), Buffer.from(expected)
  );
}
```

### Step 4: OAuth Scope Minimization

| Use Case | Required Scopes | Avoid |
|----------|----------------|-------|
| Read-only dashboard | `people:read`, `cadences:read` | `*:write` |
| Cadence enrollment | `people:read`, `cadence_memberships:create` | `admin` |
| Full sync | `people:*`, `cadences:*`, `activities:read` | Team admin scopes |

### Step 5: Security Checklist

- [ ] OAuth tokens stored in secret manager (not env files in prod)
- [ ] Refresh tokens encrypted at rest
- [ ] Webhook endpoints verify signatures before processing
- [ ] `.env` files in `.gitignore`
- [ ] Different OAuth apps for dev/staging/prod
- [ ] Token refresh runs before expiry (not after 401)
- [ ] API logs monitored for unusual access patterns

## Error Handling

| Issue | Detection | Response |
|-------|-----------|----------|
| Token leaked in git | GitHub secret scanning alerts | Revoke immediately, rotate |
| Webhook replay attack | Timestamp > 5 min old | Reject request |
| Brute force on webhook | High 401 rate | Rate limit webhook endpoint |

## Resources

- [OAuth Authorization Code](https://developers.salesloft.com/docs/platform/api-basics/oauth-authentication/)
- [Client Credentials](https://developers.salesloft.com/docs/platform/api-basics/client-creds/)
- [API Logs](https://developers.salesloft.com/docs/platform/guides/api-logs/)

## Next Steps

For production deployment, see `salesloft-prod-checklist`.
