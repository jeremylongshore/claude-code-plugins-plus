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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
