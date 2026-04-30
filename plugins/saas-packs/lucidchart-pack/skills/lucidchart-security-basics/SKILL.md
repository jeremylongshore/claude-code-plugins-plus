---
name: lucidchart-security-basics
description: 'Security Basics for Lucidchart.

  Trigger: "lucidchart security basics".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lucidchart
- diagramming
compatibility: Designed for Claude Code
---
# Lucidchart Security Basics

## Overview

Lucidchart documents often contain sensitive business diagrams — org charts, network topologies, database schemas, and architecture plans that reveal internal infrastructure. The API uses OAuth2 client credentials, meaning a compromised client secret grants access to every document the integration can reach. Collaboration sharing with granular permission levels (view, edit, owner) must be enforced server-side. API versioning via the `Lucid-Api-Version` header requires pinning to avoid unexpected schema changes that break validation logic.

## Prerequisites

- OAuth2 client ID and secret stored in a secrets manager (not environment files)
- HTTPS enforced on all redirect URIs and webhook endpoints
- `Lucid-Api-Version` header pinned to a tested version in all requests
- `.env` files in `.gitignore` — never committed to version control

## API Key Management

```typescript
// OAuth2 client credentials — load from secrets manager at startup
const LUCID_CLIENT_ID = process.env.LUCID_CLIENT_ID;
const LUCID_CLIENT_SECRET = process.env.LUCID_CLIENT_SECRET;

function validateLucidConfig(): void {
  if (!LUCID_CLIENT_ID || !LUCID_CLIENT_SECRET) {
    throw new Error('Missing LUCID_CLIENT_ID or LUCID_CLIENT_SECRET');
  }
}

async function getLucidAccessToken(): Promise<string> {
  const resp = await fetch('https://api.lucid.co/oauth2/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: LUCID_CLIENT_ID!,
      client_secret: LUCID_CLIENT_SECRET!,
    }),
  });
  if (!resp.ok) throw new Error(`OAuth2 token request failed: ${resp.status}`);
  const { access_token } = await resp.json();
  return access_token;
  // Cache token until expiry — never log it
}
```

## Webhook Signature Verification

```typescript
import crypto from 'node:crypto';

const LUCID_WEBHOOK_SECRET = process.env.LUCID_WEBHOOK_SECRET!;

function verifyLucidWebhook(payload: string, signature: string): boolean {
  const expected = crypto
    .createHmac('sha256', LUCID_WEBHOOK_SECRET)
    .update(payload, 'utf8')
    .digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

app.post('/webhooks/lucidchart', (req, res) => {
  const sig = req.headers['x-lucid-signature'] as string;
  if (!sig || !verifyLucidWebhook(JSON.stringify(req.body), sig)) {
    return res.status(401).json({ error: 'Invalid webhook signature' });
  }
  // Process verified document change event
});
```

## Input Validation

```typescript
// Validate document IDs and enforce API version pinning
const LUCID_API_VERSION = '1';

function validateDocumentId(docId: string): boolean {
  // Lucid document IDs are alphanumeric UUIDs
  return /^[a-f0-9-]{36}$/.test(docId);
}

function lucidApiHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    'Lucid-Api-Version': LUCID_API_VERSION,
    'Content-Type': 'application/json',
  };
}
```

## Data Protection

```typescript
function redactDiagramMetadata(doc: Record<string, unknown>): Record<string, unknown> {
  const sensitive = ['creator_email', 'collaborator_emails', 'share_link', 'embed_url'];
  const redacted = { ...doc };
  for (const field of sensitive) {
    if (redacted[field]) redacted[field] = '[REDACTED]';
  }
  return redacted;
}
// Always redact before logging — diagrams may contain org charts and network layouts
```

## Access Control

```typescript
type LucidPermission = 'view' | 'edit' | 'owner';

function assertDocumentPermission(
  userRole: LucidPermission,
  requiredRole: LucidPermission
): void {
  const hierarchy: LucidPermission[] = ['view', 'edit', 'owner'];
  if (hierarchy.indexOf(userRole) < hierarchy.indexOf(requiredRole)) {
    throw new Error(`Insufficient permission: need "${requiredRole}", have "${userRole}"`);
  }
}
// Enforce server-side — never rely on Lucidchart UI permissions alone
```

## Security Checklist

- [ ] OAuth2 client secret in secrets manager, rotated on schedule
- [ ] Access tokens cached in memory only, never persisted to disk or logs
- [ ] `Lucid-Api-Version` header pinned to a tested version
- [ ] Webhook signatures verified with HMAC-SHA256
- [ ] Document sharing permissions enforced server-side
- [ ] Collaborator emails redacted before logging
- [ ] Exported diagrams (PNG/PDF) treated as confidential artifacts
- [ ] OAuth2 scopes requested at minimum privilege

## Error Handling

| Vulnerability | Risk | Mitigation |
|---|---|---|
| Client secret in logs | Full API access compromise | Never log OAuth2 credentials; redact in error handlers |
| Unverified webhooks | Spoofed document change events | Reject requests without valid `x-lucid-signature` |
| Unpinned API version | Breaking schema changes bypass validation | Always send `Lucid-Api-Version` header |
| Over-permissioned sharing | Unauthorized diagram access | Enforce view/edit/owner hierarchy server-side |
| Diagram data in logs | Leaked org charts and network topology | Redact creator, collaborator, and share URLs |

## Resources

- [Lucidchart Developer Reference](https://developer.lucid.co/reference/overview)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps

See `lucidchart-prod-checklist`.
