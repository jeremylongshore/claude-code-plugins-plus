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
---
# Apollo Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Comprehensive guide for migrating contact and company data to Apollo.io from other CRMs (Salesforce, HubSpot) or CSV sources. Covers field mapping, phased migration, batch processing, validation, reconciliation, and rollback strategies using the Apollo REST API.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup
- Source CRM export in CSV or JSON format

## Instructions

### Step 1: Define Field Mappings
```typescript
// src/migration/field-map.ts
interface FieldMapping {
  source: string;        // field name in source CRM
  target: string;        // Apollo API field name
  transform?: (value: any) => any;
  required: boolean;
}

// Salesforce → Apollo field mappings
const salesforceToApollo: FieldMapping[] = [
  { source: 'FirstName', target: 'first_name', required: true },
  { source: 'LastName', target: 'last_name', required: true },
  { source: 'Email', target: 'email', required: true },
  { source: 'Title', target: 'title', required: false },
  { source: 'Phone', target: 'phone_number', required: false },
  { source: 'Company', target: 'organization_name', required: false },
  {
    source: 'Website',
    target: 'domain',
    required: false,
    transform: (url: string) => new URL(url).hostname.replace('www.', ''),
  },
];

// HubSpot → Apollo field mappings
const hubspotToApollo: FieldMapping[] = [
  { source: 'firstname', target: 'first_name', required: true },
  { source: 'lastname', target: 'last_name', required: true },
  { source: 'email', target: 'email', required: true },
  { source: 'jobtitle', target: 'title', required: false },
  { source: 'phone', target: 'phone_number', required: false },
  { source: 'company', target: 'organization_name', required: false },
  { source: 'website', target: 'domain', required: false,
    transform: (url: string) => url?.replace(/^https?:\/\/(www\.)?/, '').replace(/\/.*/, ''),
  },
];

function mapRecord(record: Record<string, any>, mappings: FieldMapping[]): Record<string, any> {
  const mapped: Record<string, any> = {};
  for (const m of mappings) {
    let value = record[m.source];
    if (m.required && !value) throw new Error(`Missing required field: ${m.source}`);
    if (value && m.transform) value = m.transform(value);
    if (value) mapped[m.target] = value;
  }
  return mapped;
}
```

### Step 2: Run Pre-Migration Assessment
```typescript
// src/migration/assessment.ts
import fs from 'fs';
import { parse } from 'csv-parse/sync';

async function assessMigration(csvPath: string, mappings: FieldMapping[]) {
  const raw = fs.readFileSync(csvPath, 'utf-8');
  const records = parse(raw, { columns: true, skip_empty_lines: true });

  const assessment = {
    totalRecords: records.length,
    validRecords: 0,
    invalidRecords: 0,
    missingFields: {} as Record<string, number>,
    duplicateEmails: 0,
    sampleErrors: [] as string[],
  };

  const emails = new Set<string>();

  for (const record of records) {
    try {
      mapRecord(record, mappings);
      const email = record.Email ?? record.email;
      if (emails.has(email)) {
        assessment.duplicateEmails++;
      } else {
        emails.add(email);
      }
      assessment.validRecords++;
    } catch (err: any) {
      assessment.invalidRecords++;
      const field = err.message.replace('Missing required field: ', '');
      assessment.missingFields[field] = (assessment.missingFields[field] ?? 0) + 1;
      if (assessment.sampleErrors.length < 5) {
        assessment.sampleErrors.push(err.message);
      }
    }
  }

  console.log('=== Migration Assessment ===');
  console.log(`Total:      ${assessment.totalRecords}`);
  console.log(`Valid:      ${assessment.validRecords}`);
  console.log(`Invalid:    ${assessment.invalidRecords}`);
  console.log(`Duplicates: ${assessment.duplicateEmails}`);
  console.log(`Missing:    ${JSON.stringify(assessment.missingFields)}`);
  return assessment;
}
```

