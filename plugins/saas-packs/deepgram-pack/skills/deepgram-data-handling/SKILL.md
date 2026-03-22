---
name: deepgram-data-handling
description: |
  Implement audio data handling best practices for Deepgram integrations.
  Use when managing audio file storage, implementing data retention,
  or ensuring GDPR/HIPAA compliance for transcription data.
  Trigger: "deepgram data", "audio storage", "transcription data",
  "deepgram GDPR", "deepgram HIPAA", "deepgram privacy", "PII redaction".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, data, compliance, privacy]

---
# Deepgram Data Handling

## Overview
Best practices for handling audio and transcript data with Deepgram. Covers Deepgram's built-in `redact` parameter for PII, secure audio upload with encryption, transcript storage patterns, data retention policies, and GDPR/HIPAA compliance workflows.

## Data Privacy Quick Reference

| Deepgram Feature | What It Does | Enable |
|-------------------|-------------|--------|
| `redact: ['pci']` | Masks credit card numbers in transcript | Query param |
| `redact: ['ssn']` | Masks Social Security numbers | Query param |
| `redact: ['numbers']` | Masks all numeric sequences | Query param |
| Data retention | Deepgram does NOT store audio or transcripts | Default behavior |

**Deepgram's data policy:** Audio is processed in real-time and not stored. Transcripts are not retained unless you use Deepgram's optional storage features.

## Instructions

### Step 1: Deepgram Built-in PII Redaction

```typescript
import { createClient } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY!);

// Deepgram redacts PII directly during transcription
const { result } = await deepgram.listen.prerecorded.transcribeUrl(
  { url: audioUrl },
  {
    model: 'nova-3',
    smart_format: true,
    redact: ['pci', 'ssn'],  // Credit cards + SSNs -> [REDACTED]
  }
);

// Output: "My card is [REDACTED] and SSN is [REDACTED]"
console.log(result.results.channels[0].alternatives[0].transcript);

// For maximum privacy, redact all numbers:
// redact: ['pci', 'ssn', 'numbers']
```

### Step 2: Application-Level PII Redaction

```typescript
// Additional redaction patterns beyond Deepgram's built-in
const piiPatterns: Array<{ name: string; pattern: RegExp; replacement: string }> = [
  { name: 'email',    pattern: /\b[\w.-]+@[\w.-]+\.\w{2,}\b/g, replacement: '[EMAIL]' },
  { name: 'phone',    pattern: /\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g, replacement: '[PHONE]' },
  { name: 'dob',      pattern: /\b(0[1-9]|1[0-2])[\/.-](0[1-9]|[12]\d|3[01])[\/.-](19|20)\d{2}\b/g, replacement: '[DOB]' },
  { name: 'address',  pattern: /\b\d{1,5}\s[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b/gi, replacement: '[ADDRESS]' },
];

function redactPII(text: string): { redacted: string; found: string[] } {
  let redacted = text;
  const found: string[] = [];

  for (const { name, pattern, replacement } of piiPatterns) {
    const matches = text.match(pattern);
    if (matches) {
      found.push(`${name}: ${matches.length} occurrence(s)`);
      redacted = redacted.replace(pattern, replacement);
    }
  }

  return { redacted, found };
}

// Usage after Deepgram transcription:
const transcript = result.results.channels[0].alternatives[0].transcript;
const { redacted, found } = redactPII(transcript);
if (found.length > 0) console.log('PII found and redacted:', found);
```

### Step 3: Secure Audio Upload and Storage

```typescript
import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { createHash, randomUUID } from 'crypto';
import { readFileSync } from 'fs';

const s3 = new S3Client({ region: process.env.AWS_REGION ?? 'us-east-1' });
const BUCKET = process.env.AUDIO_BUCKET!;

async function uploadAudio(filePath: string, metadata: Record<string, string> = {}) {
  const audio = readFileSync(filePath);
  const checksum = createHash('sha256').update(audio).digest('hex');
  const key = `audio/${randomUUID()}-${checksum.substring(0, 8)}.wav`;

  await s3.send(new PutObjectCommand({
    Bucket: BUCKET,
    Key: key,
    Body: audio,
    ContentType: 'audio/wav',
    ServerSideEncryption: 'aws:kms',  // Encrypt at rest
    Metadata: {
      ...metadata,
      checksum,
      uploadedAt: new Date().toISOString(),
    },
  }));

  // Generate presigned URL for Deepgram to fetch (expires in 1 hour)
  const presignedUrl = await getSignedUrl(s3,
    new GetObjectCommand({ Bucket: BUCKET, Key: key }),
    { expiresIn: 3600 }
  );

  return { key, checksum, presignedUrl };
}

// Upload -> Get presigned URL -> Send to Deepgram
const { presignedUrl } = await uploadAudio('./recording.wav', { source: 'call-center' });
const { result } = await deepgram.listen.prerecorded.transcribeUrl(
  { url: presignedUrl },
  { model: 'nova-3', smart_format: true, redact: ['pci', 'ssn'] }
);
```

### Step 4: Transcript Storage Pattern

