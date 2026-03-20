---
name: juicebox-data-handling
description: |
  Implement Juicebox data privacy and handling (GDPR/PII).
  Use when classifying candidate PII, building redaction pipelines,
  enforcing retention policies, or handling data subject access/deletion requests.
  Trigger with phrases like "juicebox data privacy", "juicebox GDPR",
  "juicebox PII handling", "juicebox candidate data compliance".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Data Handling

## Overview

Juicebox search results contain PII (names, emails, phones, work history) that requires classification, redaction, retention enforcement, and GDPR rights handling. This skill implements all five layers: field-level classification, log/export redaction, auto-purge cron, data subject access/deletion/rectification endpoints, and consent gating for enrichment.

## Prerequisites

- Juicebox API credentials (`username` and `api_token`)
- Node.js 18+ with TypeScript
- Database with Prisma ORM (PostgreSQL recommended)
- Understanding of applicable regulations (GDPR Article 17, CCPA)

## Instructions

### Step 1: Classify PII fields in candidate profiles

Juicebox returns structured profile data. Map every field to a sensitivity tier that determines retention, access, and logging behavior.

```typescript
// lib/data-classifier.ts
export enum DataCategory {
  PUBLIC = 'public',
  CONTACT = 'contact',
  SENSITIVE = 'sensitive',
  DERIVED = 'derived'
}

export const fieldClassification: Record<string, DataCategory> = {
  // Public — visible on LinkedIn, no special handling
  name: DataCategory.PUBLIC,
  title: DataCategory.PUBLIC,
  company: DataCategory.PUBLIC,
  location: DataCategory.PUBLIC,
  linkedin_url: DataCategory.PUBLIC,

  // Contact — PII, requires consent, limited retention
  email: DataCategory.CONTACT,
  phone: DataCategory.CONTACT,
  personal_email: DataCategory.CONTACT,

  // Sensitive — highest protection, shortest retention
  salary: DataCategory.SENSITIVE,
  compensation: DataCategory.SENSITIVE,

  // Derived — internal scores/notes, no auto-delete
  fit_score: DataCategory.DERIVED,
  recruiter_notes: DataCategory.DERIVED
};

export function classifyProfile(data: Record<string, unknown>): Record<DataCategory, string[]> {
  const classified: Record<DataCategory, string[]> = {
    [DataCategory.PUBLIC]: [],
    [DataCategory.CONTACT]: [],
    [DataCategory.SENSITIVE]: [],
    [DataCategory.DERIVED]: []
  };

  for (const field of Object.keys(data)) {
    const category = fieldClassification[field] ?? DataCategory.DERIVED;
    classified[category].push(field);
  }

  return classified;
}
```

| Category | Fields | Retention | Who can access |
|----------|--------|-----------|----------------|
| Public | name, title, company, location, linkedin_url | 1 year | All authenticated users |
| Contact | email, phone, personal_email | 90 days | Recruiters with `profile:contact` permission |
| Sensitive | salary, compensation | 30 days | Admins only |
| Derived | fit_score, recruiter_notes | No auto-delete | Internal users |

### Step 2: Build PII redaction for logs and exports

Never log raw contact or sensitive data. Redact before any write to stdout, log aggregators, or exported CSVs.

```typescript
// lib/pii-redactor.ts
import crypto from 'crypto';

export class PIIRedactor {
  maskForLogging(profile: Record<string, unknown>): Record<string, unknown> {
    return {
      ...profile,
      email: this.maskEmail(profile.email as string),
      phone: this.maskPhone(profile.phone as string),
      personal_email: '[REDACTED]',
      salary: profile.salary ? '[REDACTED]' : undefined,
      compensation: profile.compensation ? '[REDACTED]' : undefined
    };
  }

  private maskEmail(email?: string): string | undefined {
    if (!email) return undefined;
    const [local, domain] = email.split('@');
    return `${local[0]}***@${domain}`;
  }

  private maskPhone(phone?: string): string | undefined {
    if (!phone) return undefined;
    return `***-***-${phone.slice(-4)}`;
  }

  // Encrypt contact/sensitive data at rest using AES-GCM
  encryptAtRest(plaintext: string, key: Buffer): string {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    let encrypted = cipher.update(plaintext, 'utf8', 'base64');
    encrypted += cipher.final('base64');
    const tag = cipher.getAuthTag();
    return `${iv.toString('base64')}:${tag.toString('base64')}:${encrypted}`;
  }

  decryptFromRest(ciphertext: string, key: Buffer): string {
    const [ivB64, tagB64, data] = ciphertext.split(':');
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(ivB64, 'base64'));
    decipher.setAuthTag(Buffer.from(tagB64, 'base64'));
    let decrypted = decipher.update(data, 'base64', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
  }
}
```

