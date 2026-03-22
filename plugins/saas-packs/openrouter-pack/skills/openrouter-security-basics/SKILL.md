---
name: openrouter-security-basics
description: |
  Apply OpenRouter security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing OpenRouter security configuration.
  Trigger with phrases like "openrouter security", "openrouter secrets",
  "secure openrouter", "openrouter API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openrouter]
---

# OpenRouter Security Basics

## Overview
Security best practices for OpenRouter API keys, tokens, and access control.

## Prerequisites
- OpenRouter SDK installed
- Understanding of environment variables
- Access to OpenRouter dashboard

## Instructions

### Step 1: Configure Environment Variables
```bash
# .env (NEVER commit to git)
OPENROUTER_API_KEY=sk_live_***
OPENROUTER_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation
```bash
# 1. Generate new key in OpenRouter dashboard
# 2. Update environment variable
export OPENROUTER_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${OPENROUTER_API_KEY}" \
  https://api.openrouter.com/health

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
  reader: new OpenRouterClient({
    apiKey: process.env.OPENROUTER_READ_KEY,
  }),
  writer: new OpenRouterClient({
    apiKey: process.env.OPENROUTER_WRITE_KEY,
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

  // Log to OpenRouter analytics
  await openrouterClient.track('audit', log);

  // Also log locally for compliance
  console.log('[AUDIT]', JSON.stringify(log));
}

// Usage
await auditLog({
  action: 'openrouter.api.call',
  userId: currentUser.id,
  resource: '/v1/resource',
  result: 'success',
});
```

## Resources
- [OpenRouter Security Guide](https://docs.openrouter.com/security)
- [OpenRouter API Scopes](https://docs.openrouter.com/scopes)

## Next Steps
For production deployment, see `openrouter-prod-checklist`.