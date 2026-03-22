---
name: apollo-security-basics
description: |
  Apply Apollo security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Apollo security configuration.
  Trigger with phrases like "apollo security", "apollo secrets",
  "secure apollo", "apollo API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apollo]
---

# Apollo Security Basics

## Overview
Security best practices for Apollo API keys, tokens, and access control.

## Prerequisites
- Apollo SDK installed
- Understanding of environment variables
- Access to Apollo dashboard

## Instructions

### Step 1: Configure Environment Variables
```bash
# .env (NEVER commit to git)
APOLLO_API_KEY=sk_live_***
APOLLO_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation
```bash
# 1. Generate new key in Apollo dashboard
# 2. Update environment variable
export APOLLO_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${APOLLO_API_KEY}" \
  https://api.apollo.com/health

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
  reader: new ApolloClient({
    apiKey: process.env.APOLLO_READ_KEY,
  }),
  writer: new ApolloClient({
    apiKey: process.env.APOLLO_WRITE_KEY,
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

  // Log to Apollo analytics
  await apolloClient.track('audit', log);

  // Also log locally for compliance
  console.log('[AUDIT]', JSON.stringify(log));
}

// Usage
await auditLog({
  action: 'apollo.api.call',
  userId: currentUser.id,
  resource: '/v1/resource',
  result: 'success',
});
```

## Resources
- [Apollo Security Guide](https://docs.apollo.com/security)
- [Apollo API Scopes](https://docs.apollo.com/scopes)

## Next Steps
For production deployment, see `apollo-prod-checklist`.