### Step 3: Enforce retention policies with auto-purge

Run a daily cron that deletes data past its category's retention window.

```typescript
// lib/retention-policy.ts
import { DataCategory } from './data-classifier';

interface RetentionReport {
  processed: number;
  deleted: number;
  errors: string[];
}

export class RetentionPolicy {
  private readonly retentionDays: Record<DataCategory, number> = {
    [DataCategory.PUBLIC]: 365,
    [DataCategory.CONTACT]: 90,
    [DataCategory.SENSITIVE]: 30,
    [DataCategory.DERIVED]: -1  // no auto-delete
  };

  async enforceAll(db: PrismaClient): Promise<RetentionReport> {
    const report: RetentionReport = { processed: 0, deleted: 0, errors: [] };

    for (const [category, days] of Object.entries(this.retentionDays)) {
      if (days < 0) continue;

      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - days);

      try {
        const result = await db.$transaction(async (tx) => {
          const expired = await tx.profileData.findMany({
            where: { category, createdAt: { lt: cutoff } }
          });
          if (expired.length === 0) return { processed: 0, deleted: 0 };

          await tx.profileData.deleteMany({
            where: { id: { in: expired.map(e => e.id) } }
          });
          return { processed: expired.length, deleted: expired.length };
        });
        report.processed += result.processed;
        report.deleted += result.deleted;
      } catch (err) {
        report.errors.push(`${category}: ${(err as Error).message}`);
      }
    }

    return report;
  }
}
```

Schedule with node-cron:

```typescript
// jobs/retention-cron.ts
import cron from 'node-cron';
import { RetentionPolicy } from '../lib/retention-policy';
import { prisma } from '../lib/db';

cron.schedule('0 2 * * *', async () => {
  const policy = new RetentionPolicy();
  const report = await policy.enforceAll(prisma);
  console.log(JSON.stringify({ event: 'retention_enforced', ...report }));
});
```

### Step 4: Implement data subject rights (access, deletion, rectification)

GDPR Articles 15, 17, and 16 require you to export, delete, or correct a person's data on request.

```typescript
// services/data-rights.ts
export class DataRightsService {
  constructor(private db: PrismaClient) {}

  // Article 15 — Right of access
  async handleAccessRequest(subjectEmail: string): Promise<{
    profiles: unknown[];
    accessLogs: unknown[];
    exportedAt: Date;
  }> {
    const profiles = await this.db.profiles.findMany({
      where: { email: subjectEmail }
    });
    const accessLogs = await this.db.accessLogs.findMany({
      where: { profileEmail: subjectEmail }
    });
    return { profiles, accessLogs, exportedAt: new Date() };
  }

  // Article 17 — Right to erasure
  async handleDeletionRequest(
    subjectEmail: string,
    requestId: string
  ): Promise<{ requestId: string; deletedRecords: number }> {
    return this.db.$transaction(async (tx) => {
      const deleted = await tx.profiles.deleteMany({
        where: { email: subjectEmail }
      });

      await tx.deletionLogs.create({
        data: { requestId, subjectEmail, deletedCount: deleted.count, completedAt: new Date() }
      });

      return { requestId, deletedRecords: deleted.count };
    });
  }

  // Article 16 — Right to rectification
  async handleRectification(
    subjectEmail: string,
    corrections: Record<string, unknown>
  ): Promise<void> {
    await this.db.profiles.updateMany({
      where: { email: subjectEmail },
      data: corrections
    });

    await this.db.auditLogs.create({
      data: { type: 'rectification', subjectEmail, changes: corrections }
    });
  }
}
```

### Step 5: Track consent per candidate

Record when and how consent was obtained, and gate enrichment/outreach behind active consent.

