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
tags: [saas, apollo, compliance]

---
# Apollo Data Handling

## Overview
Data management, compliance, and governance for Apollo.io contact data. Apollo's database contains 275M+ contacts with PII (emails, phones, LinkedIn profiles). This covers GDPR subject access/erasure, data retention, field-level encryption, and audit logging — using the real Apollo Contacts API endpoints.

## Prerequisites
- Apollo master API key (contacts/delete requires master key)
- Node.js 18+

## Instructions

### Step 1: GDPR Subject Access Request (SAR)
Find all data Apollo has on a person and export it.

```typescript
// src/data/gdpr.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/api/v1',
  headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! },
});

interface SubjectAccessReport {
  email: string;
  dataFound: boolean;
  crmContact?: Record<string, any>;
  apolloDatabaseMatch?: Record<string, any>;
  activeSequences: string[];
  exportedAt: string;
}

export async function handleSAR(email: string): Promise<SubjectAccessReport> {
  const report: SubjectAccessReport = {
    email, dataFound: false, activeSequences: [],
    exportedAt: new Date().toISOString(),
  };

  // 1. Search your CRM contacts (contacts you've saved)
  const { data: crmData } = await client.post('/contacts/search', {
    q_keywords: email,
    per_page: 1,
  });

  if (crmData.contacts?.length > 0) {
    const c = crmData.contacts[0];
    report.dataFound = true;
    report.crmContact = {
      id: c.id, name: c.name, email: c.email, title: c.title,
      phone: c.phone_numbers, organization: c.organization_name,
      city: c.city, state: c.state, country: c.country,
      createdAt: c.created_at, updatedAt: c.updated_at,
      contactStage: c.contact_stage_id,
      labels: c.label_ids,
    };
    report.activeSequences = c.emailer_campaign_ids ?? [];
  }

  // 2. Check Apollo's database (enrichment data)
  try {
    const { data: enrichData } = await client.post('/people/match', { email });
    if (enrichData.person) {
      report.dataFound = true;
      report.apolloDatabaseMatch = {
        name: enrichData.person.name,
        title: enrichData.person.title,
        seniority: enrichData.person.seniority,
        city: enrichData.person.city,
        linkedinUrl: enrichData.person.linkedin_url,
        organization: enrichData.person.organization?.name,
      };
    }
  } catch { /* person not found in Apollo DB */ }

  return report;
}
```

### Step 2: Right to Erasure (Delete)
```typescript
export async function handleErasure(email: string): Promise<{
  email: string; erased: boolean; sequencesRemoved: number;
}> {
  // 1. Find the CRM contact
  const { data } = await client.post('/contacts/search', {
    q_keywords: email, per_page: 1,
  });

  const contact = data.contacts?.[0];
  if (!contact) return { email, erased: false, sequencesRemoved: 0 };

  // 2. Remove from all sequences first
  let sequencesRemoved = 0;
  for (const seqId of contact.emailer_campaign_ids ?? []) {
    try {
      await client.post('/emailer_campaigns/remove_or_stop_contact_ids', {
        emailer_campaign_id: seqId,
        contact_ids: [contact.id],
      });
      sequencesRemoved++;
    } catch (err: any) {
      console.warn(`Failed to remove from sequence ${seqId}:`, err.message);
    }
  }

  // 3. Delete the contact from your CRM (requires master key)
  await client.delete(`/contacts/${contact.id}`);

  return { email, erased: true, sequencesRemoved };
}
```

