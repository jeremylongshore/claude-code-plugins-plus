---
name: maintainx-data-handling
description: |
  Data synchronization, ETL patterns, and data management for MaintainX.
  Use when syncing data between MaintainX and other systems,
  building ETL pipelines, or managing data consistency.
  Trigger with phrases like "maintainx data sync", "maintainx etl",
  "maintainx export", "maintainx data migration", "maintainx data pipeline".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Data Handling

## Overview
Patterns for synchronizing, transforming, and exporting data between MaintainX and external systems (databases, data warehouses, ERPs).

## Prerequisites
- MaintainX API access configured
- Node.js 18+ with `axios`
- Target database or data warehouse available

## Instructions

### Step 1: Incremental Sync with Cursor Pagination

```typescript
import { MaintainXClient } from './client';
import { writeFileSync, existsSync, readFileSync } from 'fs';

const SYNC_STATE_FILE = '.maintainx-sync-state.json';

interface SyncState {
  lastSyncAt: string;
  workOrderCursor?: string;
  assetCursor?: string;
}

function loadSyncState(): SyncState {
  if (existsSync(SYNC_STATE_FILE)) {
    return JSON.parse(readFileSync(SYNC_STATE_FILE, 'utf-8'));
  }
  return { lastSyncAt: new Date(0).toISOString() };
}

function saveSyncState(state: SyncState) {
  writeFileSync(SYNC_STATE_FILE, JSON.stringify(state, null, 2));
}

async function incrementalSync(client: MaintainXClient) {
  const state = loadSyncState();
  const syncStart = new Date().toISOString();

  console.log(`Syncing changes since ${state.lastSyncAt}`);

  // Sync work orders updated since last run
  let cursor: string | undefined;
  let totalWOs = 0;
  do {
    const response = await client.getWorkOrders({
      updatedAtGte: state.lastSyncAt,
      limit: 100,
      cursor,
    });
    for (const wo of response.workOrders) {
      await upsertWorkOrder(wo);  // Your DB write function
      totalWOs++;
    }
    cursor = response.cursor ?? undefined;
  } while (cursor);

  // Sync assets updated since last run
  let assetCursor: string | undefined;
  let totalAssets = 0;
  do {
    const response = await client.getAssets({
      updatedAtGte: state.lastSyncAt,
      limit: 100,
      cursor: assetCursor,
    });
    for (const asset of response.assets) {
      await upsertAsset(asset);  // Your DB write function
      totalAssets++;
    }
    assetCursor = response.cursor ?? undefined;
  } while (assetCursor);

  saveSyncState({ lastSyncAt: syncStart });
  console.log(`Synced ${totalWOs} work orders, ${totalAssets} assets`);
}
```

### Step 2: Export to CSV

```typescript
import { createWriteStream } from 'fs';

async function exportWorkOrdersToCSV(client: MaintainXClient, outputPath: string) {
  const stream = createWriteStream(outputPath);
  stream.write('id,title,status,priority,assignee,asset,location,created_at,completed_at\n');

  let cursor: string | undefined;
  let count = 0;

  do {
    const response = await client.getWorkOrders({ limit: 100, cursor });
    for (const wo of response.workOrders) {
      const row = [
        wo.id,
        `"${(wo.title || '').replace(/"/g, '""')}"`,
        wo.status,
        wo.priority,
        wo.assignees?.map((a: any) => a.id).join(';') || '',
        wo.assetId || '',
        wo.locationId || '',
        wo.createdAt,
        wo.completedAt || '',
      ].join(',');
      stream.write(row + '\n');
      count++;
    }
    cursor = response.cursor ?? undefined;
  } while (cursor);

  stream.end();
  console.log(`Exported ${count} work orders to ${outputPath}`);
}

// Usage
await exportWorkOrdersToCSV(client, 'work-orders-export.csv');
```

### Step 3: Export to BigQuery

```typescript
import { BigQuery } from '@google-cloud/bigquery';

const bq = new BigQuery({ projectId: 'your-project' });
const dataset = bq.dataset('maintenance');
const table = dataset.table('work_orders');

async function syncToBigQuery(client: MaintainXClient) {
  let cursor: string | undefined;
  const batch: any[] = [];

  do {
    const response = await client.getWorkOrders({ limit: 100, cursor });
    for (const wo of response.workOrders) {
      batch.push({
        id: wo.id,
        title: wo.title,
        status: wo.status,
        priority: wo.priority,
        asset_id: wo.assetId,
        location_id: wo.locationId,
        created_at: wo.createdAt,
        completed_at: wo.completedAt,
        synced_at: new Date().toISOString(),
      });
    }
    cursor = response.cursor ?? undefined;
  } while (cursor);

  if (batch.length > 0) {
    await table.insert(batch);
    console.log(`Inserted ${batch.length} rows into BigQuery`);
  }
}
```

### Step 4: Data Reconciliation

```typescript
async function reconcile(client: MaintainXClient, localDb: any) {
  const remoteOrders = await paginate(
    (cursor) => client.getWorkOrders({ limit: 100, cursor }),
    'workOrders',
  );
  const localOrders = await localDb.query('SELECT id, updated_at FROM work_orders');

  const remoteMap = new Map(remoteOrders.map((wo: any) => [wo.id, wo.updatedAt]));
  const localMap = new Map(localOrders.map((row: any) => [row.id, row.updated_at]));

  const missing = remoteOrders.filter((wo: any) => !localMap.has(wo.id));
  const stale = remoteOrders.filter(
    (wo: any) => localMap.has(wo.id) && localMap.get(wo.id) < remoteMap.get(wo.id),
  );
  const orphaned = localOrders.filter((row: any) => !remoteMap.has(row.id));

  console.log(`Missing locally: ${missing.length}`);
  console.log(`Stale locally: ${stale.length}`);
  console.log(`Orphaned locally: ${orphaned.length}`);

  return { missing, stale, orphaned };
}
```

## Output
- Incremental sync with persistent cursor state
- CSV export of work orders with proper quoting
- BigQuery streaming insert pipeline
- Data reconciliation report (missing, stale, orphaned records)

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 Rate Limited | Too many requests during sync | Add delays between pages, use `p-queue` |
| Partial sync failure | Network error mid-pagination | Save cursor state, resume from last position |
| Duplicate rows in BigQuery | Re-running without dedup | Use `MERGE` or dedup on `(id, updated_at)` |
| Stale local data | Missed webhook or sync gap | Run full reconciliation, then incremental |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [BigQuery Node.js Client](https://cloud.google.com/bigquery/docs/reference/libraries)
- [csv-parse](https://csv.js.org/parse/) -- CSV parsing for imports

## Next Steps
For enterprise access control, see `maintainx-enterprise-rbac`.

## Examples

**Scheduled sync with cron**:

```typescript
// Run every 15 minutes via cron or node-schedule
import cron from 'node-cron';

cron.schedule('*/15 * * * *', async () => {
  console.log('Starting incremental sync...');
  await incrementalSync(new MaintainXClient());
});
```

**Import work orders from a legacy CMMS CSV**:

```typescript
import { parse } from 'csv-parse/sync';
import { readFileSync } from 'fs';

const rows = parse(readFileSync('legacy-export.csv'), { columns: true });
for (const row of rows) {
  await client.createWorkOrder({
    title: row['Work Order Name'],
    description: row['Description'],
    priority: row['Priority'].toUpperCase(),
    categories: [row['Type'].toUpperCase()],
  });
}
```
