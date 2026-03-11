# Juicebox Data Handling - Implementation Guide

Detailed implementation examples and code patterns.

## Data Classification

| Category | Examples | Retention | Access |
|----------|----------|-----------|--------|
| Public | Name, title, company | 1 year | All users |
| Contact | Email, phone | 90 days | Recruiters only |
| Sensitive | SSN, salary | 30 days | Admins only |
| Derived | Scores, notes | Permanent | Internal only |

## Instructions

### Step 1: Data Classification System
```typescript
// lib/data-classifier.ts
export enum DataCategory {
  PUBLIC = 'public',
  CONTACT = 'contact',
  SENSITIVE = 'sensitive',
  DERIVED = 'derived'
}

export const fieldClassification: Record<string, DataCategory> = {
  // Public data
  name: DataCategory.PUBLIC,
  title: DataCategory.PUBLIC,
  company: DataCategory.PUBLIC,
  location: DataCategory.PUBLIC,
  linkedin_url: DataCategory.PUBLIC,

  // Contact data
  email: DataCategory.CONTACT,
  phone: DataCategory.CONTACT,
  personal_email: DataCategory.CONTACT,

  // Sensitive data
  salary: DataCategory.SENSITIVE,
  compensation: DataCategory.SENSITIVE,

  // Derived data
  fit_score: DataCategory.DERIVED,
  recruiter_notes: DataCategory.DERIVED
};

export function classifyData(data: Record<string, any>): Record<DataCategory, string[]> {
  const classified: Record<DataCategory, string[]> = {
    [DataCategory.PUBLIC]: [],
    [DataCategory.CONTACT]: [],
    [DataCategory.SENSITIVE]: [],
    [DataCategory.DERIVED]: []
  };

  for (const field of Object.keys(data)) {
    const category = fieldClassification[field] || DataCategory.DERIVED;
    classified[category].push(field);
  }

  return classified;
}
```

### Step 2: PII Handling
```typescript
// lib/pii-handler.ts
import crypto from 'crypto';

export class PIIHandler {
  // Mask sensitive fields for logging
  maskForLogging(profile: Profile): Record<string, any> {
    return {
      ...profile,
      email: this.maskEmail(profile.email),
      phone: this.maskPhone(profile.phone),
      personal_email: undefined // Remove entirely
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

  // Encrypt sensitive data at rest
  encrypt(data: string, key: Buffer): string {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    let encrypted = cipher.update(data, 'utf8', 'base64');
    encrypted += cipher.final('base64');
    const tag = cipher.getAuthTag();
    return `${iv.toString('base64')}:${tag.toString('base64')}:${encrypted}`;
  }

  // Decrypt sensitive data
  decrypt(encrypted: string, key: Buffer): string {
    const [ivB64, tagB64, data] = encrypted.split(':');
    const iv = Buffer.from(ivB64, 'base64');
    const tag = Buffer.from(tagB64, 'base64');
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
    decipher.setAuthTag(tag);
    let decrypted = decipher.update(data, 'base64', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
  }
}
```

### Step 3: Retention Policies
```typescript
// lib/retention-policy.ts
export class RetentionPolicy {
  private policies: Record<DataCategory, number> = {
    [DataCategory.PUBLIC]: 365,      // 1 year
    [DataCategory.CONTACT]: 90,      // 90 days
    [DataCategory.SENSITIVE]: 30,    // 30 days
    [DataCategory.DERIVED]: -1       // No auto-delete
  };

  getRetentionDays(category: DataCategory): number {
    return this.policies[category];
  }

  async enforceRetention(): Promise<RetentionReport> {
    const report: RetentionReport = {
      processed: 0,
      deleted: 0,
      errors: []
    };

    for (const [category, days] of Object.entries(this.policies)) {
      if (days < 0) continue; // Skip no-delete categories

      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - days);

      const result = await this.deleteExpiredData(category as DataCategory, cutoff);
      report.processed += result.processed;
      report.deleted += result.deleted;
    }

    return report;
  }

  private async deleteExpiredData(
    category: DataCategory,
    cutoff: Date
  ): Promise<{ processed: number; deleted: number }> {
    // Implementation depends on data storage
    return db.$transaction(async (tx) => {
      const expired = await tx.profileData.findMany({
        where: {
          category,
          createdAt: { lt: cutoff }
        }
      });

      await tx.profileData.deleteMany({
        where: {
          id: { in: expired.map(e => e.id) }
        }
      });

      return {
        processed: expired.length,
        deleted: expired.length
      };
    });
  }
}

// Run retention daily
cron.schedule('0 2 * * *', async () => {
  const policy = new RetentionPolicy();
  const report = await policy.enforceRetention();
  logger.info('Retention policy enforced', report);
});
```

