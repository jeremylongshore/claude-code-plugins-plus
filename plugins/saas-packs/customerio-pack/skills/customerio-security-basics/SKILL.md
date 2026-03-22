---
name: customerio-security-basics
description: |
  Apply Customer.io security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Customer.io security configuration.
  Trigger with phrases like "customerio security", "customerio secrets",
  "secure customerio", "customerio API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, customerio]
---

# Customer.io Security Basics

## Overview
Security best practices for Customer.io API keys, tokens, and access control.

## Prerequisites
- Customer.io SDK installed
- Understanding of environment variables
- Access to Customer.io dashboard

## Instructions

### Step 1: Configure Environment Variables
```bash
# .env (NEVER commit to git)
CUSTOMERIO_API_KEY=sk_live_***
CUSTOMERIO_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation
```bash
# 1. Generate new key in Customer.io dashboard
# 2. Update environment variable
export CUSTOMERIO_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${CUSTOMERIO_API_KEY}" \
  https://api.customerio.com/health

# 4. Revoke old key in dashboard
```

### Step 3: Apply Least Privilege
| Environment | Recommended Scopes |
|-------------|-------------------|
| Development | `read:*` |
| Staging | `read:*, write:limited` |
| Production | `Only required scopes` |

## Output
- Secure API key storage
- Environment-specific access controls
- Audit logging enabled

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Exposed API key | Git scanning | Rotate immediately |
| Excessive scopes | Audit logs | Reduce permissions |
| Missing rotation | Key age check | Schedule rotation |

## Examples

### Service Account Pattern
```typescript
const clients = {
  reader: new Customer.ioClient({
    apiKey: process.env.CUSTOMERIO_READ_KEY,
  }),
  writer: new Customer.ioClient({
    apiKey: process.env.CUSTOMERIO_WRITE_KEY,
  }),
};
```

### Webhook Signature Verification
```typescript
import crypto from 'crypto';

function verifyWebhookSignature(
  payload: string, signature: string, secret: string
): boolean {
  const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}
```

### Security Checklist
- [ ] API keys in environment variables
- [ ] `.env` files in `.gitignore`
- [ ] Different keys for dev/staging/prod
- [ ] Minimal scopes per environment
- [ ] Webhook signatures validated
- [ ] Audit logging enabled

### Audit Logging
```typescript
interface AuditEntry {
  timestamp: Date;
  action: string;
  userId: string;
  resource: string;
  result: 'success' | 'failure';
  metadata?: Record<string, any>;
}

async function auditLog(entry: Omit<AuditEntry, 'timestamp'>): Promise<void> {
  const log: AuditEntry = { ...entry, timestamp: new Date() };

  // Log to Customer.io analytics
  await customerioClient.track('audit', log);

  // Also log locally for compliance
  console.log('[AUDIT]', JSON.stringify(log));
}

// Usage
await auditLog({
  action: 'customerio.api.call',
  userId: currentUser.id,
  resource: '/v1/resource',
  result: 'success',
});
```

## Resources
- [Customer.io Security Guide](https://docs.customerio.com/security)
- [Customer.io API Scopes](https://docs.customerio.com/scopes)

## Next Steps
For production deployment, see `customerio-prod-checklist`.