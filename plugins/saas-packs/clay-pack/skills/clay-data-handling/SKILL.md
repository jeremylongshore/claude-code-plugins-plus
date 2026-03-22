---
name: clay-data-handling
description: |
  Implement GDPR/CCPA-compliant data handling for Clay enrichment pipelines.
  Use when handling PII from enrichments, implementing data retention policies,
  or ensuring regulatory compliance for Clay-enriched lead data.
  Trigger with phrases like "clay data", "clay PII", "clay GDPR",
  "clay data retention", "clay privacy", "clay CCPA", "clay compliance".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, compliance]

---
# Clay Data Handling

## Overview

Manage lead data through Clay enrichment pipelines in compliance with GDPR, CCPA, and data privacy best practices. Clay enriches records with PII (emails, phone numbers, LinkedIn profiles, job titles), requiring careful handling of consent, retention, and export controls.

## Prerequisites

- Clay account with enriched tables
- Understanding of GDPR/CCPA requirements for B2B data
- Data retention policy defined by your legal team
- CRM or database for enriched data storage

## Instructions

### Step 1: Classify Enriched Data by Sensitivity

```typescript
// src/clay/data-classification.ts
enum DataSensitivity {
  PUBLIC = 'public',       // Company name, industry, employee count
  BUSINESS = 'business',   // Work email, job title, LinkedIn URL
  PERSONAL = 'personal',   // Phone number, personal email
  RESTRICTED = 'restricted' // Home address, personal phone
}

const FIELD_CLASSIFICATION: Record<string, DataSensitivity> = {
  company_name: DataSensitivity.PUBLIC,
  industry: DataSensitivity.PUBLIC,
  employee_count: DataSensitivity.PUBLIC,
  domain: DataSensitivity.PUBLIC,
  work_email: DataSensitivity.BUSINESS,
  job_title: DataSensitivity.BUSINESS,
  linkedin_url: DataSensitivity.BUSINESS,
  first_name: DataSensitivity.BUSINESS,
  last_name: DataSensitivity.BUSINESS,
  phone_number: DataSensitivity.PERSONAL,
  personal_email: DataSensitivity.RESTRICTED,
  home_address: DataSensitivity.RESTRICTED,
};

function classifyRow(row: Record<string, unknown>): Record<DataSensitivity, string[]> {
  const classified: Record<DataSensitivity, string[]> = {
    public: [], business: [], personal: [], restricted: [],
  };
  for (const [field, value] of Object.entries(row)) {
    if (value == null) continue;
    const sensitivity = FIELD_CLASSIFICATION[field] || DataSensitivity.BUSINESS;
    classified[sensitivity].push(field);
  }
  return classified;
}
```

### Step 2: Validate Input Data Before Enrichment

```typescript
// src/clay/data-validation.ts
import { z } from 'zod';

const ClayInputSchema = z.object({
  domain: z.string().min(3).refine(d => d.includes('.'), 'Invalid domain'),
  first_name: z.string().min(1).max(100),
  last_name: z.string().min(1).max(100),
  email: z.string().email().optional(),
  source: z.string().optional(),
  consent_basis: z.enum(['legitimate_interest', 'consent', 'contract']).optional(),
});

function validateForEnrichment(rows: unknown[]): {
  valid: z.infer<typeof ClayInputSchema>[];
  invalid: { row: unknown; errors: string[] }[];
} {
  const valid: z.infer<typeof ClayInputSchema>[] = [];
  const invalid: { row: unknown; errors: string[] }[] = [];

  for (const row of rows) {
    const result = ClayInputSchema.safeParse(row);
    if (result.success) {
      valid.push(result.data);
    } else {
      invalid.push({
        row,
        errors: result.error.issues.map(i => `${i.path.join('.')}: ${i.message}`),
      });
    }
  }

  return { valid, invalid };
}
```

### Step 3: Deduplicate Before Enrichment

```typescript
// src/clay/dedup.ts — prevent credit waste on duplicates
function deduplicateLeads(
  rows: Record<string, unknown>[],
  keyFields: string[] = ['domain', 'first_name', 'last_name'],
): { unique: Record<string, unknown>[]; duplicates: number } {
  const seen = new Set<string>();
  const unique: Record<string, unknown>[] = [];
  let duplicates = 0;

  for (const row of rows) {
    const key = keyFields
      .map(f => String(row[f] || '').toLowerCase().trim())
      .join(':');

    if (seen.has(key)) {
      duplicates++;
      continue;
    }
    seen.add(key);
    unique.push(row);
  }

  return { unique, duplicates };
}
```

