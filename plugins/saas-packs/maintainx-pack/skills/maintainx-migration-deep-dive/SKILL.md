---
name: maintainx-migration-deep-dive
description: |
  Execute complete platform migrations to or from MaintainX.
  Use when migrating from legacy CMMS systems, performing major re-platforming,
  or transitioning to MaintainX from spreadsheets or other tools.
  Trigger with phrases like "migrate to maintainx", "maintainx migration",
  "cmms migration", "switch to maintainx", "maintainx data migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Migration Deep Dive

## Current State
!`node --version 2>/dev/null || echo 'N/A'`

## Overview
Comprehensive guide for migrating to MaintainX from legacy CMMS systems (Maximo, UpKeep, Fiix), spreadsheets, or custom databases.

## Prerequisites
- MaintainX account with API access
- Access to source system data (CSV export, API, or database)
- Node.js 18+

## Migration Phases

```
Phase 1: Assess    →  Phase 2: Map    →  Phase 3: Migrate  →  Phase 4: Validate
(Audit source)       (Schema mapping)    (ETL + import)        (Verify + cutover)
```

## Instructions

### Step 1: Source System Assessment

```typescript
// scripts/assess-source.ts
import { parse } from 'csv-parse/sync';
import { readFileSync } from 'fs';

interface AssessmentReport {
  totalRecords: number;
  recordTypes: Record<string, number>;
  dataQuality: {
    missingFields: Record<string, number>;
    duplicates: number;
    invalidDates: number;
  };
}

function assessCSV(filePath: string, columns: string[]): AssessmentReport {
  const content = readFileSync(filePath, 'utf-8');
  const rows = parse(content, { columns: true, skip_empty_lines: true });

  const missing: Record<string, number> = {};
  const seen = new Set<string>();
  let duplicates = 0;
  let invalidDates = 0;

  for (const row of rows) {
    // Check missing fields
    for (const col of columns) {
      if (!row[col] || row[col].trim() === '') {
        missing[col] = (missing[col] || 0) + 1;
      }
    }

    // Check duplicates (by name/title)
    const key = row['Name'] || row['Title'] || row['name'];
    if (key && seen.has(key)) duplicates++;
    if (key) seen.add(key);

    // Check date formats
    for (const col of Object.keys(row)) {
      if (col.toLowerCase().includes('date') && row[col]) {
        if (isNaN(Date.parse(row[col]))) invalidDates++;
      }
    }
  }

  return {
    totalRecords: rows.length,
    recordTypes: { [filePath]: rows.length },
    dataQuality: { missingFields: missing, duplicates, invalidDates },
  };
}

// Run assessment
const report = assessCSV('legacy-work-orders.csv', ['Title', 'Priority', 'Status']);
console.log('=== Migration Assessment ===');
console.log(`Total records: ${report.totalRecords}`);
console.log('Missing fields:', report.dataQuality.missingFields);
console.log(`Duplicates: ${report.dataQuality.duplicates}`);
console.log(`Invalid dates: ${report.dataQuality.invalidDates}`);
```

### Step 2: Schema Mapping

```typescript
// src/migration/schema-map.ts

// Map legacy CMMS fields to MaintainX fields
interface FieldMapping {
  source: string;
  target: string;
  transform?: (value: any) => any;
}

const WORK_ORDER_MAP: FieldMapping[] = [
  { source: 'WO_Name', target: 'title' },
  { source: 'WO_Description', target: 'description' },
  {
    source: 'WO_Priority',
    target: 'priority',
    transform: (v: string) => {
      const map: Record<string, string> = {
        '1': 'HIGH', 'Critical': 'HIGH', 'Urgent': 'HIGH',
        '2': 'MEDIUM', 'Normal': 'MEDIUM', 'Standard': 'MEDIUM',
        '3': 'LOW', 'Low': 'LOW', 'Routine': 'LOW',
      };
      return map[v] || 'NONE';
    },
  },
  {
    source: 'WO_Status',
    target: 'status',
    transform: (v: string) => {
      const map: Record<string, string> = {
        'New': 'OPEN', 'Pending': 'OPEN',
        'Active': 'IN_PROGRESS', 'Working': 'IN_PROGRESS',
        'Waiting': 'ON_HOLD', 'Hold': 'ON_HOLD',
        'Done': 'COMPLETED', 'Finished': 'COMPLETED',
        'Archived': 'CLOSED', 'Cancelled': 'CLOSED',
      };
      return map[v] || 'OPEN';
    },
  },
  {
    source: 'WO_DueDate',
    target: 'dueDate',
    transform: (v: string) => v ? new Date(v).toISOString() : undefined,
  },
];

const ASSET_MAP: FieldMapping[] = [
  { source: 'Asset_Name', target: 'name' },
  { source: 'Asset_Description', target: 'description' },
  { source: 'Serial_Number', target: 'serialNumber' },
  { source: 'Model_Number', target: 'model' },
  { source: 'Manufacturer', target: 'manufacturer' },
];

function mapRecord(source: Record<string, any>, mappings: FieldMapping[]): Record<string, any> {
  const result: Record<string, any> = {};
  for (const mapping of mappings) {
    let value = source[mapping.source];
    if (value !== undefined && value !== '' && mapping.transform) {
      value = mapping.transform(value);
    }
    if (value !== undefined && value !== '') {
      result[mapping.target] = value;
    }
  }
  return result;
}
```

### Step 3: ETL Migration

