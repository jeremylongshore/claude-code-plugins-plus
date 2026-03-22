---
name: salesforce-migration-deep-dive
description: |
  Execute Salesforce data migrations using Bulk API, Data Loader, and ETL patterns.
  Use when migrating data to/from Salesforce, performing org-to-org migrations,
  or re-platforming CRM data into Salesforce.
  Trigger with phrases like "migrate to salesforce", "salesforce data migration",
  "salesforce import data", "salesforce ETL", "CRM migration to salesforce".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(sf:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Migration Deep Dive

## Overview
Comprehensive guide for migrating data to/from Salesforce: ETL patterns using Bulk API 2.0, data mapping between CRM schemas, record relationship preservation, and validation.

## Prerequisites
- Source and target Salesforce orgs (or external CRM)
- jsforce with Bulk API 2.0 access
- Understanding of sObject relationships and External IDs
- Staging sandbox for dry runs

## Migration Types

| Type | Complexity | Duration | Tool |
|------|-----------|----------|------|
| CSV import (< 50K records) | Low | Hours | Data Import Wizard / Bulk API |
| CRM-to-Salesforce | Medium | Weeks | Custom ETL with jsforce |
| Org-to-org migration | Medium | Weeks | SFDX + Bulk API |
| Full re-platform | High | Months | Custom ETL + change management |

## Instructions

### Step 1: Data Assessment

```typescript
const conn = await getConnection();

// Count records per object
const objectCounts = await Promise.all(
  ['Account', 'Contact', 'Lead', 'Opportunity', 'Case'].map(async (obj) => {
    const result = await conn.query(`SELECT COUNT(Id) total FROM ${obj}`);
    return { object: obj, count: result.records[0].total };
  })
);

console.table(objectCounts);
// Account:      15,234
// Contact:      45,678
// Lead:         23,456
// Opportunity:  8,901
// Case:         67,890

// Check data storage limits
const limits = await conn.request('/services/data/v59.0/limits/');
console.log(`Data storage: ${limits.DataStorageMB.Max - limits.DataStorageMB.Remaining}/${limits.DataStorageMB.Max} MB`);
```

### Step 2: Schema Mapping

```typescript
// Map source fields to Salesforce sObject fields
interface FieldMapping {
  source: string;
  target: string;
  transform?: (value: any) => any;
  required: boolean;
}

const accountMappings: FieldMapping[] = [
  { source: 'company_name', target: 'Name', required: true },
  { source: 'industry_code', target: 'Industry', required: false,
    transform: (code) => INDUSTRY_MAP[code] || 'Other' },
  { source: 'annual_rev', target: 'AnnualRevenue', required: false,
    transform: (v) => typeof v === 'string' ? parseFloat(v.replace(/[$,]/g, '')) : v },
  { source: 'website_url', target: 'Website', required: false },
  { source: 'employee_count', target: 'NumberOfEmployees', required: false },
  { source: 'external_id', target: 'External_ID__c', required: true },
];

function transformRecord(
  source: Record<string, any>,
  mappings: FieldMapping[]
): Record<string, any> {
  const target: Record<string, any> = {};
  for (const mapping of mappings) {
    let value = source[mapping.source];
    if (value === undefined || value === null) {
      if (mapping.required) throw new Error(`Missing required field: ${mapping.source}`);
      continue;
    }
    if (mapping.transform) value = mapping.transform(value);
    target[mapping.target] = value;
  }
  return target;
}
```

### Step 3: Migration Order (Respecting Relationships)

```
Migration order matters! Parent objects must be loaded before children.

1. Account          (no dependencies)
2. Contact          (depends on Account via AccountId)
3. Opportunity      (depends on Account via AccountId)
4. OpportunityContactRole (depends on Opportunity + Contact)
5. Case             (depends on Account + Contact)
6. Task / Event     (depends on Contact via WhoId, Account via WhatId)

Use External IDs to resolve relationships without knowing Salesforce IDs:
- Create External_ID__c on Account, Contact, Opportunity
- Use external ID references in child records
```

### Step 4: Bulk Migration with External ID Relationships

```typescript
import { getConnection } from './salesforce/connection';
import fs from 'fs';

const conn = await getConnection();

// Step 4a: Load Accounts first
const accountCsv = `Name,Industry,External_ID__c
Acme Corp,Technology,EXT-ACME-001
Globex Inc,Manufacturing,EXT-GLOBEX-002
Initech LLC,Consulting,EXT-INITECH-003`;

const accountResults = await conn.bulk2.loadAndWaitForResults({
  object: 'Account',
  operation: 'upsert',
  externalIdFieldName: 'External_ID__c',
  input: accountCsv,
});
console.log(`Accounts: ${accountResults.successfulResults.length} success, ${accountResults.failedResults.length} failed`);

// Step 4b: Load Contacts with Account relationship via External ID
const contactCsv = `FirstName,LastName,Email,Account.External_ID__c,External_ID__c
Jane,Smith,jane@acme.com,EXT-ACME-001,EXT-CONTACT-001
John,Doe,john@globex.com,EXT-GLOBEX-002,EXT-CONTACT-002`;

const contactResults = await conn.bulk2.loadAndWaitForResults({
  object: 'Contact',
  operation: 'upsert',
  externalIdFieldName: 'External_ID__c',
  input: contactCsv,
});
// Account.External_ID__c resolves to the correct AccountId automatically!
```

### Step 5: Validation

```typescript
async function validateMigration(
  sourceCount: number,
  objectType: string
): Promise<{ passed: boolean; details: string }> {
  const conn = await getConnection();

  // Count migrated records
  const result = await conn.query(
    `SELECT COUNT(Id) total FROM ${objectType} WHERE External_ID__c != null`
  );
  const targetCount = result.records[0].total;

  // Check for orphaned relationships
  let orphans = 0;
  if (objectType === 'Contact') {
    const orphanResult = await conn.query(
      `SELECT COUNT(Id) total FROM Contact WHERE AccountId = null AND External_ID__c != null`
    );
    orphans = orphanResult.records[0].total;
  }

  const passed = targetCount === sourceCount && orphans === 0;
  return {
    passed,
    details: `Source: ${sourceCount}, Target: ${targetCount}, Orphans: ${orphans}`,
  };
}
```

### Step 6: Rollback Plan

```typescript
// Delete migrated records using External ID marker
async function rollbackMigration(objectType: string): Promise<void> {
  const conn = await getConnection();

  // Query all migrated records (identified by External_ID__c)
  const records = await conn.query(
    `SELECT Id FROM ${objectType} WHERE External_ID__c != null`
  );

  // Delete in reverse order (children first)
  const ids = records.records.map((r: any) => r.Id);
  for (let i = 0; i < ids.length; i += 200) {
    const batch = ids.slice(i, i + 200);
    await conn.sobject(objectType).destroy(batch);
  }

  console.log(`Rolled back ${ids.length} ${objectType} records`);
}
```

## Output
- Data assessment with record counts and storage usage
- Field mapping layer transforming source to Salesforce schema
- Bulk API migration respecting parent-child relationships
- External ID-based relationship resolution (no hardcoded IDs)
- Validation and rollback procedures

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `DUPLICATE_VALUE` on External_ID__c | Re-running migration | Use upsert instead of insert |
| `INVALID_CROSS_REFERENCE_KEY` | Parent record not found | Verify parent loaded first, check External ID values |
| `STORAGE_LIMIT_EXCEEDED` | Org storage full | Delete test data or upgrade storage |
| Bulk job timeout | Very large dataset | Split into smaller jobs (< 100M records) |
| Field mapping errors | Source schema mismatch | Validate transform functions with sample data first |

## Resources
- [Bulk API 2.0](https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/bulk_api_2_0.htm)
- [External ID Fields](https://help.salesforce.com/s/articleView?id=sf.fields_about_external_ids.htm)
- [Data Import Best Practices](https://help.salesforce.com/s/articleView?id=sf.importing_data.htm)
- [Salesforce Data Loader](https://developer.salesforce.com/docs/atlas.en-us.dataLoader.meta/dataLoader/)

## Next Steps
For advanced troubleshooting, see `salesforce-advanced-troubleshooting`.
