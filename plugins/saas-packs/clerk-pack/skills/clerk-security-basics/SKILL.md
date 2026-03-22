---
name: clerk-security-basics
description: |
  Apply Clerk security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Clerk security configuration.
  Trigger with phrases like "clerk security", "clerk secrets",
  "secure clerk", "clerk API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clerk]
---

# Clerk Security Basics

## Overview
Security best practices for Clerk API keys, tokens, and access control.

## Prerequisites
- Clerk SDK installed
- Understanding of environment variables
- Access to Clerk dashboard

## Instructions

### Step 1: Configure Environment Variables
```bash
# .env (NEVER commit to git)
CLERK_API_KEY=sk_live_***
CLERK_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation
```bash
# 1. Generate new key in Clerk dashboard
# 2. Update environment variable
export CLERK_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${CLERK_API_KEY}" \
  https://api.clerk.com/health

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
  reader: new ClerkClient({
    apiKey: process.env.CLERK_READ_KEY,
  }),
  writer: new ClerkClient({
    apiKey: process.env.CLERK_WRITE_KEY,
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

  // Log to Clerk analytics
  await clerkClient.track('audit', log);

  // Also log locally for compliance
  console.log('[AUDIT]', JSON.stringify(log));
}

// Usage
await auditLog({
  action: 'clerk.api.call',
  userId: currentUser.id,
  resource: '/v1/resource',
  result: 'success',
});
```

## Resources
- [Clerk Security Guide](https://docs.clerk.com/security)
- [Clerk API Scopes](https://docs.clerk.com/scopes)

## Next Steps
For production deployment, see `clerk-prod-checklist`.