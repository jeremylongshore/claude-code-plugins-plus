---
name: linktree-security-basics
description: |
  Security Basics for Linktree.
  Trigger: "linktree security basics".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Security Basics

## Overview

Linktree integrations handle user-generated content (link titles, URLs, bios) and analytics data that is PII-adjacent — click counts, geographic breakdowns, and referrer URLs can fingerprint individual visitors. Bearer token authentication means a leaked key grants full account access including link creation, profile modification, and analytics export. Webhook payloads carry real-time event data signed with HMAC-SHA256, and failing to verify signatures opens your endpoint to spoofed events and data poisoning.

## Prerequisites

- Secrets manager (AWS SSM, GCP Secret Manager, or Vault) for all Linktree credentials
- HTTPS enforced on all webhook receiver endpoints
- `.env` files in `.gitignore` — never committed to version control
- Logging infrastructure that supports field-level redaction

## API Key Management

```typescript
// Load Linktree bearer token from environment — never hardcode
const LINKTREE_TOKEN = process.env.LINKTREE_API_KEY;

function validateLinktreeConfig(): void {
  if (!LINKTREE_TOKEN || LINKTREE_TOKEN.startsWith('lt_test_')) {
    throw new Error('Missing or test-only LINKTREE_API_KEY — set a production token');
  }
}

function linktreeHeaders(): Record<string, string> {
  return {
    Authorization: `Bearer ${LINKTREE_TOKEN}`,
    'Content-Type': 'application/json',
  };
}
// Call validateLinktreeConfig() at startup, before accepting requests
```

## Webhook Signature Verification

```typescript
import crypto from 'node:crypto';

const WEBHOOK_SECRET = process.env.LINKTREE_WEBHOOK_SECRET!;

function verifyLinktreeWebhook(payload: string, signature: string): boolean {
  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(payload, 'utf8')
    .digest('hex');
  // Timing-safe comparison prevents timing attacks
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

// Express middleware
app.post('/webhooks/linktree', (req, res) => {
  const sig = req.headers['x-linktree-signature'] as string;
  if (!sig || !verifyLinktreeWebhook(JSON.stringify(req.body), sig)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  // Process verified event
});
```

## Input Validation

```typescript
import { URL } from 'node:url';

function sanitizeLinkTitle(title: string): string {
  // Strip HTML/script tags from user-generated link titles
  return title.replace(/<[^>]*>/g, '').trim().slice(0, 150);
}

function validateLinkUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    // Only allow http/https — block javascript:, data:, file: schemes
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}
```

## Data Protection

```typescript
function redactAnalytics(data: Record<string, unknown>): Record<string, unknown> {
  const sensitive = ['ip_address', 'user_agent', 'referrer_url', 'geo_city'];
  const redacted = { ...data };
  for (const field of sensitive) {
    if (redacted[field]) redacted[field] = '[REDACTED]';
  }
  return redacted;
}
// Use redactAnalytics() before writing any analytics payload to logs
```

## Access Control

```typescript
// Linktree tokens are account-scoped — enforce least privilege
function assertReadOnlyScope(operation: string): void {
  const writeOps = ['create_link', 'update_link', 'delete_link', 'update_profile'];
  if (writeOps.includes(operation) && process.env.LINKTREE_READ_ONLY === 'true') {
    throw new Error(`Write operation "${operation}" blocked in read-only mode`);
  }
}
```

## Security Checklist

- [ ] Bearer token stored in secrets manager, not `.env` on disk
- [ ] Webhook `x-linktree-signature` verified with HMAC-SHA256
- [ ] Link URLs validated against allowlisted protocols
- [ ] Link titles sanitized for HTML/XSS before storage or display
- [ ] Analytics data redacted before logging (IP, user-agent, geo)
- [ ] Read-only mode enforced for non-admin integrations
- [ ] Token rotation scheduled quarterly
- [ ] Rate limiting applied to webhook receiver endpoint

## Error Handling

| Vulnerability | Risk | Mitigation |
|---|---|---|
| Bearer token in logs | Full account takeover | Redact `Authorization` header in all log output |
| Unverified webhooks | Spoofed link-click events | Reject any request missing valid `x-linktree-signature` |
| Malicious link URLs | Open redirect / phishing | Validate URL scheme and domain before storing |
| XSS in link titles | Script injection via UGC | Strip HTML tags and enforce max length |
| Analytics PII leakage | GDPR/CCPA violation | Redact IP, geo, and referrer before persistence |

## Resources

- [Linktree Developer Docs](https://linktr.ee/marketplace/developer)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps

See `linktree-prod-checklist`.
