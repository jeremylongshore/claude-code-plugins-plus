---
name: hubspot-migration-deep-dive
description: |
  Execute CRM data migration to HubSpot with batch imports and validation.
  Use when migrating from Salesforce/Pipedrive/spreadsheets to HubSpot,
  performing bulk data imports, or re-platforming to HubSpot CRM.
  Trigger with phrases like "migrate to hubspot", "hubspot data import",
  "salesforce to hubspot", "hubspot migration", "bulk import hubspot".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Migration Deep Dive

## Overview

Comprehensive guide for migrating CRM data into HubSpot, including data mapping, batch imports via API, validation, and rollback procedures.

## Prerequisites

- Source CRM data exported (CSV or API access)
- HubSpot account with required scopes
- Custom properties created in HubSpot for non-default fields

## Instructions

### Step 1: Data Inventory and Mapping

```typescript
// Map source CRM fields to HubSpot properties
interface FieldMapping {
  sourceField: string;
  hubspotProperty: string;
  transform?: (value: string) => string;
  required: boolean;
}

const contactFieldMap: FieldMapping[] = [
  { sourceField: 'Email', hubspotProperty: 'email', required: true },
  { sourceField: 'First Name', hubspotProperty: 'firstname', required: false },
  { sourceField: 'Last Name', hubspotProperty: 'lastname', required: false },
  { sourceField: 'Phone', hubspotProperty: 'phone', required: false },
  { sourceField: 'Company', hubspotProperty: 'company', required: false },
  {
    sourceField: 'Lead Status',
    hubspotProperty: 'lifecyclestage',
    transform: (val) => {
      // Map source values to HubSpot lifecycle stages
      const map: Record<string, string> = {
        'New': 'lead',
        'Qualified': 'marketingqualifiedlead',
        'Won': 'customer',
      };
      return map[val] || 'lead';
    },
    required: false,
  },
];

function mapRecord(
  source: Record<string, string>,
  fieldMap: FieldMapping[]
): Record<string, string> {
  const mapped: Record<string, string> = {};
  for (const field of fieldMap) {
    const value = source[field.sourceField];
    if (value !== undefined && value !== '') {
      mapped[field.hubspotProperty] = field.transform ? field.transform(value) : value;
    } else if (field.required) {
      throw new Error(`Missing required field: ${field.sourceField}`);
    }
  }
  return mapped;
}
```

### Step 2: Create Custom Properties Before Import

```typescript
import * as hubspot from '@hubspot/api-client';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
});

// Create custom properties that don't exist in HubSpot
async function ensureCustomProperties(objectType: string) {
  const customProps = [
    {
      name: 'source_crm_id',
      label: 'Source CRM ID',
      type: 'string',
      fieldType: 'text',
      groupName: 'contactinformation',
      description: 'Original record ID from source CRM',
    },
    {
      name: 'migration_date',
      label: 'Migration Date',
      type: 'date',
      fieldType: 'date',
      groupName: 'contactinformation',
      description: 'Date record was migrated to HubSpot',
    },
  ];

  for (const prop of customProps) {
    try {
      // POST /crm/v3/properties/{objectType}
      await client.crm.properties.coreApi.create(objectType, prop);
      console.log(`Created property: ${prop.name}`);
    } catch (error: any) {
      if (error?.body?.category === 'DUPLICATE_PROPERTY') {
        console.log(`Property already exists: ${prop.name}`);
      } else {
        throw error;
      }
    }
  }
}
```

### Step 3: Batch Import with Progress Tracking

```typescript
interface MigrationResult {
  total: number;
  created: number;
  updated: number;
  errors: Array<{ record: any; error: string }>;
  durationMs: number;
}

async function migrateContacts(
  records: Record<string, string>[],
  fieldMap: FieldMapping[]
): Promise<MigrationResult> {
  const start = Date.now();
  const result: MigrationResult = {
    total: records.length,
    created: 0,
    updated: 0,
    errors: [],
    durationMs: 0,
  };

  // Process in batches of 100 (HubSpot batch limit)
  const batchSize = 100;
  for (let i = 0; i < records.length; i += batchSize) {
    const batch = records.slice(i, i + batchSize);
    const mapped = [];

    for (const record of batch) {
      try {
        const properties = mapRecord(record, fieldMap);
        properties.migration_date = new Date().toISOString().split('T')[0];
        properties.source_crm_id = record.Id || record.id || '';
        mapped.push({ properties });
      } catch (error: any) {
        result.errors.push({ record, error: error.message });
      }
    }

    if (mapped.length === 0) continue;

    try {
      // Use batch upsert to handle existing contacts
      // POST /crm/v3/objects/contacts/batch/upsert
      const response = await client.apiRequest({
        method: 'POST',
        path: '/crm/v3/objects/contacts/batch/upsert',
        body: {
          inputs: mapped.map(m => ({
            properties: m.properties,
            idProperty: 'email',
            id: m.properties.email,
          })),
        },
      });

      const data = await response.json();
      result.created += data.results?.length || 0;
    } catch (error: any) {
      // On batch failure, try individual records
      for (const item of mapped) {
        try {
          await client.crm.contacts.basicApi.create({
            properties: item.properties,
            associations: [],
          });
          result.created++;
        } catch (err: any) {
          if (err?.body?.category === 'CONFLICT') {
            // Contact exists, update instead
            const existing = await client.crm.contacts.searchApi.doSearch({
              filterGroups: [{
                filters: [{ propertyName: 'email', operator: 'EQ', value: item.properties.email }],
              }],
              properties: ['email'], limit: 1, after: 0, sorts: [],
            });
            if (existing.results.length > 0) {
              await client.crm.contacts.basicApi.update(existing.results[0].id, {
                properties: item.properties,
              });
              result.updated++;
            }
          } else {
            result.errors.push({ record: item.properties, error: err.message });
          }
        }
      }
    }

    // Progress logging
    const progress = Math.min(i + batchSize, records.length);
    console.log(`Progress: ${progress}/${records.length} ` +
      `(${result.created} created, ${result.updated} updated, ${result.errors.length} errors)`);

    // Rate limit: max 10 requests/second
    await new Promise(r => setTimeout(r, 200));
  }

  result.durationMs = Date.now() - start;
  return result;
}
```

