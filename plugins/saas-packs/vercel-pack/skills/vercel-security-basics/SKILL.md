---
name: vercel-security-basics
description: |
  Apply Vercel security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Vercel security configuration.
  Trigger with phrases like "vercel security", "vercel secrets",
  "secure vercel", "vercel API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Security Basics

## Overview
Security best practices for Vercel API keys, tokens, and access control.

## Prerequisites
- Vercel SDK installed
- Understanding of environment variables
- Access to Vercel dashboard

## Instructions

### Step 1: Configure Environment Variables
```bash
# .env (NEVER commit to git)
VERCEL_API_KEY=sk_live_***
VERCEL_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation
```bash
# 1. Generate new key in Vercel dashboard
# 2. Update environment variable
export VERCEL_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${VERCEL_API_KEY}" \
  https://api.vercel.com/health

# 4. Revoke old key in dashboard
```

### Step 3: Apply Least Privilege
| Environment | Recommended Scopes |
|-------------|-------------------|
| Development | `read, deploy` |
| Staging | `read, write, deploy` |
| Production | `read, write, deploy, domains` |

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
  reader: new VercelClient({
    apiKey: process.env.VERCEL_READ_KEY,
  }),
  writer: new VercelClient({
    apiKey: process.env.VERCEL_WRITE_KEY,
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

## Resources
- [Vercel Security Guide](https://vercel.com/docs/security)
- [Vercel API Scopes](https://vercel.com/docs/scopes)

## Next Steps
For production deployment, see `vercel-prod-checklist`.