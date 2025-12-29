---
name: supabase-data-handling
description: |
  Supabase PII handling, data retention, and redaction patterns.
  Use when implementing data privacy or compliance for Supabase.
  Trigger with phrases like "supabase data", "supabase PII",
  "supabase GDPR", "supabase data retention".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Data Handling

## Overview
Handle sensitive data correctly when integrating with Supabase.

## Prerequisites
- supabase-install-auth completed
- Data classification policy defined
- Compliance requirements documented (GDPR, CCPA, etc.)
- Data retention periods established

## Instructions

### Step 1: Data Classification

| Category | Examples | Handling |
|----------|----------|----------|
| PII | Email, name, phone | Encrypt, minimize |
| Sensitive | API keys, tokens | Never log, rotate |
| Business | Usage metrics | Aggregate when possible |
| Public | Product names | Standard handling |

## PII Detection

```typescript
const PII_PATTERNS = [
  { type: 'email', regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone', regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: 'ssn', regex: /\b\d{3}-\d{2}-\d{4}\b/g },
  { type: 'credit_card', regex: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g },
];

function detectPII(text: string): { type: string; match: string }[] {
  const findings: { type: string; match: string }[] = [];

  for (const pattern of PII_PATTERNS) {
    const matches = text.matchAll(pattern.regex);
    for (const match of matches) {
      findings.push({ type: pattern.type, match: match[0] });
    }
  }

  return findings;
}
```

## Data Redaction

```typescript
function redactPII(data: Record<string, any>): Record<string, any> {
  const sensitiveFields = ['email', 'phone', 'ssn', 'password', 'apiKey'];
  const redacted = { ...data };

  for (const field of sensitiveFields) {
    if (redacted[field]) {
      redacted[field] = '[REDACTED]';
    }
  }

  return redacted;
}

// Use in logging
console.log('Supabase request:', redactPII(requestData));
```

## Data Retention Policy

### Retention Periods
| Data Type | Retention | Reason |
|-----------|-----------|--------|
| API logs | 30 days | Debugging |
| Error logs | 90 days | Root cause analysis |
| Audit logs | 7 years | Compliance |
| PII | Until deletion request | GDPR/CCPA |

### Automatic Cleanup

```typescript
async function cleanupSupabaseData(retentionDays: number): Promise<void> {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - retentionDays);

  await db.supabaseLogs.deleteMany({
    createdAt: { $lt: cutoff },
    type: { $nin: ['audit', 'compliance'] },
  });
}

// Schedule daily cleanup
cron.schedule('0 3 * * *', () => cleanupSupabaseData(30));
```

## GDPR/CCPA Compliance

### Data Subject Access Request (DSAR)

```typescript
async function exportUserData(userId: string): Promise<DataExport> {
  const supabaseData = await supabaseClient.getUserData(userId);

  return {
    source: 'Supabase',
    exportedAt: new Date().toISOString(),
    data: {
      profile: supabaseData.profile,
      activities: supabaseData.activities,
      // Include all user-related data
    },
  };
}
```

### Right to Deletion

```typescript
async function deleteUserData(userId: string): Promise<DeletionResult> {
  // 1. Delete from Supabase
  await supabaseClient.deleteUser(userId);

  // 2. Delete local copies
  await db.supabaseUserCache.deleteMany({ userId });

  // 3. Audit log (required to keep)
  await auditLog.record({
    action: 'GDPR_DELETION',
    userId,
    service: 'supabase',
    timestamp: new Date(),
  });

  return { success: true, deletedAt: new Date() };
}
```

### Step 2: Data Minimization

```typescript
// Only request needed fields
const user = await supabaseClient.getUser(userId, {
  fields: ['id', 'name'], // Not email, phone, address
});

// Don't store unnecessary data
const cacheData = {
  id: user.id,
  name: user.name,
  // Omit sensitive fields
};
```

## Output
- PII detected and redacted from logs
- Data retention policies enforced
- GDPR/CCPA compliance implemented
- Audit trail for data access

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| PII in logs | Missing redaction | Add redaction middleware to all logging |
| Retention violation | Data kept too long | Run cleanup job, fix retention settings |
| DSAR timeout | Too much data to export | Implement streaming export |
| Deletion failed | Cascade delete issue | Check foreign key constraints |

## Examples

### Encryption at Rest

```typescript
import { createCipheriv, createDecipheriv } from 'crypto';

function encryptSupabaseData(data: string): string {
  const key = Buffer.from(process.env.ENCRYPTION_KEY!, 'hex');
  const iv = randomBytes(16);
  const cipher = createCipheriv('aes-256-gcm', key, iv);
  const encrypted = cipher.update(data, 'utf8', 'hex') + cipher.final('hex');
  return `${iv.toString('hex')}:${encrypted}:${cipher.getAuthTag().toString('hex')}`;
}
```

## Resources
- [Supabase Privacy Guide](https://supabase.com/docs/privacy)
- [GDPR Compliance](https://supabase.com/docs/gdpr)
- [Data Processing Agreement](https://supabase.com/docs/dpa)

## Next Steps
For enterprise access control, see `supabase-enterprise-rbac`.