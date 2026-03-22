---
name: canva-security-basics
description: |
  Apply Canva Connect API security best practices for OAuth tokens and access control.
  Use when securing OAuth credentials, implementing least-privilege scopes,
  or auditing Canva integration security.
  Trigger with phrases like "canva security", "canva secrets",
  "secure canva", "canva token security", "canva OAuth security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Security Basics

## Overview

Security best practices for Canva Connect API OAuth 2.0 tokens, client credentials, and webhook verification. The Canva API uses OAuth with PKCE — there are no static API keys.

## Token Security

### Never Expose Client Secrets

```bash
# .env (NEVER commit)
CANVA_CLIENT_ID=OCAxxxxxxxxxxxxxxxx
CANVA_CLIENT_SECRET=xxxxxxxxxxxxxxxx

# .gitignore — mandatory entries
.env
.env.local
.env.*.local
```

```typescript
// WRONG — client-side JavaScript can't safely hold secrets
// Token exchange and refresh MUST happen server-side
// "Requests that require authenticating with your client ID and
// client secret can't be made from a web-browser client" — Canva docs
```

### Token Storage

```typescript
// Store tokens encrypted at rest — they grant access to user's Canva account
interface SecureTokenStore {
  save(userId: string, tokens: {
    accessToken: string;   // Valid ~4 hours
    refreshToken: string;  // Single-use — always save the latest
    expiresAt: number;
  }): Promise<void>;

  get(userId: string): Promise<CanvaTokens | null>;
  delete(userId: string): Promise<void>;
}

// Production: use your database with encryption
// Never store tokens in: localStorage, cookies without httpOnly, log files, git
```

### Token Revocation

```typescript
// Revoke tokens when user disconnects your integration
async function revokeCanvaToken(token: string, clientId: string, clientSecret: string) {
  const basicAuth = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

  await fetch('https://api.canva.com/rest/v1/oauth/revoke', {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${basicAuth}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({ token }),
  });
}
```

## Least-Privilege Scopes

```typescript
// Request ONLY the scopes you need — scopes don't cascade
// e.g., asset:write does NOT grant asset:read

const SCOPE_PROFILES = {
  // Read-only integration — view designs and templates
  readonly: ['design:meta:read', 'brandtemplate:meta:read', 'folder:read'],

  // Content creation — create and export designs
  creator: ['design:content:write', 'design:content:read', 'design:meta:read', 'asset:write', 'asset:read'],

  // Full collaboration — includes comments and webhooks
  collaborator: [
    'design:content:write', 'design:content:read', 'design:meta:read',
    'asset:write', 'asset:read', 'comment:read', 'comment:write',
    'collaboration:event',
  ],
};
```

## Webhook Signature Verification

Canva signs webhook payloads with JWK. Verify before processing.

```typescript
import { createRemoteJWKSet, jwtVerify } from 'jose';

// Fetch Canva's public keys for webhook verification
// GET https://api.canva.com/rest/v1/connect/keys
const JWKS = createRemoteJWKSet(
  new URL('https://api.canva.com/rest/v1/connect/keys')
);

async function verifyCanvaWebhook(
  token: string, // JWT from Canva webhook
): Promise<{ valid: boolean; payload?: any }> {
  try {
    const { payload } = await jwtVerify(token, JWKS, {
      issuer: 'canva',
    });
    return { valid: true, payload };
  } catch {
    return { valid: false };
  }
}

// Express middleware
app.post('/webhooks/canva', express.text({ type: '*/*' }), async (req, res) => {
  const result = await verifyCanvaWebhook(req.body);
  if (!result.valid) return res.status(401).send('Invalid signature');

  await handleWebhookEvent(result.payload);
  res.status(200).send('OK'); // Must return 200 to acknowledge
});
```

## Security Checklist

- [ ] Client secret stored in environment variables / secret manager
- [ ] `.env` files in `.gitignore`
- [ ] Token exchange and refresh happen server-side only
- [ ] Access tokens encrypted at rest in database
- [ ] Refresh tokens treated as single-use (always store latest)
- [ ] Scopes follow least-privilege principle
- [ ] Webhook signatures verified with JWK
- [ ] Token revocation implemented for user disconnect
- [ ] No tokens in log output
- [ ] HTTPS enforced for all callback URLs

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Token in logs | Log audit | Redact before logging |
| Excessive scopes | Scope audit | Reduce to minimum needed |
| Stale refresh token | Auth failures | Re-authorize user |
| Unsigned webhook | Missing verification | Always verify JWK signature |
| Client secret in frontend | Code review | Server-side only |

## Resources

- [Canva Authentication](https://www.canva.dev/docs/connect/authentication/)
- [Canva Scopes](https://www.canva.dev/docs/connect/appendix/scopes/)
- [Webhook Keys API](https://www.canva.dev/docs/connect/api-reference/webhooks/keys/)

## Next Steps

For production deployment, see `canva-prod-checklist`.