### Step 4: Migrate Deals with Associations

```typescript
async function migrateDeals(
  deals: any[],
  contactEmailToId: Map<string, string>
): Promise<MigrationResult> {
  const result: MigrationResult = {
    total: deals.length, created: 0, updated: 0, errors: [], durationMs: 0,
  };
  const start = Date.now();

  // Get pipeline stages
  const pipelines = await client.crm.pipelines.pipelinesApi.getAll('deals');
  const defaultPipeline = pipelines.results[0];

  for (const deal of deals) {
    try {
      const associations = [];

      // Associate with contact if we have a mapping
      if (deal.contactEmail && contactEmailToId.has(deal.contactEmail)) {
        associations.push({
          to: { id: contactEmailToId.get(deal.contactEmail)! },
          types: [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 3 }],
        });
      }

      await client.crm.deals.basicApi.create({
        properties: {
          dealname: deal.name,
          amount: String(deal.amount || 0),
          pipeline: defaultPipeline.id,
          dealstage: defaultPipeline.stages[0].id,
          closedate: deal.closeDate || new Date().toISOString(),
          source_crm_id: deal.id || '',
        },
        associations,
      });
      result.created++;
    } catch (error: any) {
      result.errors.push({ record: deal, error: error.message });
    }
  }

  result.durationMs = Date.now() - start;
  return result;
}
```

### Step 5: Post-Migration Validation

```typescript
async function validateMigration(
  expectedCounts: { contacts: number; deals: number }
): Promise<{ valid: boolean; checks: any[] }> {
  const checks = [];

  // Count contacts
  const contacts = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [{
      filters: [{ propertyName: 'migration_date', operator: 'HAS_PROPERTY', value: '' }],
    }],
    properties: ['email'], limit: 1, after: 0, sorts: [],
  });
  checks.push({
    check: 'Contact count',
    expected: expectedCounts.contacts,
    actual: contacts.total,
    passed: contacts.total >= expectedCounts.contacts * 0.95, // 95% threshold
  });

  // Check for required fields
  const missingEmail = await client.crm.contacts.searchApi.doSearch({
    filterGroups: [{
      filters: [
        { propertyName: 'migration_date', operator: 'HAS_PROPERTY', value: '' },
        { propertyName: 'email', operator: 'NOT_HAS_PROPERTY', value: '' },
      ],
    }],
    properties: ['firstname'], limit: 1, after: 0, sorts: [],
  });
  checks.push({
    check: 'Contacts with email',
    missing: missingEmail.total,
    passed: missingEmail.total === 0,
  });

  return {
    valid: checks.every(c => c.passed),
    checks,
  };
}
```

## Output

- Field mapping from source CRM to HubSpot properties
- Custom properties created before import
- Batch upsert with progress tracking and error recovery
- Deal migration with contact associations
- Post-migration validation with threshold checks

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `PROPERTY_DOESNT_EXIST` | Custom property not created | Run `ensureCustomProperties` first |
| `409 Conflict` | Contact email already exists | Use batch upsert instead of batch create |
| Batch partial failure | Some records invalid | Fall back to individual creates |
| Association failure | Contact not yet created | Import contacts before deals |

## Resources

- [HubSpot Import API](https://developers.hubspot.com/docs/guides/api/crm/imports)
- [Batch Operations Guide](https://developers.hubspot.com/docs/guides/api/crm/understanding-the-crm)
- [Custom Properties API](https://developers.hubspot.com/docs/guides/api/crm/properties)

## Next Steps

For advanced troubleshooting, see `hubspot-advanced-troubleshooting`.
