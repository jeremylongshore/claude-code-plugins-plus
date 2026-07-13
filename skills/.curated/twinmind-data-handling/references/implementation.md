# TwinMind Data Handling - Detailed Implementation

## Data Classification

| Data Type | Classification | Retention | Notes |
|-----------|---------------|-----------|-------|
| Audio recordings | Not stored | 0 | TwinMind deletes immediately |
| Transcripts | Sensitive | Configurable | Contains meeting content |
| Summaries | Sensitive | Same as transcript | Derived from transcript |
| Action items | Business | Configurable | May contain PII |
| Speaker data | PII | Same as transcript | Names, voice profiles |
| Usage logs | Internal | 90 days | For debugging |

## Retention Policy

```typescript
export interface RetentionPolicy {
  transcripts: { defaultDays: number; maxDays: number; autoDelete: boolean };
  summaries: { defaultDays: number; linkedToTranscript: boolean };
  actionItems: { defaultDays: number; deleteOnComplete: boolean };
  userProfiles: { retainAfterDeletion: number };
}

const defaultRetentionPolicy: RetentionPolicy = {
  transcripts: { defaultDays: 90, maxDays: 365, autoDelete: true },
  summaries: { defaultDays: 90, linkedToTranscript: true },
  actionItems: { defaultDays: 180, deleteOnComplete: false },
  userProfiles: { retainAfterDeletion: 30 },
};

export async function cleanupExpiredData(): Promise<{ transcriptsDeleted: number }> {
  const client = getTwinMindClient();
  const policy = await getRetentionPolicy();
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - policy.transcripts.defaultDays);

  const expired = await client.get('/transcripts', {
    params: { created_before: cutoffDate.toISOString(), limit: 1000 },
  });

  let deleted = 0;
  for (const transcript of expired.data) {
    await client.delete(`/transcripts/${transcript.id}`);
    deleted++;
  }
  return { transcriptsDeleted: deleted };
}
```

## PII Redaction

```typescript
export interface PIIPattern {
  name: string;
  pattern: RegExp;
  replacement: string;
}

const defaultPIIPatterns: PIIPattern[] = [
  { name: 'SSN', pattern: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: '[SSN REDACTED]' },
  { name: 'Credit Card', pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, replacement: '[CARD REDACTED]' },
  { name: 'Email', pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, replacement: '[EMAIL REDACTED]' },
  { name: 'Phone', pattern: /\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b/g, replacement: '[PHONE REDACTED]' },
  { name: 'IP Address', pattern: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, replacement: '[IP REDACTED]' },
];

export function redactPII(text: string, patterns = defaultPIIPatterns): {
  redactedText: string;
  redactions: Array<{ type: string; count: number }>;
} {
  let redactedText = text;
  const redactions: Array<{ type: string; count: number }> = [];
  for (const pattern of patterns) {
    const matches = text.match(pattern.pattern);
    if (matches?.length) {
      redactedText = redactedText.replace(pattern.pattern, pattern.replacement);
      redactions.push({ type: pattern.name, count: matches.length });
    }
  }
  return { redactedText, redactions };
}
```

## GDPR Handler

```typescript
export class GDPRHandler {
  private client = getTwinMindClient();

  // Right to Access (Article 15)
  async handleAccessRequest(email: string) {
    const [transcripts, profile] = await Promise.all([
      this.client.get('/transcripts', { params: { participant_email: email, limit: 1000 } }),
      this.client.get('/users', { params: { email } }),
    ]);
    const summaries = [];
    const actionItems = [];
    for (const transcript of transcripts.data) {
      const [summary, actions] = await Promise.all([
        this.client.get(`/transcripts/${transcript.id}/summary`).catch(() => null),
        this.client.get(`/transcripts/${transcript.id}/action-items`).catch(() => []),
      ]);
      if (summary) summaries.push(summary.data);
      actionItems.push(...(actions.data || []));
    }
    return { transcripts: transcripts.data, summaries, actionItems, profile: profile.data };
  }

  // Right to Erasure (Article 17)
  async handleErasureRequest(email: string) {
    const data = await this.handleAccessRequest(email);
    let transcriptsDeleted = 0;
    for (const transcript of data.transcripts) {
      await this.client.delete(`/transcripts/${transcript.id}`);
      transcriptsDeleted++;
    }
    if (data.profile?.id) await this.client.delete(`/users/${data.profile.id}`);
    return { transcriptsDeleted, profileDeleted: !!data.profile?.id };
  }

  // Right to Data Portability (Article 20)
  async handlePortabilityRequest(email: string): Promise<Buffer> {
    const data = await this.handleAccessRequest(email);
    return Buffer.from(JSON.stringify({ exportedAt: new Date().toISOString(), subject: email, data }, null, 2));
  }
}
```

## Consent Manager

```typescript
export class ConsentManager {
  async recordConsent(userId: string, purposes: ConsentRecord['purposes'], method: 'explicit' | 'implied'): Promise<void> {
    await db.consents.create({ userId, purposes, consentedAt: new Date(), method, version: process.env.CONSENT_POLICY_VERSION || '1.0' });
    const client = getTwinMindClient();
    await client.patch(`/users/${userId}/consent`, purposes);
  }

  async checkConsent(userId: string, purpose: keyof ConsentRecord['purposes']): Promise<boolean> {
    const consent = await db.consents.findLatest({ userId });
    return consent?.purposes[purpose] ?? false;
  }

  async revokeConsent(userId: string, purposes: string[]): Promise<void> {
    const current = await this.getConsent(userId);
    if (!current) throw new Error('No consent record found');
    const updated = { ...current.purposes };
    for (const p of purposes) updated[p as keyof typeof updated] = false;
    await this.recordConsent(userId, updated, 'explicit');
    if (Object.values(updated).every(v => !v)) {
      await new GDPRHandler().handleErasureRequest(userId);
    }
  }
}

export function requireConsent(purpose: keyof ConsentRecord['purposes']) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userId = req.user?.id;
    if (!userId) return res.status(401).json({ error: 'Unauthorized' });
    const manager = new ConsentManager();
    if (!await manager.checkConsent(userId, purpose)) {
      return res.status(403).json({ error: 'Consent required', required_purpose: purpose });
    }
    next();
  };
}
```

## Data Anonymization

```typescript
import crypto from 'crypto';

export function anonymizeTranscript(transcript: Transcript, config: { hashSalt: string }): Transcript {
  const hashId = (id: string) => crypto.createHmac('sha256', config.hashSalt).update(id).digest('hex').substring(0, 16);
  return {
    ...transcript,
    id: hashId(transcript.id),
    text: redactPII(transcript.text).redactedText,
    speakers: transcript.speakers?.map((s, i) => ({ ...s, id: hashId(s.id), name: `Speaker ${i + 1}` })),
    segments: transcript.segments?.map(seg => ({
      ...seg,
      speaker_id: hashId(seg.speaker_id || ''),
      text: redactPII(seg.text).redactedText,
    })),
  };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
