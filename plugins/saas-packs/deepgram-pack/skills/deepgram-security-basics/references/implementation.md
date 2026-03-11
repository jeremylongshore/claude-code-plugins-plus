# Deepgram Security Basics - Implementation Details

## AWS Secret Manager Integration
```typescript
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

const client = new SecretsManager({ region: 'us-east-1' });
let cachedKey: string | null = null;
let cacheExpiry = 0;

export async function getDeepgramKey(): Promise<string> {
  if (cachedKey && Date.now() < cacheExpiry) return cachedKey;
  const response = await client.getSecretValue({ SecretId: 'deepgram/api-key' });
  const secret = JSON.parse(response.SecretString!);
  cachedKey = secret.DEEPGRAM_API_KEY;
  cacheExpiry = Date.now() + 300000;
  return cachedKey!;
}
```

## GCP Secret Manager Integration
```typescript
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';
const client = new SecretManagerServiceClient();

export async function getDeepgramKey(): Promise<string> {
  const [version] = await client.accessSecretVersion({
    name: `projects/${process.env.GCP_PROJECT_ID}/secrets/deepgram-api-key/versions/latest`,
  });
  return version.payload?.data?.toString()!;
}
```

## Key Rotation Script
```typescript
export async function rotateDeepgramKey(adminKey: string, projectId: string) {
  const client = createClient(adminKey);

  // Create new key
  const { result: newKey, error } = await client.manage.createProjectKey(projectId, {
    comment: `Rotated key - ${new Date().toISOString()}`,
    scopes: ['usage:write', 'listen:*'],
    expiration_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000),
  });
  if (error) throw new Error(`Failed to create key: ${error.message}`);

  // Test new key
  const testClient = createClient(newKey.key);
  const { error: testError } = await testClient.manage.getProjects();
  if (testError) {
    await client.manage.deleteProjectKey(projectId, newKey.key_id);
    throw new Error('New key validation failed');
  }

  return { newKeyId: newKey.key_id, rotatedAt: new Date() };
}
```

## Scoped API Keys
```typescript
const scopedKeys = {
  transcription: { scopes: ['listen:*'], comment: 'Read-only transcription key' },
  admin: { scopes: ['manage:*'], comment: 'Administrative access only' },
  usage: { scopes: ['usage:read'], comment: 'Usage monitoring only' },
};
```

## Request Sanitization
```typescript
export function sanitizeAudioUrl(url: string): string {
  const parsed = new URL(url);
  if (parsed.protocol !== 'https:') throw new Error('Only HTTPS URLs allowed');
  const blockedHosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1'];
  if (blockedHosts.includes(parsed.hostname)) throw new Error('Local URLs not allowed');
  const privateRanges = [/^10\./, /^172\.(1[6-9]|2[0-9]|3[0-1])\./, /^192\.168\./];
  if (privateRanges.some(range => range.test(parsed.hostname))) throw new Error('Private IPs not allowed');
  return url;
}
```

## Audit Logging
```typescript
export class AuditLogger {
  log(event: { action: string; success: boolean; userId?: string; metadata?: Record<string, unknown> }) {
    console.log(JSON.stringify({ ...event, timestamp: new Date().toISOString() }));
  }

  async transcribe(transcribeFn: () => Promise<unknown>, context: { userId?: string; ipAddress?: string }) {
    const startTime = Date.now();
    try {
      const result = await transcribeFn();
      this.log({ action: 'TRANSCRIBE', success: true, ...context, metadata: { durationMs: Date.now() - startTime } });
      return result;
    } catch (error) {
      this.log({ action: 'TRANSCRIBE', success: false, ...context, metadata: { error: error instanceof Error ? error.message : 'Unknown', durationMs: Date.now() - startTime } });
      throw error;
    }
  }
}
```

## Data Protection (Encryption at Rest)
```typescript
import crypto from 'crypto';

export function encryptTranscript(transcript: string, key: Buffer): string {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
  let encrypted = cipher.update(transcript, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  return JSON.stringify({ iv: iv.toString('hex'), data: encrypted, tag: cipher.getAuthTag().toString('hex') });
}

export function redactSensitiveData(transcript: string): string {
  const patterns = [
    { pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, replacement: '[REDACTED-CC]' },
    { pattern: /\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b/g, replacement: '[REDACTED-SSN]' },
    { pattern: /\b\d{3}[\s-]?\d{3}[\s-]?\d{4}\b/g, replacement: '[REDACTED-PHONE]' },
    { pattern: /\b[\w.-]+@[\w.-]+\.\w+\b/g, replacement: '[REDACTED-EMAIL]' },
  ];
  let redacted = transcript;
  for (const { pattern, replacement } of patterns) redacted = redacted.replace(pattern, replacement);
  return redacted;
}
```
