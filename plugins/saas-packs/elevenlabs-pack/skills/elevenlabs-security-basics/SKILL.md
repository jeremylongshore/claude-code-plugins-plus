---
name: elevenlabs-security-basics
description: |
  Apply ElevenLabs security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing ElevenLabs security configuration.
  Trigger with phrases like "elevenlabs security", "elevenlabs secrets",
  "secure elevenlabs", "elevenlabs API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, elevenlabs]
---

# ElevenLabs Security Basics

## Overview
Security best practices for ElevenLabs API keys, tokens, and access control.

## Prerequisites
- ElevenLabs SDK installed
- Understanding of environment variables
- Access to ElevenLabs dashboard

## Instructions

### Step 1: Configure Environment Variables
```bash
# .env (NEVER commit to git)
ELEVENLABS_API_KEY=sk_live_***
ELEVENLABS_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

### Step 2: Implement Secret Rotation
```bash
# 1. Generate new key in ElevenLabs dashboard
# 2. Update environment variable
export ELEVENLABS_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${ELEVENLABS_API_KEY}" \
  https://api.elevenlabs.com/health

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
  reader: new ElevenLabsClient({
    apiKey: process.env.ELEVENLABS_READ_KEY,
  }),
  writer: new ElevenLabsClient({
    apiKey: process.env.ELEVENLABS_WRITE_KEY,
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

  // Log to ElevenLabs analytics
  await elevenlabsClient.track('audit', log);

  // Also log locally for compliance
  console.log('[AUDIT]', JSON.stringify(log));
}

// Usage
await auditLog({
  action: 'elevenlabs.api.call',
  userId: currentUser.id,
  resource: '/v1/resource',
  result: 'success',
});
```

## Resources
- [ElevenLabs Security Guide](https://docs.elevenlabs.com/security)
- [ElevenLabs API Scopes](https://docs.elevenlabs.com/scopes)

## Next Steps
For production deployment, see `elevenlabs-prod-checklist`.