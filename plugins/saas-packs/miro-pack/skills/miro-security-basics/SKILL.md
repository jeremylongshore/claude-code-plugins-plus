---
name: miro-security-basics
description: |
  Apply Miro REST API v2 security best practices — OAuth scope minimization,
  token storage, webhook signature validation, and secret rotation.
  Trigger with phrases like "miro security", "miro secrets",
  "secure miro", "miro token security", "miro webhook signature".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, security, oauth]
compatible-with: claude-code
---

# Miro Security Basics

## Overview

Security best practices for Miro OAuth 2.0 tokens, webhook signatures, and access control across the REST API v2.

## Prerequisites

- Miro app created at https://developers.miro.com
- Understanding of OAuth 2.0 concepts
- Secret management solution for production

## OAuth Token Security

### Never Store Tokens in Code

```bash
# .env (NEVER commit to git)
MIRO_CLIENT_ID=3458764500000001
MIRO_CLIENT_SECRET=your_client_secret_here
MIRO_ACCESS_TOKEN=eyJ...
MIRO_REFRESH_TOKEN=eyJ...

# .gitignore — MUST include these
.env
.env.local
.env.*.local
*.pem
```

### Scope Minimization

Request only the scopes your app actually needs. Fewer scopes = smaller blast radius if a token is compromised.

| Use Case | Minimum Scopes |
|----------|---------------|
| Read-only dashboard | `boards:read` |
| Board automation | `boards:read`, `boards:write` |
| Team management | `boards:read`, `team:read`, `team:write` |
| Enterprise admin | `boards:read`, `organizations:read`, `auditlogs:read` |
| Full integration | `boards:read`, `boards:write`, `identity:read` |

### Token Lifecycle Management

```typescript
// src/miro/token-manager.ts

interface TokenInfo {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;  // Unix timestamp in ms
  scopes: string[];
}

class MiroTokenManager {
  constructor(
    private storage: TokenStorage,   // DB, Redis, or Vault
    private clientId: string,
    private clientSecret: string,
  ) {}

  async getValidToken(userId: string): Promise<string> {
    const info = await this.storage.get(userId);
    if (!info) throw new Error('User not authorized');

    // Refresh 5 minutes before expiry
    if (Date.now() > info.expiresAt - 300_000) {
      return this.refreshToken(userId, info.refreshToken);
    }

    return info.accessToken;
  }

  private async refreshToken(userId: string, refreshToken: string): Promise<string> {
    const response = await fetch('https://api.miro.com/v1/oauth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        client_id: this.clientId,
        client_secret: this.clientSecret,
        refresh_token: refreshToken,
      }),
    });

    if (!response.ok) {
      // Refresh token revoked or expired — user must re-authorize
      await this.storage.delete(userId);
      throw new Error('Miro refresh token invalid. User must re-authorize.');
    }

    const data = await response.json();
    await this.storage.set(userId, {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      expiresAt: Date.now() + data.expires_in * 1000,
      scopes: data.scope.split(' '),
    });

    return data.access_token;
  }
}
```

## Webhook Signature Validation

Miro signs webhook payloads so you can verify they originate from Miro's servers.

```typescript
import crypto from 'crypto';

function verifyMiroWebhookSignature(
  rawBody: Buffer | string,
  signature: string,
  secret: string,
): boolean {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');

  // Timing-safe comparison to prevent timing attacks
  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expected, 'hex'),
    );
  } catch {
    return false; // Different lengths = not equal
  }
}

// Express middleware
app.post('/webhooks/miro',
  express.raw({ type: 'application/json' }),
  (req, res) => {
    const signature = req.headers['x-miro-signature'] as string;
    if (!signature || !verifyMiroWebhookSignature(req.body, signature, process.env.MIRO_WEBHOOK_SECRET!)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());
    // Process verified event...
    res.status(200).json({ received: true });
  }
);
```

## Client Secret Rotation

```bash
# Step 1: Generate new secret in Miro app settings
# https://developers.miro.com > Your apps > Select app > App Credentials

# Step 2: Update secret in your environment
# For production (example with GCP Secret Manager):
gcloud secrets versions add miro-client-secret \
  --data-file=<(echo -n "new_secret_value")

# Step 3: Verify new secret works
curl -X POST https://api.miro.com/v1/oauth/token \
  -d "grant_type=refresh_token" \
  -d "client_id=$MIRO_CLIENT_ID" \
  -d "client_secret=NEW_SECRET" \
  -d "refresh_token=$MIRO_REFRESH_TOKEN"

# Step 4: Revoke old secret in Miro app settings
```

## Request Signing for Audit Trails

```typescript
interface MiroAuditEntry {
  timestamp: string;
  userId: string;
  endpoint: string;
  method: string;
  boardId?: string;
  requestId?: string;  // From X-Request-Id response header
  status: number;
}

async function auditedMiroFetch(
  userId: string,
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const response = await fetch(`https://api.miro.com${path}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${await tokenManager.getValidToken(userId)}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  const audit: MiroAuditEntry = {
    timestamp: new Date().toISOString(),
    userId,
    endpoint: path,
    method: options.method ?? 'GET',
    boardId: path.match(/boards\/([^/]+)/)?.[1],
    requestId: response.headers.get('X-Request-Id') ?? undefined,
    status: response.status,
  };

  // Log audit trail (never log token or request body)
  console.log('[MIRO_AUDIT]', JSON.stringify(audit));

  return response;
}
```

## Security Checklist

- [ ] Access tokens stored in environment variables or secret manager, never in code
- [ ] `.env` files in `.gitignore`
- [ ] OAuth scopes minimized per environment
- [ ] Webhook signatures validated with timing-safe comparison
- [ ] Token refresh handled before expiry (5-minute buffer)
- [ ] Failed refresh triggers re-authorization flow
- [ ] Client secret rotation procedure documented and tested
- [ ] Audit logging captures endpoint, method, user, and status (never tokens)
- [ ] `X-Request-Id` captured for support ticket correlation

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Token in logs | Log audit | Redact `Authorization` headers in logging middleware |
| Token in git | Pre-commit hook / secret scanning | Rotate immediately, revoke old token |
| Webhook forgery | Signature validation fails | Return 401, alert security team |
| Excessive scopes | Scope audit | Reduce to minimum needed per endpoint |

## Resources

- [Miro OAuth 2.0](https://developers.miro.com/docs/getting-started-with-oauth)
- [Permission Scopes](https://developers.miro.com/reference/scopes)
- [Troubleshoot OAuth 2.0](https://developers.miro.com/docs/troubleshooting-oauth20)

## Next Steps

For production deployment, see `miro-prod-checklist`.
