---
name: supabase-security-basics
description: |
  Apply Supabase security best practices for secrets and access control.
  Use when securing API keys or implementing least privilege access.
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
- supabase-install-auth completed
- Understanding of environment variables
- Access to Supabase dashboard

## Instructions

### Step 1: Secure Environment Variables
```bash
# .env (NEVER commit to git)
SUPABASE_API_KEY=sk_live_***
SUPABASE_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Key Rotation
```bash
# 1. Generate new key in Supabase dashboard
# 2. Update environment variable
export SUPABASE_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer $SUPABASE_API_KEY" \
  https://api.supabase.com/health

# 4. Revoke old key in dashboard
```

### Step 3: Apply Least Privilege

| Environment | Recommended Scopes |
|-------------|-------------------|
| Development | `read, write` |
| Staging | `read, write, admin` |
| Production | `read, write` |

### Step 4: Implement Audit Logging
```typescript
function logOperation(operation: string, params: Record<string, any>) {
  const sanitized = { ...params };
  delete sanitized.apiKey;
  delete sanitized.token;

  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    service: 'supabase',
    operation,
    params: sanitized,
  }));
}
```

## Output
- API keys stored securely in environment variables
- .env files excluded from version control
- Separate keys for each environment
- Audit trail of all API operations

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Key exposed in git | Committed .env file | Rotate key immediately, add to .gitignore |
| Unauthorized (401) | Invalid or revoked key | Check key in dashboard, regenerate if needed |
| Forbidden (403) | Insufficient scope | Update API key scopes in dashboard |
| Audit log gaps | Logging not implemented | Add audit middleware to all API calls |

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
  payload: string,
  signature: string,
  secret: string
): boolean {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}
```

### Security Checklist
- [ ] API keys stored in environment variables
- [ ] `.env` files in `.gitignore`
- [ ] Different keys for dev/staging/prod
- [ ] Minimal scopes per environment
- [ ] Audit logging enabled
- [ ] Regular key rotation schedule
- [ ] Webhook signatures validated

## Resources
- [Supabase Security Guide](https://supabase.com/docs/security)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [Secret Management Best Practices](https://supabase.com/docs/secrets)

## Next Steps
For production deployment, see `supabase-prod-checklist`.