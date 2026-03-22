---
name: apollo-migration-deep-dive
description: |
  Comprehensive Apollo.io migration strategies.
  Use when migrating from other CRMs to Apollo, consolidating data sources,
  or executing large-scale data migrations.
  Trigger with phrases like "apollo migration", "migrate to apollo",
  "apollo data import", "crm to apollo", "apollo migration strategy".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, migration, scaling]

---
# Apollo Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -10`

## Overview
Migrate contact and company data into Apollo.io from other CRMs (Salesforce, HubSpot) or CSV sources. Uses Apollo's **Contacts API** for creating/updating contacts and **Bulk Create Contacts** endpoint for high-throughput imports (up to 100 contacts per call). Covers field mapping, assessment, batch processing, reconciliation, and rollback.

## Prerequisites
- Apollo master API key (Contacts API requires master key)
- Node.js 18+
- Source CRM export in CSV or JSON format

## Instructions

### Step 1: Define Field Mappings
```typescript
// src/migration/field-map.ts
interface FieldMapping {
  source: string;
  target: string;        // Apollo Contacts API field
  transform?: (v: any) => any;
  required: boolean;
}

// Salesforce -> Apollo
const salesforceMap: FieldMapping[] = [
  { source: 'FirstName', target: 'first_name', required: true },
  { source: 'LastName', target: 'last_name', required: true },
  { source: 'Email', target: 'email', required: true },
  { source: 'Title', target: 'title', required: false },
  { source: 'Phone', target: 'phone_number', required: false },
  { source: 'Company', target: 'organization_name', required: false },
  { source: 'Website', target: 'website_url', required: false,
    transform: (url: string) => url?.startsWith('http') ? url : `https://${url}` },
  { source: 'LinkedIn', target: 'linkedin_url', required: false },
];

// HubSpot -> Apollo
const hubspotMap: FieldMapping[] = [
  { source: 'firstname', target: 'first_name', required: true },
  { source: 'lastname', target: 'last_name', required: true },
  { source: 'email', target: 'email', required: true },
  { source: 'jobtitle', target: 'title', required: false },
  { source: 'phone', target: 'phone_number', required: false },
  { source: 'company', target: 'organization_name', required: false },
  { source: 'website', target: 'website_url', required: false },
];

function mapRecord(record: Record<string, any>, mappings: FieldMapping[]): Record<string, any> {
  const mapped: Record<string, any> = {};
  for (const m of mappings) {
    let value = record[m.source];
    if (m.required && !value) throw new Error(`Missing: ${m.source}`);
    if (value && m.transform) value = m.transform(value);
    if (value) mapped[m.target] = value;
  }
  return mapped;
}
```

### Step 2: Pre-Migration Assessment
```typescript
// src/migration/assessment.ts
import fs from 'fs';
import { parse } from 'csv-parse/sync';

async function assess(csvPath: string, mappings: FieldMapping[]) {
  const records = parse(fs.readFileSync(csvPath, 'utf-8'), { columns: true, skip_empty_lines: true });

  const stats = { total: records.length, valid: 0, invalid: 0,
    missing: {} as Record<string, number>, duplicateEmails: 0, errors: [] as string[] };
  const emails = new Set<string>();

  for (const record of records) {
    try {
      mapRecord(record, mappings);
      const email = record.Email ?? record.email;
      if (emails.has(email)) stats.duplicateEmails++;
      else emails.add(email);
      stats.valid++;
    } catch (err: any) {
      stats.invalid++;
      const field = err.message.replace('Missing: ', '');
      stats.missing[field] = (stats.missing[field] ?? 0) + 1;
      if (stats.errors.length < 5) stats.errors.push(err.message);
    }
  }

  console.log(`Total: ${stats.total}, Valid: ${stats.valid}, Invalid: ${stats.invalid}, Dupes: ${stats.duplicateEmails}`);
  if (Object.keys(stats.missing).length) console.log('Missing fields:', stats.missing);
  return stats;
}
```

### Step 3: Batch Migration Using Bulk Create
Apollo's Bulk Create Contacts endpoint creates up to 100 contacts per call with intelligent deduplication.

```typescript
// src/migration/batch-worker.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/api/v1',
  headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! },
});

interface MigrationResult {
  total: number; created: number; existing: number; failed: number;
  createdIds: string[];
  errors: Array<{ record: any; error: string }>;
}

