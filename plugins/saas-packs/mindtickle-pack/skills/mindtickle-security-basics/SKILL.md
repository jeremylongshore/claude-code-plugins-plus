---
name: mindtickle-security-basics
description: 'Security Basics for MindTickle.

  Trigger: "mindtickle security basics".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mindtickle
- sales
compatibility: Designed for Claude Code
---
# MindTickle Security Basics

## Overview

MindTickle integrations process employee PII through SCIM provisioning (names, emails, job titles, manager chains) and HR-sensitive data like course completion scores, certification status, and coaching assessments. The API uses bearer token authentication combined with a `Company-Id` header for multi-tenant isolation — omitting or spoofing this header can leak data across tenants. Webhook payloads carrying training completion events must be HMAC-verified to prevent injection of fraudulent compliance records.

## Prerequisites

- Secrets manager (AWS SSM, GCP Secret Manager, or Vault) for API tokens
- HTTPS enforced on all SCIM and webhook endpoints
- `Company-Id` validated against an allowlist of known tenant identifiers
- `.env` files in `.gitignore` — never committed to version control
- Data retention policy for employee training records (GDPR/SOC2)

## API Key Management

```typescript
// MindTickle requires both bearer token and company ID for multi-tenant isolation
const MT_API_TOKEN = process.env.MINDTICKLE_API_KEY;
const MT_COMPANY_ID = process.env.MINDTICKLE_COMPANY_ID;

function validateMindTickleConfig(): void {
  if (!MT_API_TOKEN) throw new Error('Missing MINDTICKLE_API_KEY');
  if (!MT_COMPANY_ID) throw new Error('Missing MINDTICKLE_COMPANY_ID');
}

function mindtickleHeaders(): Record<string, string> {
  return {
    Authorization: `Bearer ${MT_API_TOKEN}`,
    'Company-Id': MT_COMPANY_ID!,
    'Content-Type': 'application/json',
  };
}
// Call validateMindTickleConfig() at startup — both values are required for every request
```

## Webhook Signature Verification

```typescript
import crypto from 'node:crypto';

const MT_WEBHOOK_SECRET = process.env.MINDTICKLE_WEBHOOK_SECRET!;

function verifyMindTickleWebhook(payload: string, signature: string, timestamp: string): boolean {
  // Reject stale webhooks (>5 min) to prevent replay attacks
  const age = Date.now() - parseInt(timestamp, 10) * 1000;
  if (age > 300_000) return false;

  const signedPayload = `${timestamp}.${payload}`;
  const expected = crypto
    .createHmac('sha256', MT_WEBHOOK_SECRET)
    .update(signedPayload, 'utf8')
    .digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

app.post('/webhooks/mindtickle', (req, res) => {
  const sig = req.headers['x-mindtickle-signature'] as string;
  const ts = req.headers['x-mindtickle-timestamp'] as string;
  if (!sig || !ts || !verifyMindTickleWebhook(JSON.stringify(req.body), sig, ts)) {
    return res.status(401).json({ error: 'Invalid signature or stale timestamp' });
  }
  // Process verified training completion event
});
```

## Input Validation

```typescript
// Validate SCIM user payloads — employee PII requires strict schema enforcement
interface ScimUser {
  userName: string;
  name: { givenName: string; familyName: string };
  emails: { value: string; primary: boolean }[];
}

function validateScimUser(user: unknown): user is ScimUser {
  const u = user as Record<string, unknown>;
  if (typeof u.userName !== 'string' || u.userName.length > 254) return false;
  const emails = u.emails as { value: string }[] | undefined;
  if (!emails?.every(e => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.value))) return false;
  return true;
}
```

## Data Protection

```typescript
function redactEmployeeData(record: Record<string, unknown>): Record<string, unknown> {
  const piiFields = ['email', 'userName', 'phone', 'manager_email', 'employee_id'];
  const hrFields = ['score', 'certification_status', 'coaching_notes'];
  const redacted = { ...record };
  for (const field of [...piiFields, ...hrFields]) {
    if (redacted[field]) redacted[field] = '[REDACTED]';
  }
  return redacted;
}
// Redact before logging — course scores and coaching data are HR-confidential
```

## Access Control

```typescript
// Enforce tenant isolation — Company-Id must match the authenticated context
const ALLOWED_COMPANY_IDS = new Set(process.env.MT_ALLOWED_COMPANIES?.split(',') ?? []);

function assertTenantAccess(companyId: string): void {
  if (!ALLOWED_COMPANY_IDS.has(companyId)) {
    throw new Error(`Unauthorized tenant: ${companyId}`);
  }
}

function assertScimWriteAccess(operation: string, hasScimScope: boolean): void {
  const writeOps = ['createUser', 'updateUser', 'deactivateUser'];
  if (writeOps.includes(operation) && !hasScimScope) {
    throw new Error(`SCIM write operation "${operation}" requires scim:write scope`);
  }
}
```

## Security Checklist

- [ ] Bearer token and Company-Id stored in secrets manager
- [ ] Company-Id validated against tenant allowlist on every request
- [ ] Webhook HMAC-SHA256 verified with timestamp replay protection
- [ ] SCIM payloads validated against strict schema before processing
- [ ] Employee PII (email, name, phone) redacted in all logs
- [ ] Course scores and coaching data classified as HR-confidential
- [ ] SCIM write operations gated behind explicit scope checks
- [ ] Data retention policy enforced for training completion records
- [ ] Token rotation scheduled quarterly with zero-downtime swap

## Error Handling

| Vulnerability | Risk | Mitigation |
|---|---|---|
| Missing Company-Id header | Cross-tenant data leakage | Reject requests without validated Company-Id |
| Unverified webhooks | Fraudulent training completion records | HMAC-SHA256 + timestamp validation on every webhook |
| SCIM PII in logs | Employee data breach (GDPR/SOC2) | Redact all PII fields before logging |
| Stale webhook replay | Duplicate or backdated compliance events | Reject webhooks older than 5 minutes |
| Over-permissioned SCIM token | Unauthorized user provisioning | Enforce scim:write scope check for mutations |

## Resources

- [MindTickle Developer Platform](https://www.mindtickle.com/platform/integrations/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps

See `mindtickle-prod-checklist`.