### Step 3: Implement Batch Migration Worker
```typescript
// src/migration/batch-worker.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  params: { api_key: process.env.APOLLO_API_KEY },
  headers: { 'Content-Type': 'application/json' },
});

interface MigrationResult {
  total: number;
  succeeded: number;
  failed: number;
  errors: Array<{ record: any; error: string }>;
}

async function migrateBatch(
  records: Record<string, any>[],
  batchSize: number = 10,
  delayMs: number = 1000,
): Promise<MigrationResult> {
  const result: MigrationResult = { total: records.length, succeeded: 0, failed: 0, errors: [] };

  for (let i = 0; i < records.length; i += batchSize) {
    const batch = records.slice(i, i + batchSize);

    for (const record of batch) {
      try {
        // Check if contact exists first
        const { data: searchData } = await client.post('/people/search', {
          q_keywords: record.email,
          per_page: 1,
        });

        if (searchData.people?.length > 0) {
          // Update existing contact
          await client.put(`/contacts/${searchData.people[0].id}`, record);
        } else {
          // Create new contact
          await client.post('/contacts', record);
        }
        result.succeeded++;
      } catch (err: any) {
        result.failed++;
        result.errors.push({
          record,
          error: err.response?.data?.message ?? err.message,
        });
      }
    }

    // Rate limit pause between batches
    if (i + batchSize < records.length) {
      await new Promise((r) => setTimeout(r, delayMs));
    }

    // Progress update
    console.log(`Progress: ${Math.min(i + batchSize, records.length)}/${records.length}`);
  }

  return result;
}
```

### Step 4: Validate and Reconcile
```typescript
// src/migration/reconciliation.ts
async function reconcile(
  sourceRecords: Record<string, any>[],
): Promise<{ matched: number; missing: number; mismatched: number }> {
  let matched = 0, missing = 0, mismatched = 0;

  for (const source of sourceRecords) {
    const { data } = await client.post('/people/search', {
      q_keywords: source.email,
      per_page: 1,
    });

    const apolloContact = data.people?.[0];
    if (!apolloContact) {
      missing++;
      console.warn(`Missing in Apollo: ${source.email}`);
      continue;
    }

    // Compare key fields
    const nameMatch = apolloContact.name === `${source.first_name} ${source.last_name}`;
    const titleMatch = !source.title || apolloContact.title === source.title;

    if (nameMatch && titleMatch) {
      matched++;
    } else {
      mismatched++;
      console.warn(`Mismatch: ${source.email} — name: ${nameMatch}, title: ${titleMatch}`);
    }
  }

  console.log(`Reconciliation: ${matched} matched, ${missing} missing, ${mismatched} mismatched`);
  return { matched, missing, mismatched };
}
```

### Step 5: Implement Rollback Procedures
```typescript
// src/migration/rollback.ts
async function rollbackMigration(
  migratedContactIds: string[],
  batchSize: number = 50,
) {
  console.log(`Rolling back ${migratedContactIds.length} contacts...`);

  for (let i = 0; i < migratedContactIds.length; i += batchSize) {
    const batch = migratedContactIds.slice(i, i + batchSize);

    for (const contactId of batch) {
      try {
        await client.delete(`/contacts/${contactId}`);
      } catch (err: any) {
        console.error(`Failed to delete ${contactId}: ${err.message}`);
      }
    }

    await new Promise((r) => setTimeout(r, 500));
    console.log(`Rollback progress: ${Math.min(i + batchSize, migratedContactIds.length)}/${migratedContactIds.length}`);
  }
}
```

## Output
- Field mapping configs for Salesforce and HubSpot to Apollo
- Pre-migration assessment with validation stats, duplicates, and missing fields
- Batch migration worker with upsert logic and rate limiting
- Post-migration reconciliation comparing source and Apollo data
- Rollback procedure for removing migrated contacts

## Error Handling
| Issue | Resolution |
|-------|------------|
| Field mapping error | Review mapping config, check source field names |
| Batch failure | Retry with smaller batch size (5 instead of 10) |
| Validation mismatch | Run reconciliation, re-migrate mismatched records |
| Rollback needed | Execute `rollbackMigration` with saved contact IDs |

## Examples

### Full Migration Pipeline
```typescript
import { salesforceToApollo, mapRecord } from './migration/field-map';
import { assessMigration } from './migration/assessment';
import { migrateBatch } from './migration/batch-worker';
import { reconcile } from './migration/reconciliation';

// 1. Assess
const assessment = await assessMigration('./export.csv', salesforceToApollo);
if (assessment.invalidRecords > assessment.totalRecords * 0.1) {
  console.error('Too many invalid records (>10%). Fix data before migrating.');
  process.exit(1);
}

// 2. Map and migrate
const records = parseCsv('./export.csv').map((r) => mapRecord(r, salesforceToApollo));
const result = await migrateBatch(records, 10, 1000);
console.log(`Migrated: ${result.succeeded}/${result.total}, Errors: ${result.failed}`);

// 3. Reconcile
await reconcile(records);
```

## Resources
- [Apollo Contacts API](https://apolloio.github.io/apollo-api-docs/#contacts)
- [Salesforce Data Export](https://help.salesforce.com/s/articleView?id=sf.exporting_data.htm)
- [HubSpot Export Guide](https://knowledge.hubspot.com/crm-setup/export-contacts-companies-deals-or-tickets)

## Next Steps
After migration, verify data with `apollo-prod-checklist`.