async function migrateBatch(records: Record<string, any>[], batchSize: number = 100): Promise<MigrationResult> {
  const result: MigrationResult = { total: records.length, created: 0, existing: 0, failed: 0,
    createdIds: [], errors: [] };

  for (let i = 0; i < records.length; i += batchSize) {
    const batch = records.slice(i, i + batchSize);

    try {
      // Bulk create endpoint handles deduplication
      const { data } = await client.post('/contacts/bulk_create', {
        contacts: batch,
      });

      const newContacts = data.contacts ?? [];
      const existingContacts = data.existing_contacts ?? [];
      result.created += newContacts.length;
      result.existing += existingContacts.length;
      result.createdIds.push(...newContacts.map((c: any) => c.id));
    } catch (err: any) {
      // Fall back to individual creates
      for (const record of batch) {
        try {
          const { data } = await client.post('/contacts', record);
          result.created++;
          result.createdIds.push(data.contact.id);
        } catch (e: any) {
          result.failed++;
          result.errors.push({ record, error: e.response?.data?.message ?? e.message });
        }
      }
    }

    // Rate limit: 100 requests/min for contacts
    if (i + batchSize < records.length) {
      await new Promise((r) => setTimeout(r, 1000));
    }

    console.log(`Progress: ${Math.min(i + batchSize, records.length)}/${records.length}`);
  }

  return result;
}
```

### Step 4: Post-Migration Reconciliation
```typescript
async function reconcile(sourceRecords: Record<string, any>[]) {
  let matched = 0, missing = 0, mismatched = 0;

  for (const source of sourceRecords.slice(0, 100)) {  // Sample reconciliation
    const { data } = await client.post('/contacts/search', {
      q_keywords: source.email, per_page: 1,
    });

    const contact = data.contacts?.[0];
    if (!contact) { missing++; continue; }

    const nameMatch = contact.first_name === source.first_name && contact.last_name === source.last_name;
    if (nameMatch) matched++;
    else { mismatched++; console.warn(`Mismatch: ${source.email}`); }
  }

  console.log(`Reconciliation: ${matched} matched, ${missing} missing, ${mismatched} mismatched`);
  return { matched, missing, mismatched };
}
```

### Step 5: Rollback
```typescript
async function rollback(contactIds: string[]) {
  console.log(`Rolling back ${contactIds.length} contacts...`);
  let deleted = 0;

  for (let i = 0; i < contactIds.length; i += 50) {
    const batch = contactIds.slice(i, i + 50);
    for (const id of batch) {
      try { await client.delete(`/contacts/${id}`); deleted++; }
      catch (err: any) { console.error(`Failed: ${id}: ${err.message}`); }
    }
    await new Promise((r) => setTimeout(r, 500));
    console.log(`Rollback: ${Math.min(i + 50, contactIds.length)}/${contactIds.length}`);
  }

  console.log(`Rolled back ${deleted}/${contactIds.length} contacts`);
}
```

## Output
- Field mappings for Salesforce and HubSpot to Apollo Contacts API
- Pre-migration assessment with validation, duplicates, and missing fields
- Batch migration via `POST /contacts/bulk_create` (100 per call)
- Post-migration reconciliation sampling
- Rollback procedure deleting created contacts

## Error Handling
| Issue | Resolution |
|-------|------------|
| 403 on create | Contacts API requires master key |
| Bulk create fails | Falls back to individual `POST /contacts` calls |
| Duplicate contacts | Apollo's bulk_create handles dedup — returns `existing_contacts` |
| Field mapping error | Review source field names, check for case sensitivity |
| Rate limited | Increase delay between batches |

## Examples

### Full Migration Pipeline
```typescript
const assessment = await assess('./salesforce-export.csv', salesforceMap);
if (assessment.invalid > assessment.total * 0.1) {
  console.error('Too many invalid records (>10%). Clean data first.');
  process.exit(1);
}

const records = parseCsv('./salesforce-export.csv').map((r) => mapRecord(r, salesforceMap));
const result = await migrateBatch(records, 100);
console.log(`Created: ${result.created}, Existing: ${result.existing}, Failed: ${result.failed}`);

// Save contact IDs for potential rollback
fs.writeFileSync('migration-ids.json', JSON.stringify(result.createdIds));

await reconcile(records);
```

## Resources
- [Create a Contact](https://docs.apollo.io/reference/create-a-contact)
- [Bulk Create Contacts](https://docs.apollo.io/reference/bulk-create-contacts)
- [Search for Contacts](https://docs.apollo.io/reference/search-for-contacts)
- [Update a Contact](https://docs.apollo.io/reference/update-a-contact)

## Next Steps
After migration, verify data with `apollo-prod-checklist`.
