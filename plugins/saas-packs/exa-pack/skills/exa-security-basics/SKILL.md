---
name: exa-security-basics
description: |
  Apply Exa security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Exa security configuration.
  Trigger with phrases like "exa security", "exa secrets",
  "secure exa", "exa API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Exa Security Basics

## Overview
Security best practices for Exa API keys, tokens, and access control.

## Prerequisites
- Exa SDK installed
- Understanding of environment variables
- Access to Exa dashboard

## Instructions

### Step 1: Configure Environment Variables
```bash
# .env (NEVER commit to git)
EXA_API_KEY=sk_live_***
EXA_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation
```bash
set -euo pipefail
# 1. Generate new key in Exa dashboard
# 2. Update environment variable
export EXA_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${EXA_API_KEY}" \
  https://api.exa.com/health

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
  reader: new ExaClient({
    apiKey: process.env.EXA_READ_KEY,
  }),
  writer: new ExaClient({
    apiKey: process.env.EXA_WRITE_KEY,
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

  // Log to Exa analytics
  await exaClient.track('audit', log);

  // Also log locally for compliance
  console.log('[AUDIT]', JSON.stringify(log));
}

// Usage
await auditLog({
  action: 'exa.api.call',
  userId: currentUser.id,
  resource: '/v1/resource',
  result: 'success',
});
```

## Resources
- [Exa Security Guide](https://docs.exa.com/security)
- [Exa API Scopes](https://docs.exa.com/scopes)

## Next Steps
For production deployment, see `exa-prod-checklist`.