# TwinMind Security Basics - Detailed Implementation

## API Key Management

```typescript
// NEVER hardcode secrets
const apiKey = process.env.TWINMIND_API_KEY;
if (!apiKey) throw new Error('TWINMIND_API_KEY required');

// Use a secrets manager
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

async function getApiKey(): Promise<string> {
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: 'projects/my-project/secrets/twinmind-api-key/versions/latest',
  });
  return version.payload?.data?.toString() || '';
}
```

## Environment Configuration

```bash
# .env file (gitignored)
TWINMIND_API_KEY=tm_sk_your_secret_key
TWINMIND_WEBHOOK_SECRET=whsec_your_webhook_secret
TWINMIND_ENCRYPTION_KEY=your_32_byte_encryption_key

# .env.example (committed to repo - no real values)
TWINMIND_API_KEY=tm_sk_xxx
TWINMIND_WEBHOOK_SECRET=whsec_xxx
TWINMIND_ENCRYPTION_KEY=xxx
```

```gitignore
.env
.env.local
.env.*.local
*.pem
*.key
secrets/
```

## Webhook Signature Verification

```typescript
import crypto from 'crypto';

export function verifyWebhookSignature(
  payload: string | Buffer,
  signature: string,
  secret: string
): boolean {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  const providedSignature = signature.replace('sha256=', '');
  return crypto.timingSafeEqual(
    Buffer.from(expectedSignature),
    Buffer.from(providedSignature)
  );
}

export function webhookMiddleware(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers['x-twinmind-signature'] as string;
  const secret = process.env.TWINMIND_WEBHOOK_SECRET!;
  if (!signature) return res.status(401).json({ error: 'Missing signature' });
  const rawBody = (req as any).rawBody || JSON.stringify(req.body);
  if (!verifyWebhookSignature(rawBody, signature, secret)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  next();
}
```

## Data Encryption (AES-256-GCM)

```typescript
import crypto from 'crypto';

const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 16;

export function encrypt(text: string, key: string): string {
  const iv = crypto.randomBytes(IV_LENGTH);
  const cipher = crypto.createCipheriv(ALGORITHM, Buffer.from(key, 'hex'), iv);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  const tag = cipher.getAuthTag();
  return `${iv.toString('hex')}:${tag.toString('hex')}:${encrypted}`;
}

export function decrypt(encryptedData: string, key: string): string {
  const [ivHex, tagHex, encrypted] = encryptedData.split(':');
  const decipher = crypto.createDecipheriv(ALGORITHM, Buffer.from(key, 'hex'), Buffer.from(ivHex, 'hex'));
  decipher.setAuthTag(Buffer.from(tagHex, 'hex'));
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
}
```

## Access Control

```typescript
export enum Permission {
  READ_TRANSCRIPTS = 'transcripts:read',
  WRITE_TRANSCRIPTS = 'transcripts:write',
  DELETE_TRANSCRIPTS = 'transcripts:delete',
  MANAGE_SETTINGS = 'settings:manage',
  VIEW_ANALYTICS = 'analytics:view',
  ADMIN = 'admin:*',
}

export function hasPermission(user: User, permission: Permission): boolean {
  if (user.permissions.includes(Permission.ADMIN)) return true;
  return user.permissions.includes(permission);
}

export function requirePermission(permission: Permission) {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as User;
    if (!user) return res.status(401).json({ error: 'Unauthorized' });
    if (!hasPermission(user, permission)) return res.status(403).json({ error: 'Insufficient permissions' });
    next();
  };
}
```

## Privacy Configuration

```typescript
export interface PrivacyConfig {
  storeAudio: boolean;
  audioRetentionDays: number;
  storeTranscripts: boolean;
  transcriptRetentionDays: number;
  encryptTranscripts: boolean;
  processLocally: boolean;
  allowSharing: boolean;
  requireConsent: boolean;
  redactPII: boolean;
  piiPatterns: string[];
}

const defaultPrivacyConfig: PrivacyConfig = {
  storeAudio: false,
  audioRetentionDays: 0,
  storeTranscripts: true,
  transcriptRetentionDays: 90,
  encryptTranscripts: true,
  processLocally: true,
  allowSharing: false,
  requireConsent: true,
  redactPII: true,
  piiPatterns: [
    '\\b\\d{3}-\\d{2}-\\d{4}\\b',
    '\\b\\d{16}\\b',
    '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b',
  ],
};
```

## Audit Logging

```typescript
export interface AuditEvent {
  timestamp: Date;
  userId: string;
  action: string;
  resource: string;
  resourceId?: string;
  details?: Record<string, any>;
  ipAddress?: string;
  userAgent?: string;
}

export class AuditLogger {
  private events: AuditEvent[] = [];

  log(event: Omit<AuditEvent, 'timestamp'>): void {
    const fullEvent = { ...event, timestamp: new Date() };
    this.events.push(fullEvent);
    this.persist(fullEvent);
    if (process.env.NODE_ENV === 'development') {
      console.log('[AUDIT]', JSON.stringify(fullEvent));
    }
  }

  private async persist(event: AuditEvent): Promise<void> {
    // Send to logging service (CloudWatch, Datadog)
  }
}
```

## Security Checklist

- [ ] API keys stored in environment variables or secrets manager
- [ ] No hardcoded credentials in source code
- [ ] Webhook signatures verified with timing-safe comparison
- [ ] Transcripts encrypted at rest (AES-256-GCM)
- [ ] PII redaction enabled
- [ ] RBAC implemented with least privilege
- [ ] Audit logging enabled for all sensitive operations
- [ ] MFA enabled for admin accounts
- [ ] Data retention policies configured

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