```typescript
// src/migration/migrate.ts
import { parse } from 'csv-parse/sync';
import { readFileSync, writeFileSync } from 'fs';
import PQueue from 'p-queue';

interface MigrationResult {
  success: number;
  failed: number;
  errors: Array<{ record: any; error: string }>;
}

async function migrateWorkOrders(
  client: MaintainXClient,
  csvPath: string,
): Promise<MigrationResult> {
  const rows = parse(readFileSync(csvPath, 'utf-8'), { columns: true });
  const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 5 });
  const result: MigrationResult = { success: 0, failed: 0, errors: [] };

  console.log(`Migrating ${rows.length} work orders...`);

  const promises = rows.map((row: any, index: number) =>
    queue.add(async () => {
      try {
        const mapped = mapRecord(row, WORK_ORDER_MAP);
        if (!mapped.title) {
          mapped.title = `Migrated WO #${index + 1}`;
        }
        await client.createWorkOrder(mapped);
        result.success++;

        if (result.success % 50 === 0) {
          console.log(`  Progress: ${result.success}/${rows.length}`);
        }
      } catch (err: any) {
        result.failed++;
        result.errors.push({
          record: row,
          error: err.response?.data?.message || err.message,
        });
      }
    }),
  );

  await Promise.all(promises);

  console.log(`\n=== Migration Complete ===`);
  console.log(`Success: ${result.success} | Failed: ${result.failed}`);

  if (result.errors.length > 0) {
    writeFileSync(
      'migration-errors.json',
      JSON.stringify(result.errors, null, 2),
    );
    console.log('Errors saved to migration-errors.json');
  }

  return result;
}
```

### Step 4: Validation and Reconciliation

```typescript
// src/migration/validate.ts

async function validateMigration(
  client: MaintainXClient,
  sourceRows: any[],
): Promise<void> {
  console.log('=== Migration Validation ===');

  // Count comparison
  const allWOs = await paginate(
    (cursor) => client.getWorkOrders({ limit: 100, cursor }),
    'workOrders',
  );

  console.log(`Source records: ${sourceRows.length}`);
  console.log(`MaintainX work orders: ${allWOs.length}`);
  console.log(`Match: ${allWOs.length >= sourceRows.length ? 'YES' : 'NO - check migration-errors.json'}`);

  // Spot-check random samples
  const sampleSize = Math.min(10, allWOs.length);
  const samples = allWOs.sort(() => Math.random() - 0.5).slice(0, sampleSize);

  console.log(`\nSpot-checking ${sampleSize} random records:`);
  for (const wo of samples) {
    const checks = [
      wo.title ? 'title OK' : 'MISSING title',
      wo.priority ? 'priority OK' : 'MISSING priority',
      wo.status ? 'status OK' : 'MISSING status',
    ];
    console.log(`  #${wo.id}: ${checks.join(', ')}`);
  }
}
```

### Rollback Plan

```bash
#!/bin/bash
# rollback-migration.sh
# Delete all migrated records (use with extreme caution)

echo "WARNING: This will delete all work orders created during migration."
echo "Press Ctrl+C to cancel, Enter to continue."
read

# Tag migrated work orders with a search pattern
# Then delete by filtering
curl -s "https://api.getmaintainx.com/v1/workorders?limit=100" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  | jq -r '.workOrders[] | select(.title | startswith("Migrated")) | .id' \
  | while read id; do
    echo "Deleting WO #$id..."
    curl -s -X DELETE "https://api.getmaintainx.com/v1/workorders/$id" \
      -H "Authorization: Bearer $MAINTAINX_API_KEY"
    sleep 0.5  # Rate limiting
  done
```

## Output
- Source system assessment report (record counts, data quality issues)
- Schema mapping configuration (legacy fields to MaintainX fields)
- ETL migration with rate-limited batch imports
- Validation report comparing source and target counts
- Rollback script for emergency reversal

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request on import | Invalid field value after mapping | Fix transform function, re-run failed records |
| 429 during bulk import | Too many records too fast | Reduce PQueue concurrency to 2 |
| Duplicate records | Migration re-run without cleanup | Deduplicate by title or external ID |
| Missing relationships | Assets migrated after work orders | Migrate in order: Locations -> Assets -> Work Orders |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [MaintainX Import Guide](https://help.getmaintainx.com)
- [csv-parse](https://csv.js.org/parse/) -- CSV parsing for Node.js

## Next Steps
You have completed the MaintainX skill pack. For additional support, see the [MaintainX Help Center](https://help.getmaintainx.com).

## Examples

**Migrate from Excel spreadsheet**:

```typescript
import XLSX from 'xlsx';

const workbook = XLSX.readFile('maintenance-tracker.xlsx');
const sheet = workbook.Sheets[workbook.SheetNames[0]];
const rows = XLSX.utils.sheet_to_json(sheet);

for (const row of rows) {
  const mapped = mapRecord(row as Record<string, any>, WORK_ORDER_MAP);
  await client.createWorkOrder(mapped);
}
```

**Migrate locations first, then link assets**:

```typescript
// 1. Migrate locations
const locationIdMap = new Map<string, number>(); // legacy ID → MaintainX ID
for (const loc of legacyLocations) {
  const created = await client.request('POST', '/locations', { name: loc.name });
  locationIdMap.set(loc.legacyId, created.id);
}

// 2. Migrate assets with location links
for (const asset of legacyAssets) {
  const maintainxLocationId = locationIdMap.get(asset.legacyLocationId);
  await client.request('POST', '/assets', {
    name: asset.name,
    locationId: maintainxLocationId,
    serialNumber: asset.serial,
  });
}
```
