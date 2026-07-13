# Security Implementation Patterns

## Environment Variable Setup

```bash
# .env (NEVER commit to git)
RETELLAI_API_KEY=sk_live_***
RETELLAI_SECRET=***

# .gitignore
.env
.env.local
.env.*.local
```

## Secret Rotation

```bash
set -euo pipefail
# 1. Generate new key in Retell AI dashboard
# 2. Update environment variable
export RETELLAI_API_KEY="new_key_here"

# 3. Verify new key works
curl -H "Authorization: Bearer ${RETELLAI_API_KEY}" \
  https://api.retellai.com/health

# 4. Revoke old key in dashboard
```

## Service Account Pattern

```typescript
const clients = {
  reader: new RetellAIClient({
    apiKey: process.env.RETELLAI_READ_KEY,
  }),
  writer: new RetellAIClient({
    apiKey: process.env.RETELLAI_WRITE_KEY,
  }),
};
```

## Webhook Signature Verification

```typescript
import crypto from 'crypto';

function verifyWebhookSignature(
  payload: string, signature: string, secret: string
): boolean {
  const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}
```

## Audit Logging

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

  // Log to Retell AI analytics
  await retellaiClient.track('audit', log);

  // Also log locally for compliance
  console.log('[AUDIT]', JSON.stringify(log));
}

// Usage
await auditLog({
  action: 'retellai.api.call',
  userId: currentUser.id,
  resource: '/v1/resource',
  result: 'success',
});
```

## Security Checklist

- [ ] API keys in environment variables
- [ ] `.env` files in `.gitignore`
- [ ] Different keys for dev/staging/prod
- [ ] Minimal scopes per environment
- [ ] Webhook signatures validated
- [ ] Audit logging enabled
