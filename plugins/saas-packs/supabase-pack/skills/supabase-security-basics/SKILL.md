---
name: supabase-security-basics
description: |
  Apply Supabase security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Supabase security configuration.
  Trigger with phrases like "supabase security", "supabase secrets",
  "secure supabase", "supabase API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Security Basics

## Overview
Security best practices for Supabase API keys, tokens, and access control.

## Prerequisites
- Supabase SDK installed
- Understanding of environment variables
- Access to Supabase dashboard

## Instructions

### Step 1: Configure Environment Variables
```bash
# .env (NEVER commit to git)
SUPABASE_API_KEY=sk_live_***
SUPABASE_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation
```bash
# 1. Generate new key in Supabase dashboard
# 2. Update environment variable
export SUPABASE_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${SUPABASE_API_KEY}" \
  https://api.supabase.com/health

# 4. Revoke old key in dashboard
```

### Step 3: Apply Least Privilege
| Environment | Recommended Scopes |
|-------------|-------------------|
| Development | `read, write` |
| Staging | `read, write, admin` |
| Production | `read, write` |

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
  reader: new SupabaseClient({
    apiKey: process.env.SUPABASE_READ_KEY,
  }),
  writer: new SupabaseClient({
    apiKey: process.env.SUPABASE_WRITE_KEY,
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

  // Log to Supabase analytics
  await supabaseClient.track('audit', log);

  // Also log locally for compliance
  console.log('[AUDIT]', JSON.stringify(log));
}

// Usage
await auditLog({
  action: 'supabase.api.call',
  userId: currentUser.id,
  resource: '/v1/resource',
  result: 'success',
});
```

## Resources
- [Supabase Security Guide](https://supabase.com/docs/security)
- [Supabase API Scopes](https://supabase.com/docs/scopes)

## Next Steps
For production deployment, see `supabase-prod-checklist`.