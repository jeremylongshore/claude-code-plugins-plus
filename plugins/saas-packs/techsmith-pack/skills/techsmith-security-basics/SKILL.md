---
name: techsmith-security-basics
description: |
  Apply TechSmith security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing TechSmith security configuration.
  Trigger with phrases like "techsmith security", "techsmith secrets",
  "secure techsmith", "techsmith API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, techsmith]
---

# TechSmith Security Basics

## Overview
Security best practices for TechSmith API keys, tokens, and access control.

## Prerequisites
- TechSmith SDK installed
- Understanding of environment variables
- Access to TechSmith dashboard

## Instructions

### Step 1: Configure Environment Variables
```bash
# .env (NEVER commit to git)
TECHSMITH_API_KEY=sk_live_***
TECHSMITH_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation
```bash
# 1. Generate new key in TechSmith dashboard
# 2. Update environment variable
export TECHSMITH_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${TECHSMITH_API_KEY}" \
  https://api.techsmith.com/health

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
  reader: new TechSmithClient({
    apiKey: process.env.TECHSMITH_READ_KEY,
  }),
  writer: new TechSmithClient({
    apiKey: process.env.TECHSMITH_WRITE_KEY,
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

  // Log to TechSmith analytics
  await techsmithClient.track('audit', log);

  // Also log locally for compliance
  console.log('[AUDIT]', JSON.stringify(log));
}

// Usage
await auditLog({
  action: 'techsmith.api.call',
  userId: currentUser.id,
  resource: '/v1/resource',
  result: 'success',
});
```

## Resources
- [TechSmith Security Guide](https://docs.techsmith.com/security)
- [TechSmith API Scopes](https://docs.techsmith.com/scopes)

## Next Steps
For production deployment, see `techsmith-prod-checklist`.