# Apollo Data Handling - Implementation Guide

> Full implementation details and code examples for the `apollo-data-handling` skill.

# Apollo Data Handling

## Overview
Data management, compliance, and governance practices for Apollo.io contact data including GDPR, data retention, and secure handling.

## Data Classification

| Data Type | Classification | Retention | Handling |
|-----------|---------------|-----------|----------|
| Email addresses | PII | 2 years | Encrypted at rest |
| Phone numbers | PII | 2 years | Encrypted at rest |
| Names | PII | 2 years | Standard |
| Job titles | Business | 5 years | Standard |
| Company info | Business | 5 years | Standard |
| Engagement data | Analytics | 1 year | Aggregated |

## GDPR Compliance

### Right to Access (Subject Access Request)

```typescript
// src/services/gdpr/access.service.ts
import { Contact } from '../../models/contact.model';
import { Engagement } from '../../models/engagement.model';

interface SubjectAccessResponse {
  personalData: {
    contact: Partial<Contact>;
    engagements: Partial<Engagement>[];
  };
  processingPurposes: string[];
  dataRetention: string;
  dataSources: string[];
}

export async function handleSubjectAccessRequest(
  email: string
): Promise<SubjectAccessResponse> {
  // Find all data for this subject
  const contact = await prisma.contact.findFirst({
    where: { email },
    select: {
      id: true,
      email: true,
      name: true,
      firstName: true,
      lastName: true,
      title: true,
      phone: true,
      linkedinUrl: true,
      company: {
        select: {
          name: true,
          domain: true,
        },
      },
      createdAt: true,
      updatedAt: true,
    },
  });

  if (!contact) {
    return {
      personalData: { contact: {}, engagements: [] },
      processingPurposes: [],
      dataRetention: 'No data found',
      dataSources: [],
    };
  }

  const engagements = await prisma.engagement.findMany({
    where: { contactId: contact.id },
    select: {
      type: true,
      occurredAt: true,
      sequenceId: true,
    },
  });

  return {
    personalData: {
      contact,
      engagements,
    },
    processingPurposes: [
      'B2B sales outreach',
      'Lead qualification',
      'Marketing communications',
    ],
    dataRetention: '2 years from last activity',
    dataSources: ['Apollo.io API', 'User-provided forms'],
  };
}
```

### Right to Erasure (Right to be Forgotten)

```typescript
// src/services/gdpr/erasure.service.ts
interface ErasureResult {
  success: boolean;
  recordsDeleted: {
    contacts: number;
    engagements: number;
    sequences: number;
  };
  apolloNotified: boolean;
}

export async function handleErasureRequest(email: string): Promise<ErasureResult> {
  const result: ErasureResult = {
    success: false,
    recordsDeleted: { contacts: 0, engagements: 0, sequences: 0 },
    apolloNotified: false,
  };

  try {
    // Start transaction
    await prisma.$transaction(async (tx) => {
      // Find contact
      const contact = await tx.contact.findFirst({ where: { email } });
      if (!contact) {
        throw new Error('Contact not found');
      }

      // Delete engagements
      const deletedEngagements = await tx.engagement.deleteMany({
        where: { contactId: contact.id },
      });
      result.recordsDeleted.engagements = deletedEngagements.count;

      // Remove from sequences
      const deletedSequences = await tx.sequenceEnrollment.deleteMany({
        where: { contactId: contact.id },
      });
      result.recordsDeleted.sequences = deletedSequences.count;

      // Delete contact
      await tx.contact.delete({ where: { id: contact.id } });
      result.recordsDeleted.contacts = 1;

      // Notify Apollo (if they support it)
      try {
        await notifyApolloOfDeletion(email);
        result.apolloNotified = true;
      } catch (e) {
        console.warn('Could not notify Apollo of deletion', e);
      }
    });

    result.success = true;

    // Log for audit
    await auditLog.create({
      type: 'GDPR_ERASURE',
      subject: hashEmail(email), // Don't store email in audit log
      timestamp: new Date(),
      recordsAffected: result.recordsDeleted,
    });

    return result;
  } catch (error) {
    console.error('Erasure request failed:', error);
    throw error;
  }
}

async function notifyApolloOfDeletion(email: string): Promise<void> {
  // Apollo doesn't have a deletion API, but we can:
  // 1. Remove from all sequences
  // 2. Mark as do-not-contact
  // 3. Open support ticket for full removal

  console.log(`Note: Contact Apollo support to fully delete ${email} from their system`);
}
```

