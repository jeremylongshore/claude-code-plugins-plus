---
name: procore-data-sync
description: |
  Execute Procore secondary workflow: Integration & Data Sync.
  Use when syncing records between systems on a schedule,
  or building real-time event-driven integrations.
  Trigger with phrases like "procore sync data",
  "sync between systems with procore".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, procore]
---

# Procore Integration & Data Sync

## Overview
Sync data between the enterprise platform and other systems (ERP, accounting, HR).
The glue workflow that connects vertical SaaS to the rest of the tech stack.


## Prerequisites
- Completed `procore-install-auth` setup
- Familiarity with `procore-entity-management`
- Valid API credentials configured

## Instructions

### Step 1: Fetch Changes Since Last Sync
```typescript
const changes = await client.entities.list({
  filter: { updated_after: lastSyncTimestamp },
  sort: { field: 'updated_at', direction: 'asc' },
});
console.log(`${changes.total} records changed since last sync`);

```

### Step 2: Transform and Map
```typescript
const mapped = changes.data.map(entity => ({
  externalId: entity.id,
  name: entity.name,
  ...mapToTargetSchema(entity),
}));

```

### Step 3: Write to Target System
```typescript
const results = await targetSystem.batchUpsert(mapped);
console.log(`Synced: ${results.success} success, ${results.failed} failed`);
// Update sync cursor
await saveSyncCursor(changes.data[changes.data.length - 1].updated_at);

```

## Output
- Completed Integration & Data Sync execution

- Results from Procore API

- Success confirmation or error details

## Error Handling
| Aspect | Domain Entity Management | Integration & Data Sync |
|--------|------------|------------|
| Use Case | creating and managing domain-specific records via API | syncing records between systems on a schedule |
| Complexity | Medium | Medium-High |
| Performance | Standard | Depends on batch size and target system |

## Examples

### Complete Workflow
```typescript
async function incrementalSync() {
  const cursor = await loadSyncCursor();
  const changes = await client.entities.list({ filter: { updated_after: cursor } });
  for (const batch of chunk(changes.data, 100)) {
    await targetSystem.batchUpsert(batch.map(mapToTargetSchema));
  }
  await saveSyncCursor(new Date().toISOString());
  return changes.total;
}

```

### Error Recovery
```typescript
try {
  await targetSystem.batchUpsert(records);
} catch (err) {
  if (err.code === 'partial_failure') {
    console.error(`${err.failedRecords.length} records failed`);
    // Retry failed records individually
    for (const failed of err.failedRecords) {
      await retryQueue.push(failed);
    }
  }
  throw err;
}

```

## Resources
- [Procore Documentation](https://docs.procore.com)
- [Procore API Reference](https://docs.procore.com/api)

## Next Steps
For common errors, see `procore-common-errors`.