### Step 4: Data Subject Rights
```typescript
// services/data-rights.ts
export class DataRightsService {
  // Right to access
  async handleAccessRequest(subjectEmail: string): Promise<DataExport> {
    // Find all data for subject
    const profiles = await db.profiles.findMany({
      where: { email: subjectEmail }
    });

    // Include access logs
    const accessLogs = await db.accessLogs.findMany({
      where: { profileEmail: subjectEmail }
    });

    return {
      profiles,
      accessLogs,
      exportedAt: new Date(),
      format: 'json'
    };
  }

  // Right to erasure (GDPR Article 17)
  async handleDeletionRequest(
    subjectEmail: string,
    requestId: string
  ): Promise<DeletionReport> {
    const report: DeletionReport = {
      requestId,
      subjectEmail,
      deletedRecords: 0,
      status: 'completed',
      completedAt: new Date()
    };

    await db.$transaction(async (tx) => {
      // Delete profile data
      const deleted = await tx.profiles.deleteMany({
        where: { email: subjectEmail }
      });
      report.deletedRecords += deleted.count;

      // Delete from cache
      await cache.deleteByPattern(`*${subjectEmail}*`);

      // Log deletion for compliance
      await tx.deletionLogs.create({
        data: {
          requestId,
          subjectEmail,
          deletedCount: report.deletedRecords,
          completedAt: new Date()
        }
      });
    });

    // Notify downstream systems
    await this.notifyDeletion(subjectEmail, requestId);

    return report;
  }

  // Right to rectification
  async handleRectificationRequest(
    subjectEmail: string,
    corrections: Record<string, any>
  ): Promise<void> {
    await db.profiles.updateMany({
      where: { email: subjectEmail },
      data: corrections
    });

    // Log for audit
    await db.auditLogs.create({
      data: {
        type: 'rectification',
        subjectEmail,
        changes: corrections
      }
    });
  }
}
```

### Step 5: Access Logging
```typescript
// middleware/access-logging.ts
export function logDataAccess(req: Request, res: Response, next: NextFunction) {
  const originalJson = res.json.bind(res);

  res.json = (data: any) => {
    // Log access to profile data
    if (data?.profiles || data?.profile) {
      const profiles = data.profiles || [data.profile];
      const profileIds = profiles.map((p: any) => p.id);

      db.accessLogs.create({
        data: {
          userId: req.user?.id,
          profileIds,
          operation: req.method,
          path: req.path,
          timestamp: new Date(),
          ip: req.ip,
          userAgent: req.get('user-agent')
        }
      }).catch(console.error);
    }

    return originalJson(data);
  };

  next();
}
```

## Compliance Checklist

```markdown

## Data Handling Compliance

### GDPR Requirements
- [ ] Lawful basis for processing documented
- [ ] Privacy policy updated
- [ ] Data subject rights implemented
- [ ] Data breach notification process
- [ ] DPA with Juicebox executed

### CCPA Requirements
- [ ] "Do Not Sell" option implemented
- [ ] Consumer rights portal
- [ ] Opt-out mechanisms
- [ ] Annual training completed

### Security
- [ ] Encryption at rest
- [ ] Encryption in transit
- [ ] Access logging
- [ ] Regular audits
```