### Consent Management

```typescript
// src/services/consent/consent.service.ts
import { z } from 'zod';

const ConsentSchema = z.object({
  email: z.string().email(),
  purposes: z.array(z.enum([
    'sales_outreach',
    'marketing_email',
    'analytics',
    'third_party_sharing',
  ])),
  timestamp: z.date(),
  source: z.string(),
  ipAddress: z.string().optional(),
});

type Consent = z.infer<typeof ConsentSchema>;

export async function recordConsent(consent: Consent): Promise<void> {
  await prisma.consent.create({
    data: {
      email: consent.email,
      purposes: consent.purposes,
      grantedAt: consent.timestamp,
      source: consent.source,
      ipAddress: consent.ipAddress,
    },
  });
}

export async function checkConsent(email: string, purpose: string): Promise<boolean> {
  const consent = await prisma.consent.findFirst({
    where: {
      email,
      purposes: { has: purpose },
      revokedAt: null,
    },
    orderBy: { grantedAt: 'desc' },
  });

  return !!consent;
}

export async function revokeConsent(email: string, purpose?: string): Promise<void> {
  if (purpose) {
    // Revoke specific purpose
    await prisma.consent.updateMany({
      where: { email, purposes: { has: purpose } },
      data: { revokedAt: new Date() },
    });
  } else {
    // Revoke all
    await prisma.consent.updateMany({
      where: { email },
      data: { revokedAt: new Date() },
    });
  }
}
```

## Data Retention

```typescript
// src/jobs/data-retention.job.ts
import { CronJob } from 'cron';

// Run daily at 2 AM
const retentionJob = new CronJob('0 2 * * *', async () => {
  console.log('Starting data retention cleanup...');

  const retentionPolicies = [
    { table: 'contacts', field: 'lastActivityAt', maxAgeDays: 730 },
    { table: 'engagements', field: 'occurredAt', maxAgeDays: 365 },
    { table: 'auditLogs', field: 'createdAt', maxAgeDays: 2555 }, // 7 years
  ];

  for (const policy of retentionPolicies) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - policy.maxAgeDays);

    const deleted = await prisma[policy.table].deleteMany({
      where: {
        [policy.field]: { lt: cutoffDate },
      },
    });

    console.log(`Deleted ${deleted.count} records from ${policy.table}`);
  }

  // Archive before deletion for compliance
  await archiveOldData();
});

async function archiveOldData(): Promise<void> {
  const archiveCutoff = new Date();
  archiveCutoff.setDate(archiveCutoff.getDate() - 365);

  // Export to cold storage before deletion
  const oldContacts = await prisma.contact.findMany({
    where: { lastActivityAt: { lt: archiveCutoff } },
  });

  if (oldContacts.length > 0) {
    await uploadToArchive('contacts', oldContacts);
  }
}
```

## Data Export

```typescript
// src/services/export/export.service.ts
import { stringify } from 'csv-stringify/sync';
import { createWriteStream } from 'fs';
import archiver from 'archiver';

interface ExportOptions {
  format: 'csv' | 'json';
  includeEngagements: boolean;
  dateRange?: { start: Date; end: Date };
}

export async function exportContactData(
  criteria: any,
  options: ExportOptions
): Promise<string> {
  const contacts = await prisma.contact.findMany({
    where: {
      ...criteria,
      ...(options.dateRange && {
        createdAt: {
          gte: options.dateRange.start,
          lte: options.dateRange.end,
        },
      }),
    },
    include: options.includeEngagements ? { engagements: true } : undefined,
  });

  const filename = `apollo-export-${Date.now()}`;

  if (options.format === 'csv') {
    const csv = stringify(contacts, {
      header: true,
      columns: ['id', 'email', 'name', 'title', 'company', 'createdAt'],
    });
    await writeFile(`exports/${filename}.csv`, csv);
    return `${filename}.csv`;
  } else {
    await writeFile(`exports/${filename}.json`, JSON.stringify(contacts, null, 2));
    return `${filename}.json`;
  }
}

export async function createSecureExport(
  contacts: any[],
  encryptionKey: string
): Promise<Buffer> {
  const data = JSON.stringify(contacts);
  const encrypted = await encrypt(data, encryptionKey);
  return encrypted;
}
```

