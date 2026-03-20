---
name: apollo-data-handling
description: |
  Apollo.io data management and compliance.
  Use when handling contact data, implementing GDPR compliance,
  or managing data exports and retention.
  Trigger with phrases like "apollo data", "apollo gdpr", "apollo compliance",
  "apollo data export", "apollo data retention", "apollo pii".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Data Handling

## Overview
Data management, compliance, and governance practices for Apollo.io contact data. Covers GDPR subject access/erasure requests, data retention policies, secure export, field-level encryption, and audit logging for the Apollo REST API.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Implement GDPR Subject Access Request
```typescript
// src/data/gdpr.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  params: { api_key: process.env.APOLLO_API_KEY },
  headers: { 'Content-Type': 'application/json' },
});

interface SubjectAccessReport {
  email: string;
  dataFound: boolean;
  person?: Record<string, any>;
  sequences?: string[];
  exportedAt: string;
}

async function handleSubjectAccessRequest(email: string): Promise<SubjectAccessReport> {
  // Search for the person in Apollo
  const { data } = await client.post('/people/search', {
    q_keywords: email,
    per_page: 1,
  });

  const person = data.people?.[0];
  if (!person) {
    return { email, dataFound: false, exportedAt: new Date().toISOString() };
  }

  // Collect all data associated with this contact
  return {
    email,
    dataFound: true,
    person: {
      name: person.name,
      title: person.title,
      email: person.email,
      phone: person.phone_numbers,
      organization: person.organization?.name,
      city: person.city,
      state: person.state,
      country: person.country,
    },
    sequences: person.emailer_campaign_ids ?? [],
    exportedAt: new Date().toISOString(),
  };
}
```

### Step 2: Implement Data Erasure (Right to be Forgotten)
```typescript
async function handleErasureRequest(email: string): Promise<{
  email: string;
  erased: boolean;
  contactId?: string;
  sequencesRemoved: number;
}> {
  // Find the contact
  const { data: searchData } = await client.post('/people/search', {
    q_keywords: email,
    per_page: 1,
  });

  const person = searchData.people?.[0];
  if (!person) {
    return { email, erased: false, sequencesRemoved: 0 };
  }

  // Remove from all sequences first
  let sequencesRemoved = 0;
  for (const seqId of person.emailer_campaign_ids ?? []) {
    try {
      await client.post('/emailer_campaigns/remove_contact_ids', {
        emailer_campaign_id: seqId,
        contact_ids: [person.id],
      });
      sequencesRemoved++;
    } catch (err) {
      console.warn(`Failed to remove from sequence ${seqId}:`, err);
    }
  }

  // Delete the contact
  await client.delete(`/contacts/${person.id}`);

  return {
    email,
    erased: true,
    contactId: person.id,
    sequencesRemoved,
  };
}
```

### Step 3: Implement Data Retention Policy
```typescript
// src/data/retention.ts
interface RetentionPolicy {
  maxAgeDays: number;          // delete contacts older than this
  inactiveThresholdDays: number;  // contacts with no activity
  excludeTags: string[];       // never auto-delete these
}

async function enforceRetention(policy: RetentionPolicy) {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - policy.maxAgeDays);

  const { data } = await client.post('/people/search', {
    contact_created_at_before: cutoffDate.toISOString(),
    per_page: 100,
  });

  const candidates = data.people.filter((p: any) => {
    const tags = p.labels ?? [];
    return !policy.excludeTags.some((t) => tags.includes(t));
  });

  console.log(`Found ${candidates.length} contacts past retention (${policy.maxAgeDays} days)`);

  for (const contact of candidates) {
    await client.delete(`/contacts/${contact.id}`);
    console.log(`Deleted: ${contact.name} (created ${contact.created_at})`);
  }

  return { deleted: candidates.length, evaluated: data.people.length };
}
```

### Step 4: Encrypt Sensitive Fields Before Storage
```typescript
// src/data/encryption.ts
import crypto from 'crypto';

const ENCRYPTION_KEY = process.env.APOLLO_ENCRYPTION_KEY!;  // 32-byte hex key
const ALGORITHM = 'aes-256-gcm';

export function encryptField(plaintext: string): string {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(ALGORITHM, Buffer.from(ENCRYPTION_KEY, 'hex'), iv);
  let encrypted = cipher.update(plaintext, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  const tag = cipher.getAuthTag().toString('hex');
  return `${iv.toString('hex')}:${tag}:${encrypted}`;
}

export function decryptField(ciphertext: string): string {
  const [ivHex, tagHex, encrypted] = ciphertext.split(':');
  const decipher = crypto.createDecipheriv(
    ALGORITHM,
    Buffer.from(ENCRYPTION_KEY, 'hex'),
    Buffer.from(ivHex, 'hex'),
  );
  decipher.setAuthTag(Buffer.from(tagHex, 'hex'));
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
}

// Encrypt PII fields before storing Apollo data locally
function encryptContactPII(contact: any) {
  return {
    ...contact,
    email: contact.email ? encryptField(contact.email) : null,
    phone: contact.phone ? encryptField(contact.phone) : null,
    name: contact.name,  // non-PII, keep readable for search
  };
}
```

### Step 5: Implement Audit Logging
```typescript
// src/data/audit-log.ts
interface AuditEntry {
  timestamp: string;
  action: 'search' | 'enrich' | 'export' | 'delete' | 'access_request' | 'erasure';
  userId: string;
  contactId?: string;
  email?: string;
  details: string;
}

const auditLog: AuditEntry[] = [];

export function logAuditEvent(entry: Omit<AuditEntry, 'timestamp'>) {
  const fullEntry: AuditEntry = {
    ...entry,
    timestamp: new Date().toISOString(),
  };
  auditLog.push(fullEntry);

  // In production, write to persistent store (database, cloud logging)
  console.log(`[AUDIT] ${fullEntry.action} by ${fullEntry.userId}: ${fullEntry.details}`);
}

// Usage:
// logAuditEvent({
//   action: 'erasure',
//   userId: 'admin@company.com',
//   email: 'subject@example.com',
//   details: 'GDPR erasure request processed, contact deleted from Apollo',
// });
```

## Output
- GDPR Subject Access Request handler returning all stored data for an email
- Data erasure handler removing contacts from sequences then deleting
- Retention policy enforcer with age-based cleanup and tag exclusions
- AES-256-GCM field-level encryption for PII stored locally
- Audit log capturing every data operation with user attribution

## Error Handling
| Issue | Resolution |
|-------|------------|
| Export too large | Paginate results, stream to file instead of memory |
| Encryption key lost | Use a key management service (GCP KMS, AWS KMS) with key versioning |
| Audit log gaps | Write audit entries to a durable queue before processing |
| Consent conflicts | Use the latest consent timestamp as the authoritative record |

## Examples

### Run a GDPR Compliance Check
```typescript
// Process a subject access request and log it
const report = await handleSubjectAccessRequest('user@example.com');
logAuditEvent({
  action: 'access_request',
  userId: 'privacy-officer@company.com',
  email: 'user@example.com',
  details: `SAR completed. Data found: ${report.dataFound}`,
});
console.log(JSON.stringify(report, null, 2));
```

## Resources
- [GDPR Official Text](https://gdpr.eu/)
- [CCPA Requirements](https://oag.ca.gov/privacy/ccpa)
- [Apollo Privacy Policy](https://www.apollo.io/privacy-policy)

## Next Steps
Proceed to `apollo-enterprise-rbac` for access control.
