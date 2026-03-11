# Deepgram Data Handling - Implementation Details

## Secure Upload Handler

```typescript
import crypto from 'crypto';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { KMSClient, GenerateDataKeyCommand } from '@aws-sdk/client-kms';

interface UploadOptions {
  userId: string;
  purpose: string;
  retentionDays: number;
  encrypted: boolean;
}

export class SecureAudioUpload {
  private s3: S3Client;
  private kms: KMSClient;
  private bucket: string;
  private kmsKeyId: string;

  constructor() {
    this.s3 = new S3Client({});
    this.kms = new KMSClient({});
    this.bucket = process.env.AUDIO_BUCKET!;
    this.kmsKeyId = process.env.KMS_KEY_ID!;
  }

  async upload(audioBuffer: Buffer, options: UploadOptions): Promise<{ audioId: string; url: string }> {
    const audioId = crypto.randomUUID();
    if (!this.isValidAudio(audioBuffer)) throw new Error('Invalid audio format');

    let encryptedData = audioBuffer;
    let dataKey: string | undefined;
    if (options.encrypted) {
      const { encrypted, key } = await this.encryptData(audioBuffer);
      encryptedData = encrypted;
      dataKey = key;
    }

    const hash = crypto.createHash('sha256').update(audioBuffer).digest('hex');
    const key = `audio/${options.userId}/${audioId}`;
    const expirationDate = new Date();
    expirationDate.setDate(expirationDate.getDate() + options.retentionDays);

    await this.s3.send(new PutObjectCommand({
      Bucket: this.bucket, Key: key, Body: encryptedData, ContentType: 'audio/wav',
      Metadata: {
        'user-id': options.userId, 'purpose': options.purpose,
        'content-hash': hash, 'encrypted': String(options.encrypted),
        'data-key': dataKey || '', 'expiration-date': expirationDate.toISOString(),
      },
      ServerSideEncryption: 'aws:kms', SSEKMSKeyId: this.kmsKeyId,
    }));
    return { audioId, url: `s3://${this.bucket}/${key}` };
  }

  private isValidAudio(buffer: Buffer): boolean {
    const headers = {
      wav: Buffer.from([0x52, 0x49, 0x46, 0x46]),
      mp3: Buffer.from([0xFF, 0xFB]),
      flac: Buffer.from([0x66, 0x4C, 0x61, 0x43]),
    };
    return Object.values(headers).some(header => buffer.slice(0, header.length).equals(header));
  }

  private async encryptData(data: Buffer): Promise<{ encrypted: Buffer; key: string }> {
    const { Plaintext, CiphertextBlob } = await this.kms.send(
      new GenerateDataKeyCommand({ KeyId: this.kmsKeyId, KeySpec: 'AES_256' })
    );
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', Plaintext!, iv);
    const encrypted = Buffer.concat([iv, cipher.update(data), cipher.final(), cipher.getAuthTag()]);
    return { encrypted, key: CiphertextBlob!.toString('base64') };
  }
}
```

## PII Redaction

```typescript
const redactionRules = [
  { name: 'ssn', pattern: /\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b/g, replacement: '[SSN REDACTED]' },
  { name: 'credit_card', pattern: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g, replacement: '[CARD REDACTED]' },
  { name: 'phone', pattern: /\b(\+1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b/g, replacement: '[PHONE REDACTED]' },
  { name: 'email', pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, replacement: '[EMAIL REDACTED]' },
  { name: 'date_of_birth', pattern: /\b(0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12]\d|3[01])[\/\-](19|20)\d{2}\b/g, replacement: '[DOB REDACTED]' },
];

export function redactPII(transcript: string) {
  let redacted = transcript;
  const redactions: Array<{ type: string; count: number }> = [];
  for (const rule of redactionRules) {
    const matches = redacted.match(rule.pattern);
    if (matches?.length) {
      redactions.push({ type: rule.name, count: matches.length });
      redacted = redacted.replace(rule.pattern, rule.replacement);
    }
  }
  return { redacted, redactions };
}

export async function transcribeWithRedaction(client: DeepgramClient, audioUrl: string) {
  const { result, error } = await client.listen.prerecorded.transcribeUrl(
    { url: audioUrl },
    { model: 'nova-2', redact: ['pci', 'ssn', 'numbers'], smart_format: true }
  );
  if (error) throw error;
  const transcript = result.results.channels[0].alternatives[0].transcript;
  const { redacted } = redactPII(transcript);
  return { transcript, redactedTranscript: redacted };
}
```

## Data Retention Policy

```typescript
import { S3Client, ListObjectsV2Command, DeleteObjectsCommand } from '@aws-sdk/client-s3';

