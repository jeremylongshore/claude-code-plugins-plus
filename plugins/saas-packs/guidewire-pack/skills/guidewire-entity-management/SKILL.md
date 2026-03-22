---
name: guidewire-entity-management
description: |
  Execute Guidewire primary workflow: Domain Entity Management.
  Use when creating and managing domain-specific records via API,
  automating data entry from external sources, or building custom workflows on top of domain data.
  Trigger with phrases like "guidewire manage entities",
  "create or update domain entities with guidewire".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, guidewire]
---

# Guidewire Domain Entity Management

## Overview
Create, update, and manage domain-specific entities through the API.
This is the primary workflow — CRUD on the core business objects.


## Prerequisites
- Completed `guidewire-install-auth` setup

- Understanding of Guidewire core concepts

- Valid API credentials configured

## Instructions

### Step 1: List and Filter Entities
```typescript
const entities = await client.entities.list({
  filter: { status: 'active', type: 'primary' },
  sort: { field: 'updated_at', direction: 'desc' },
  limit: 50,
});
console.log(`Found ${entities.total} active entities`);

```

### Step 2: Create or Update
```typescript
const entity = await client.entities.upsert({
  externalId: record.id,
  name: record.name,
  type: record.type,
  metadata: record.properties,
  status: 'active',
});
console.log(`Entity ${entity.id}: ${entity.name} (${entity.status})`);

```

### Step 3: Trigger Workflow
```typescript
// Trigger domain-specific workflow on the entity
const workflow = await client.workflows.trigger({
  entityId: entity.id,
  workflow: 'review-and-approve',
  assignee: manager.id,
});
console.log(`Workflow ${workflow.id} started — awaiting approval`);

```

## Output
- Completed Domain Entity Management execution

- Expected results from Guidewire API

- Success confirmation or error details

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Validation Error | Entity data doesn't match the domain schema or business rules | Check required fields and validation rules. Get schema from /schema endpoint. |
| Permission Denied | API user lacks required role for this operation | Check user roles. Enterprise APIs often require admin or domain-specific roles. |

## Examples

### Complete Workflow
```typescript
const client = new EnterpriseClient({ apiKey: process.env.API_KEY });

async function syncRecords(source: ExternalRecord[]) {
  const results = { created: 0, updated: 0, failed: 0 };
  for (const record of source) {
    try {
      await client.entities.upsert({
        externalId: record.id,
        ...mapToSchema(record),
      });
      results.created++;
    } catch (err) {
      results.failed++;
      console.error(`Failed: ${record.id} — ${err.message}`);
    }
  }
  return results;
}

```

### Common Variations
- **Bulk import**: Use batch API for large data migrations
- **Webhook sync**: Real-time sync via entity change webhooks
- **Approval flows**: Trigger review workflows on entity creation/update


## Resources
- [Guidewire Documentation](https://docs.guidewire.com)
- [Guidewire API Reference](https://docs.guidewire.com/api)

## Next Steps
For secondary workflow, see `guidewire-data-sync`.