### Step 4: Add Retention Metadata to Enriched Data

```typescript
// src/clay/retention.ts
interface EnrichedRecordWithRetention {
  // Original enriched data
  [key: string]: unknown;
  // Retention metadata
  _enriched_at: string;       // ISO timestamp
  _retention_expires: string; // ISO timestamp
  _enrichment_source: string; // 'clay'
  _consent_basis: string;     // Legal basis for processing
  _data_subject_rights: string; // How to handle deletion requests
}

function addRetentionMetadata(
  enrichedRow: Record<string, unknown>,
  retentionDays: number = 365,
  consentBasis: string = 'legitimate_interest',
): EnrichedRecordWithRetention {
  const now = new Date();
  const expires = new Date(now.getTime() + retentionDays * 24 * 60 * 60 * 1000);

  return {
    ...enrichedRow,
    _enriched_at: now.toISOString(),
    _retention_expires: expires.toISOString(),
    _enrichment_source: 'clay',
    _consent_basis: consentBasis,
    _data_subject_rights: 'Contact privacy@yourcompany.com for deletion/access requests',
  };
}
```

### Step 5: GDPR-Compliant Export

```typescript
// src/clay/export.ts
/** Strip PII for analytics/reporting exports */
function anonymizeForAnalytics(row: Record<string, unknown>): Record<string, unknown> {
  const anonymized = { ...row };
  // Hash identifiers instead of including plaintext
  if (anonymized.work_email) {
    anonymized.email_hash = crypto.createHash('sha256')
      .update(String(anonymized.work_email).toLowerCase())
      .digest('hex');
    delete anonymized.work_email;
  }
  // Remove all personal identifiers
  delete anonymized.first_name;
  delete anonymized.last_name;
  delete anonymized.phone_number;
  delete anonymized.linkedin_url;
  delete anonymized.personal_email;

  return anonymized;
}

/** Full export for CRM push (with consent tracking) */
function exportForCRM(row: Record<string, unknown>): Record<string, unknown> {
  return {
    ...row,
    processing_consent: row._consent_basis || 'legitimate_interest',
    enrichment_date: row._enriched_at,
    data_source: 'clay_enrichment',
  };
}
```

### Step 6: Data Subject Rights Implementation

```typescript
// src/clay/data-rights.ts — handle GDPR deletion/access requests
async function handleDeletionRequest(email: string): Promise<{
  tablesAffected: string[];
  recordsDeleted: number;
}> {
  // In Clay: manually delete rows containing this email
  // In your database: automated deletion
  console.log(`Processing deletion request for ${email}`);

  // 1. Find all records
  const records = await db.query('SELECT * FROM enriched_leads WHERE email = ?', [email]);

  // 2. Delete from database
  await db.query('DELETE FROM enriched_leads WHERE email = ?', [email]);

  // 3. Log for compliance audit
  await db.query('INSERT INTO deletion_log (email_hash, deleted_at, record_count) VALUES (?, ?, ?)', [
    crypto.createHash('sha256').update(email).digest('hex'),
    new Date().toISOString(),
    records.length,
  ]);

  // 4. Note: Clay table rows must be deleted manually in Clay UI
  return {
    tablesAffected: ['enriched_leads'],
    recordsDeleted: records.length,
  };
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| High duplicate rate | Same list imported twice | Run dedup before sending to Clay |
| Invalid emails in export | Bad source data | Validate with Zod before import |
| Expired data in CRM | No retention cleanup | Schedule weekly expiration check |
| Missing consent basis | No legal basis tracked | Add consent_basis to all records |
| GDPR deletion incomplete | Data in multiple systems | Track all systems in data map |

## Resources

- [GDPR Official Text](https://gdpr.eu/what-is-gdpr/)
- [CCPA Requirements](https://oag.ca.gov/privacy/ccpa)
- [Clay Community](https://community.clay.com)

## Next Steps

For access control, see `clay-enterprise-rbac`.