const policies = [
  { name: 'standard', retentionDays: 30, dataTypes: ['audio', 'transcript'], complianceReasons: ['business'] },
  { name: 'legal_hold', retentionDays: 365 * 7, dataTypes: ['audio', 'transcript', 'metadata'], complianceReasons: ['legal', 'regulatory'] },
  { name: 'hipaa', retentionDays: 365 * 6, dataTypes: ['audio', 'transcript', 'access_logs'], complianceReasons: ['hipaa'] },
];

export class RetentionManager {
  private s3: S3Client;
  private bucket: string;

  constructor() { this.s3 = new S3Client({}); this.bucket = process.env.AUDIO_BUCKET!; }

  async enforceRetention() {
    const stats = { checked: 0, deleted: 0, retained: 0 };
    const now = new Date();
    const { Contents } = await this.s3.send(new ListObjectsV2Command({ Bucket: this.bucket, Prefix: 'audio/' }));
    if (!Contents) return stats;

    const toDelete: string[] = [];
    for (const object of Contents) {
      stats.checked++;
      if (!object.Key) continue;
      const metadata = await this.getMetadata(object.Key);
      const policy = this.getApplicablePolicy(metadata);
      const expirationDate = new Date(metadata.uploadDate);
      expirationDate.setDate(expirationDate.getDate() + policy.retentionDays);
      if (now > expirationDate && !metadata.legalHold) { toDelete.push(object.Key); stats.deleted++; }
      else { stats.retained++; }
    }
    if (toDelete.length > 0) await this.deleteObjects(toDelete);
    return stats;
  }

  private getApplicablePolicy(metadata: Record<string, string>) {
    if (metadata.legalHold === 'true') return policies.find(p => p.name === 'legal_hold')!;
    if (metadata.hipaa === 'true') return policies.find(p => p.name === 'hipaa')!;
    return policies.find(p => p.name === 'standard')!;
  }

  private async deleteObjects(keys: string[]) { /* batch delete implementation */ }
  private async getMetadata(key: string): Promise<Record<string, string>> { return {}; }
}
```

## GDPR Right to Deletion

```typescript
export class GDPRCompliance {
  private s3: S3Client;
  constructor() { this.s3 = new S3Client({}); }

  async processRightToErasure(userId: string) {
    const deletedItems = { transcripts: 0, audioFiles: 0, metadata: 0 };
    try {
      const transcriptResult = await db.transcripts.deleteMany({ userId });
      deletedItems.transcripts = transcriptResult.deletedCount;

      const audioFiles = await this.listUserAudioFiles(userId);
      for (const file of audioFiles) {
        await this.s3.send(new DeleteObjectCommand({ Bucket: process.env.AUDIO_BUCKET!, Key: file }));
        deletedItems.audioFiles++;
      }

      const metadataResult = await db.userMetadata.deleteMany({ userId });
      deletedItems.metadata = metadataResult.deletedCount;
      await this.logDeletion(userId, deletedItems);
      return { success: true, deletedItems };
    } catch (error) { throw error; }
  }

  async exportUserData(userId: string): Promise<Buffer> {
    const userData = {
      transcripts: await db.transcripts.find({ userId }).toArray(),
      metadata: await db.userMetadata.findOne({ userId }),
      usageHistory: await db.usage.find({ userId }).toArray(),
      exportedAt: new Date().toISOString(),
    };
    return Buffer.from(JSON.stringify(userData, null, 2));
  }
}
```

## Audit Logging

```typescript
export class AuditLogger {
  async log(event: { action: string; userId: string; resourceType: string; resourceId: string; details: Record<string, unknown> }) {
    const fullEvent = { ...event, timestamp: new Date() };
    await db.auditLog.insertOne({ ...fullEvent, hash: this.computeHash(fullEvent) });
    if (process.env.SIEM_ENDPOINT) await this.sendToSIEM(fullEvent);
  }

  private computeHash(event: any): string {
    return crypto.createHash('sha256').update(JSON.stringify(event)).digest('hex');
  }

  private async sendToSIEM(event: any): Promise<void> {
    await fetch(process.env.SIEM_ENDPOINT!, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event),
    });
  }
}
```
