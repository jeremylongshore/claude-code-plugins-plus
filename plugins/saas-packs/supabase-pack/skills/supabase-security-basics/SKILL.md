---
name: supabase-security-basics
description: |
  Supabase security best practices for secrets and access control.
  Trigger phrases: "supabase security", "supabase secrets",
  "secure supabase", "supabase API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Security Basics

## Overview
Security best practices for Supabase API keys, tokens, and access control.

## Secret Management

### Environment Variables (Required)
```bash
# .env (NEVER commit to git)
SUPABASE_API_KEY=sk_live_***
SUPABASE_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Secret Rotation
```bash
# 1. Generate new key in Supabase dashboard
# 2. Update environment variable
export SUPABASE_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${SUPABASE_API_KEY}" \
  https://api.supabase.com/health

# 4. Revoke old key in dashboard
```

## Least Privilege Principle

### Scope Recommendations
| Environment | Recommended Scopes |
|-------------|-------------------|
| Development | `read, write` |
| Staging | `read, write, admin` |
| Production | `read, write` |

### Service Account Pattern
```typescript
// Use separate API keys per service/environment
const clients = {
  reader: new SupabaseClient({
    apiKey: process.env.SUPABASE_READ_KEY,
  }),
  writer: new SupabaseClient({
    apiKey: process.env.SUPABASE_WRITE_KEY,
  }),
};
```

## Audit Logging

```typescript
// Log all Supabase operations (without secrets)
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

## Security Checklist

- [ ] API keys stored in environment variables
- [ ] `.env` files in `.gitignore`
- [ ] Different keys for dev/staging/prod
- [ ] Minimal scopes per environment
- [ ] Audit logging enabled
- [ ] Regular key rotation schedule
- [ ] IP allowlist configured (if available)
- [ ] Webhook signatures validated

## Common Security Mistakes

### ❌ Don't Do This
```typescript
// NEVER hardcode API keys
const client = new SupabaseClient({
  apiKey: 'sk_live_actual_key_here', // BAD!
});

// NEVER log API keys
console.log('Using key:', process.env.SUPABASE_API_KEY); // BAD!

// NEVER commit .env files
git add .env  // BAD!
```

### ✅ Do This Instead
```typescript
// Use environment variables
const client = new SupabaseClient({
  apiKey: process.env.SUPABASE_API_KEY,
});

// Log presence, not value
console.log('API key configured:', !!process.env.SUPABASE_API_KEY);
```

## Webhook Security

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

## Next Steps
For production deployment, see `supabase-prod-checklist`.