## Data Encryption

```typescript
// src/lib/encryption.ts
import crypto from 'crypto';

const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 16;
const AUTH_TAG_LENGTH = 16;

export function encryptPII(plaintext: string, key: Buffer): string {
  const iv = crypto.randomBytes(IV_LENGTH);
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);

  let encrypted = cipher.update(plaintext, 'utf8', 'hex');
  encrypted += cipher.final('hex');

  const authTag = cipher.getAuthTag();

  // Format: iv:authTag:ciphertext
  return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
}

export function decryptPII(encrypted: string, key: Buffer): string {
  const [ivHex, authTagHex, ciphertext] = encrypted.split(':');

  const iv = Buffer.from(ivHex, 'hex');
  const authTag = Buffer.from(authTagHex, 'hex');

  const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(authTag);

  let decrypted = decipher.update(ciphertext, 'hex', 'utf8');
  decrypted += decipher.final('utf8');

  return decrypted;
}

// Column-level encryption for Prisma
export const encryptedFields = {
  email: {
    encrypt: (value: string) => encryptPII(value, getEncryptionKey()),
    decrypt: (value: string) => decryptPII(value, getEncryptionKey()),
  },
  phone: {
    encrypt: (value: string) => encryptPII(value, getEncryptionKey()),
    decrypt: (value: string) => decryptPII(value, getEncryptionKey()),
  },
};
```

## Audit Logging

```typescript
// src/services/audit/audit.service.ts
interface AuditEntry {
  action: string;
  actor: string;
  resource: string;
  resourceId: string;
  changes?: Record<string, { old: any; new: any }>;
  metadata?: Record<string, any>;
  timestamp: Date;
}

export async function logDataAccess(entry: AuditEntry): Promise<void> {
  await prisma.auditLog.create({
    data: {
      action: entry.action,
      actor: entry.actor,
      resource: entry.resource,
      resourceId: entry.resourceId,
      changes: entry.changes ? JSON.stringify(entry.changes) : null,
      metadata: entry.metadata ? JSON.stringify(entry.metadata) : null,
      occurredAt: entry.timestamp,
    },
  });
}

// Middleware to audit all data access
export function auditMiddleware(req: any, res: any, next: any) {
  const originalSend = res.send;

  res.send = function(body: any) {
    // Log data access
    if (req.path.includes('/apollo/') && req.method === 'GET') {
      logDataAccess({
        action: 'DATA_ACCESS',
        actor: req.user?.id || 'anonymous',
        resource: 'apollo_contact',
        resourceId: req.params.id || 'bulk',
        metadata: {
          path: req.path,
          query: req.query,
          responseSize: body?.length,
        },
        timestamp: new Date(),
      });
    }

    return originalSend.call(this, body);
  };

  next();
}
```

## Output
- GDPR compliance (access, erasure, consent)
- Data retention policies
- Secure data export
- Column-level encryption
- Comprehensive audit logging

## Error Handling
| Issue | Resolution |
|-------|------------|
| Export too large | Implement streaming |
| Encryption key lost | Use key management service |
| Audit log gaps | Implement retry queue |
| Consent conflicts | Use latest consent record |

## Resources
- [GDPR Official Text](https://gdpr.eu/)
- [CCPA Requirements](https://oag.ca.gov/privacy/ccpa)
- [Apollo Privacy Policy](https://www.apollo.io/privacy-policy)

## Next Steps
Proceed to `apollo-enterprise-rbac` for access control.
