# Customer.io Security Basics - Implementation Details

## Configuration

### Secure API Key Management

```typescript
// Never hardcode keys; load from environment or secrets manager
function getSecureCioConfig() {
  const siteId = process.env.CIO_SITE_ID;
  const apiKey = process.env.CIO_API_KEY;
  const appApiKey = process.env.CIO_APP_API_KEY;

  if (!siteId || !apiKey) {
    throw new Error('Missing Customer.io credentials in environment');
  }

  return {
    siteId,
    apiKey,      // Track API (write-only, safe for backend)
    appApiKey,   // App API (read+write, never expose to client)
  };
}
```

## Advanced Patterns

### Webhook Signature Verification

```typescript
import crypto from 'crypto';

function verifyCioWebhook(payload: string, signature: string, secret: string): boolean {
  const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

// Express middleware
function cioWebhookAuth(req: Request, res: Response, next: NextFunction) {
  const sig = req.headers['x-cio-signature'] as string;
  const rawBody = (req as any).rawBody as string;

  if (!sig || !verifyCioWebhook(rawBody, sig, process.env.CIO_WEBHOOK_SECRET!)) {
    return res.status(401).json({ error: 'Invalid webhook signature' });
  }
  next();
}
```

### PII Minimization in Events

```typescript
function sanitizeEventData(data: Record<string, any>): Record<string, any> {
  const PII_FIELDS = ['ssn', 'credit_card', 'password', 'secret'];
  const sanitized = { ...data };

  for (const field of PII_FIELDS) {
    if (sanitized[field]) {
      sanitized[field] = '[REDACTED]';
    }
  }

  // Hash email if used for analytics only
  if (sanitized.email && !sanitized._preserveEmail) {
    sanitized.email_hash = crypto.createHash('sha256')
      .update(sanitized.email.toLowerCase())
      .digest('hex');
    delete sanitized.email;
  }

  return sanitized;
}
```

### API Key Rotation Procedure

```typescript
async function rotateApiKey() {
  // 1. Generate new key in Customer.io dashboard
  // 2. Update secrets manager
  const newKey = await secretsManager.get('cio-api-key-v2');

  // 3. Test new key
  const testClient = new TrackClient(process.env.CIO_SITE_ID!, newKey, { region: RegionUS });
  await testClient.identify('rotation-test', { _test: true });

  // 4. Switch live traffic
  await secretsManager.setActive('cio-api-key', newKey);

  // 5. Revoke old key after drain period (24h)
  console.log('New key active. Revoke old key after 24h drain period.');
}
```

### Request IP Allowlisting

```typescript
// Customer.io webhook source IPs (verify with their docs)
const CIO_WEBHOOK_IPS = [
  '35.188.196.183',
  '35.232.174.22',
  '35.184.18.16',
];

function isValidCioSource(req: Request): boolean {
  const ip = req.headers['x-forwarded-for']?.toString().split(',')[0] ?? req.ip;
  return CIO_WEBHOOK_IPS.includes(ip!);
}
```

## Troubleshooting

### Detecting Leaked Keys

```bash
# Check git history for accidentally committed keys
git log -p --all -S 'CIO_API_KEY' -- '*.ts' '*.js' '*.env'

# Scan current codebase
grep -rn "track_site_id\|CIO_API_KEY\|cio_.*=" --include="*.ts" --include="*.js" src/
```

### Verifying Webhook Security

```bash
# Send a test request without signature (should be rejected)
curl -X POST http://localhost:3000/api/cio/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "test"}' -w "\nHTTP %{http_code}\n"
# Expected: 401

# Send with valid signature
BODY='{"event":"test"}'
SIG=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$CIO_WEBHOOK_SECRET" | cut -d' ' -f2)
curl -X POST http://localhost:3000/api/cio/webhook \
  -H "Content-Type: application/json" \
  -H "x-cio-signature: $SIG" \
  -d "$BODY" -w "\nHTTP %{http_code}\n"
# Expected: 200
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