```typescript
// lib/consent-tracker.ts
export interface ConsentRecord {
  subjectEmail: string;
  purpose: 'recruiting' | 'marketing' | 'analytics';
  granted: boolean;
  source: 'form' | 'email_reply' | 'api';
  grantedAt: Date;
  expiresAt?: Date;
}

export class ConsentTracker {
  constructor(private db: PrismaClient) {}

  async recordConsent(record: ConsentRecord): Promise<void> {
    await this.db.consent.upsert({
      where: {
        subjectEmail_purpose: {
          subjectEmail: record.subjectEmail,
          purpose: record.purpose
        }
      },
      create: record,
      update: { granted: record.granted, grantedAt: record.grantedAt }
    });
  }

  async hasActiveConsent(email: string, purpose: string): Promise<boolean> {
    const consent = await this.db.consent.findUnique({
      where: { subjectEmail_purpose: { subjectEmail: email, purpose } }
    });
    if (!consent || !consent.granted) return false;
    if (consent.expiresAt && consent.expiresAt < new Date()) return false;
    return true;
  }

  // Gate enrichment behind consent
  async enrichWithConsentCheck(
    email: string,
    juiceboxClient: JuiceboxClient
  ): Promise<EnrichedProfile | null> {
    const consented = await this.hasActiveConsent(email, 'recruiting');
    if (!consented) {
      console.log(JSON.stringify({
        event: 'enrichment_blocked',
        reason: 'no_consent',
        email: email[0] + '***'
      }));
      return null;
    }

    const response = await juiceboxClient.post('/api/search', {
      headers: { Authorization: `token ${process.env.JB_USERNAME}:${process.env.JB_API_TOKEN}` },
      body: JSON.stringify({ query: email, limit: 1 })
    });
    return response.json();
  }
}
```

## Output

- `lib/data-classifier.ts` — field-level PII classification enum and mapper
- `lib/pii-redactor.ts` — masking for logs, AES-256-GCM encrypt/decrypt for storage
- `lib/retention-policy.ts` — per-category retention windows with daily cron purge
- `services/data-rights.ts` — GDPR Article 15/16/17 handlers (access, rectification, erasure)
- `lib/consent-tracker.ts` — consent recording, expiry checking, enrichment gating

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `401 Unauthorized` | Invalid `token username:api_token` format or expired token | Regenerate API token at juicebox.ai dashboard, verify `username:token` format |
| `ENCRYPTION_KEY_LENGTH` | AES-256-GCM requires exactly 32-byte key | Use `crypto.randomBytes(32)` to generate, store in secret manager |
| `P2025 Record not found` | Deletion request for email with no stored profiles | Return success with `deletedRecords: 0` — idempotent by design |
| `CONSENT_EXPIRED` | Consent record exists but `expiresAt` is past | Re-request consent before enrichment; do not auto-renew |
| `RETENTION_TX_TIMEOUT` | Large batch delete exceeds Prisma transaction timeout | Increase `transactionTimeout` in Prisma client config or batch deletes in chunks of 1000 |

## Examples

**Classify and redact a Juicebox search result before logging:**

```typescript
import { classifyProfile } from './lib/data-classifier';
import { PIIRedactor } from './lib/pii-redactor';

const redactor = new PIIRedactor();

// Raw profile from Juicebox API
const profile = {
  name: 'Jane Doe',
  title: 'Staff Engineer',
  company: 'Acme Corp',
  email: 'jane.doe@acme.com',
  phone: '+1-555-867-5309',
  salary: '185000'
};

const classification = classifyProfile(profile);
// { public: ['name','title','company'], contact: ['email','phone'], sensitive: ['salary'], derived: [] }

const safe = redactor.maskForLogging(profile);
// { name: 'Jane Doe', title: 'Staff Engineer', company: 'Acme Corp',
//   email: 'j***@acme.com', phone: '***-***-5309', salary: '[REDACTED]' }

console.log(JSON.stringify({ event: 'search_result', profile: safe }));
```

**Handle a GDPR deletion request end-to-end:**

```typescript
import { DataRightsService } from './services/data-rights';
import { prisma } from './lib/db';

const rights = new DataRightsService(prisma);

// Subject requests deletion
const result = await rights.handleDeletionRequest(
  'jane.doe@acme.com',
  'GDPR-REQ-2026-0042'
);
console.log(`Deleted ${result.deletedRecords} records for request ${result.requestId}`);
// Deleted 3 records for request GDPR-REQ-2026-0042
```

## Resources

- [Juicebox API docs](https://juicebox.ai/docs)
- [GDPR full text — Articles 15-17](https://gdpr.eu/tag/chapter-3/)
- [CCPA consumer rights](https://oag.ca.gov/privacy/ccpa)
- [Node.js crypto — AES-GCM](https://nodejs.org/api/crypto.html#class-cipher)

## Next Steps

After data handling, see `juicebox-enterprise-rbac` to restrict who can access which candidate pools.