```typescript
interface StoredTranscript {
  id: string;
  audioKey: string;           // S3 reference
  requestId: string;          // Deepgram request_id
  transcript: string;         // Redacted text
  confidence: number;
  duration: number;           // Audio duration in seconds
  model: string;
  speakers: number;
  utterances?: Array<{
    speaker: number;
    text: string;
    start: number;
    end: number;
  }>;
  metadata: {
    redacted: boolean;
    piiTypesFound: string[];
    createdAt: string;
    retentionPolicy: 'standard' | 'legal_hold' | 'hipaa';
    expiresAt: string;
  };
}

function buildTranscriptRecord(
  audioKey: string,
  result: any,
  retentionDays = 90
): StoredTranscript {
  const alt = result.results.channels[0].alternatives[0];
  const { redacted, found } = redactPII(alt.transcript);

  return {
    id: randomUUID(),
    audioKey,
    requestId: result.metadata.request_id,
    transcript: redacted,
    confidence: alt.confidence,
    duration: result.metadata.duration,
    model: Object.keys(result.metadata.model_info ?? {})[0] ?? 'unknown',
    speakers: new Set(alt.words?.map((w: any) => w.speaker).filter(Boolean)).size,
    utterances: result.results.utterances?.map((u: any) => ({
      speaker: u.speaker,
      text: u.transcript,
      start: u.start,
      end: u.end,
    })),
    metadata: {
      redacted: found.length > 0,
      piiTypesFound: found,
      createdAt: new Date().toISOString(),
      retentionPolicy: 'standard',
      expiresAt: new Date(Date.now() + retentionDays * 86400000).toISOString(),
    },
  };
}
```

### Step 5: Data Retention Policies

```typescript
const retentionPolicies = {
  standard: { days: 90, description: 'Default retention' },
  legal_hold: { days: 2555, description: '7 years for legal' },
  hipaa: { days: 2190, description: '6 years per HIPAA' },
  temp: { days: 7, description: 'Temporary processing' },
};

async function enforceRetention(db: any, s3Client: S3Client, bucket: string) {
  const now = new Date();

  // Find expired transcripts
  const expired = await db.query(
    'SELECT id, audio_key FROM transcripts WHERE expires_at < $1 AND retention_policy != $2',
    [now.toISOString(), 'legal_hold']
  );

  console.log(`Found ${expired.rows.length} expired transcripts`);

  for (const row of expired.rows) {
    // Delete audio from S3
    try {
      await s3Client.send(new DeleteObjectCommand({
        Bucket: bucket, Key: row.audio_key,
      }));
    } catch (err: any) {
      console.error(`S3 delete failed for ${row.audio_key}:`, err.message);
    }

    // Delete transcript from database
    await db.query('DELETE FROM transcripts WHERE id = $1', [row.id]);
    console.log(`Deleted: ${row.id}`);
  }

  return expired.rows.length;
}
```

### Step 6: GDPR Right to Erasure

```typescript
async function processErasureRequest(userId: string, db: any, s3Client: S3Client, bucket: string) {
  console.log(`Processing GDPR erasure request for user: ${userId}`);

  // 1. Find all user transcripts
  const transcripts = await db.query(
    'SELECT id, audio_key FROM transcripts WHERE user_id = $1', [userId]
  );

  // 2. Delete audio files from S3
  for (const row of transcripts.rows) {
    if (row.audio_key) {
      await s3Client.send(new DeleteObjectCommand({ Bucket: bucket, Key: row.audio_key }));
    }
  }

  // 3. Delete transcripts from database
  const deleted = await db.query('DELETE FROM transcripts WHERE user_id = $1', [userId]);

  // 4. Delete user metadata
  await db.query('DELETE FROM user_metadata WHERE user_id = $1', [userId]);

  // 5. Audit log (keep for compliance — does not contain PII)
  console.log(JSON.stringify({
    action: 'gdpr_erasure',
    userId: userId.substring(0, 8) + '...',  // Partial for audit
    transcriptsDeleted: deleted.rowCount,
    audioFilesDeleted: transcripts.rows.length,
    timestamp: new Date().toISOString(),
  }));

  return { transcriptsDeleted: deleted.rowCount, audioFilesDeleted: transcripts.rows.length };
}
```

## Output
- Deepgram built-in PII redaction (pci, ssn, numbers)
- Application-level PII redaction (email, phone, DOB, address)
- Secure audio upload to S3 with KMS encryption
- Transcript storage pattern with retention metadata
- Automated retention enforcement
- GDPR erasure workflow

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII still visible | Deepgram `redact` not set | Add `redact: ['pci', 'ssn']` to options |
| S3 upload fails | Missing KMS permissions | Add `kms:GenerateDataKey` to IAM role |
| Retention not enforced | Cron not running | Schedule retention job, add monitoring |
| Erasure incomplete | Transaction failed | Use database transactions for atomic delete |

## Resources
- [Deepgram Redaction](https://developers.deepgram.com/docs/redaction)
- [Deepgram Security](https://deepgram.com/security)
- [HIPAA Compliance](https://deepgram.com/hipaa)
- [GDPR Guide](https://developers.deepgram.com/docs/gdpr)