### Step 3: Data Retention Policy
```typescript
// src/data/retention.ts
interface RetentionPolicy {
  maxAgeDays: number;
  inactiveThresholdDays: number;
  protectedLabels: string[];  // label IDs to never auto-delete
}

export async function enforceRetention(policy: RetentionPolicy) {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - policy.maxAgeDays);

  // Search for old contacts
  const { data } = await client.post('/contacts/search', {
    sort_by_field: 'contact_created_at',
    sort_ascending: true,
    per_page: 100,
  });

  const candidates = data.contacts.filter((c: any) => {
    if (new Date(c.created_at) > cutoff) return false;
    // Skip contacts with protected labels
    const labels = c.label_ids ?? [];
    return !policy.protectedLabels.some((l) => labels.includes(l));
  });

  console.log(`Found ${candidates.length} contacts past ${policy.maxAgeDays}-day retention`);

  let deleted = 0;
  for (const contact of candidates) {
    try {
      await client.delete(`/contacts/${contact.id}`);
      deleted++;
    } catch (err: any) {
      console.error(`Failed to delete ${contact.name}: ${err.message}`);
    }
  }

  return { evaluated: data.contacts.length, deleted };
}
```

### Step 4: Field-Level Encryption for Local Storage
```typescript
// src/data/encryption.ts
import crypto from 'crypto';

const KEY = Buffer.from(process.env.APOLLO_ENCRYPTION_KEY!, 'hex');  // 32 bytes
const ALGO = 'aes-256-gcm';

export function encrypt(plaintext: string): string {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(ALGO, KEY, iv);
  let enc = cipher.update(plaintext, 'utf8', 'hex');
  enc += cipher.final('hex');
  return `${iv.toString('hex')}:${cipher.getAuthTag().toString('hex')}:${enc}`;
}

export function decrypt(ciphertext: string): string {
  const [ivHex, tagHex, enc] = ciphertext.split(':');
  const decipher = crypto.createDecipheriv(ALGO, KEY, Buffer.from(ivHex, 'hex'));
  decipher.setAuthTag(Buffer.from(tagHex, 'hex'));
  let dec = decipher.update(enc, 'hex', 'utf8');
  dec += decipher.final('utf8');
  return dec;
}

// Encrypt PII before storing Apollo data locally
export function encryptContactPII(contact: any) {
  return {
    ...contact,
    email: contact.email ? encrypt(contact.email) : null,
    phone: contact.phone ? encrypt(contact.phone) : null,
    linkedin_url: contact.linkedin_url ? encrypt(contact.linkedin_url) : null,
    name: contact.name,  // keep searchable
  };
}
```

### Step 5: Audit Logging
```typescript
// src/data/audit-log.ts
interface AuditEntry {
  timestamp: string;
  action: 'search' | 'enrich' | 'export' | 'delete' | 'sar' | 'erasure';
  userId: string;
  contactId?: string;
  email?: string;
  detail: string;
}

export function logAudit(entry: Omit<AuditEntry, 'timestamp'>) {
  const full: AuditEntry = { ...entry, timestamp: new Date().toISOString() };
  // In production: write to database or cloud logging
  console.log(`[AUDIT] ${full.action} by ${full.userId}: ${full.detail}`);
}

// Usage:
// logAudit({ action: 'erasure', userId: 'privacy@co.com', email: 'user@ex.com',
//   detail: 'GDPR erasure: contact deleted, removed from 2 sequences' });
```

## Output
- GDPR Subject Access Request handler searching CRM contacts + Apollo database
- Right to Erasure handler: remove from sequences then delete contact
- Retention policy enforcer with age-based cleanup and label protection
- AES-256-GCM field-level encryption for locally stored PII
- Audit log capturing every data operation with user attribution

## Error Handling
| Issue | Resolution |
|-------|------------|
| 403 on delete | Contact deletion requires master API key |
| Contact in active sequence | Remove from sequence before deleting |
| Encryption key lost | Use a KMS (GCP KMS, AWS KMS) with key versioning |
| Audit log gaps | Write to durable store before processing, not after |

## Resources
- [Search for Contacts](https://docs.apollo.io/reference/search-for-contacts)
- [Update Contact Status in Sequence](https://docs.apollo.io/reference/update-contact-status-sequence)
- [Apollo Privacy Policy](https://www.apollo.io/privacy-policy)
- [GDPR Official Text](https://gdpr.eu/)

## Next Steps
Proceed to `apollo-enterprise-rbac` for access control.
