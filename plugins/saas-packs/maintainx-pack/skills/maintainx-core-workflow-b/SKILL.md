---
name: maintainx-core-workflow-b
description: |
  Execute MaintainX secondary workflow: Asset and Location management.
  Use when managing equipment assets, organizing locations/facilities,
  building asset hierarchies, and tracking equipment maintenance history.
  Trigger with phrases like "maintainx asset", "maintainx location",
  "equipment tracking", "asset management", "facility hierarchy".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Core Workflow B: Asset & Location Management

## Overview
Manage equipment assets and facility locations in MaintainX. Assets represent equipment that requires maintenance; locations organize your facilities into a manageable hierarchy.

## Prerequisites
- Completed `maintainx-install-auth` setup
- `MAINTAINX_API_KEY` environment variable configured
- MaintainX account with asset management permissions

## Instructions

### Step 1: Create a Location Hierarchy

```typescript
import { MaintainXClient } from './maintainx/client';

const client = new MaintainXClient();

// Create top-level facility
const { data: plant } = await client.request('POST', '/locations', {
  name: 'Manufacturing Plant - Austin',
  description: 'Main production facility',
  address: '1234 Industrial Blvd, Austin, TX 78701',
});

// Create sub-locations
const { data: floor } = await client.request('POST', '/locations', {
  name: 'Production Floor - Building A',
  parentId: plant.id,
  description: 'Primary manufacturing area with 12 production lines',
});

const { data: mechRoom } = await client.request('POST', '/locations', {
  name: 'Mechanical Room - B2',
  parentId: plant.id,
  description: 'Pumps, compressors, and HVAC equipment',
});

console.log(`Location hierarchy created: ${plant.id} → ${floor.id}, ${mechRoom.id}`);
```

### Step 2: Register Assets

```typescript
// Create an asset linked to a location
const { data: pump } = await client.request('POST', '/assets', {
  name: 'Centrifugal Pump #3',
  description: 'Grundfos CR 45-2, 15HP, installed 2023',
  locationId: mechRoom.id,
  serialNumber: 'GF-CR45-2-00891',
  model: 'CR 45-2',
  manufacturer: 'Grundfos',
});

const { data: conveyor } = await client.request('POST', '/assets', {
  name: 'Conveyor Belt - Line 7',
  description: 'Main assembly line conveyor, 120ft span',
  locationId: floor.id,
  serialNumber: 'DRV-CONV-7-2024',
  model: 'Heavy Duty BD-120',
  manufacturer: 'Dorner',
});

console.log(`Assets registered: Pump #${pump.id}, Conveyor #${conveyor.id}`);
```

### Step 3: List and Filter Assets

```typescript
// Get all assets at a location
const { data: locationAssets } = await client.getAssets({
  locationId: mechRoom.id,
  limit: 50,
});

for (const asset of locationAssets.assets) {
  console.log(`  ${asset.name} (SN: ${asset.serialNumber || 'N/A'})`);
}

// Paginate through all assets
async function getAllAssets() {
  const all = [];
  let cursor: string | undefined;
  do {
    const { data } = await client.getAssets({ limit: 100, cursor });
    all.push(...data.assets);
    cursor = data.cursor;
  } while (cursor);
  return all;
}

const allAssets = await getAllAssets();
console.log(`Total assets: ${allAssets.length}`);
```

### Step 4: Query Locations

```typescript
// Get all locations (flat list)
const { data: locations } = await client.getLocations({ limit: 100 });

// Build a tree structure from flat list
function buildTree(locations: any[]) {
  const map = new Map();
  const roots: any[] = [];

  for (const loc of locations) {
    map.set(loc.id, { ...loc, children: [] });
  }
  for (const loc of locations) {
    const node = map.get(loc.id);
    if (loc.parentId && map.has(loc.parentId)) {
      map.get(loc.parentId).children.push(node);
    } else {
      roots.push(node);
    }
  }
  return roots;
}

const tree = buildTree(locations.locations);
console.log(JSON.stringify(tree, null, 2));
```

### Step 5: Create Work Orders Linked to Assets

```typescript
// Corrective maintenance on a specific asset
const { data: wo } = await client.createWorkOrder({
  title: 'Centrifugal Pump #3 - Bearing Noise',
  description: 'Unusual grinding noise detected during morning inspection.',
  priority: 'HIGH',
  assetId: pump.id,
  locationId: mechRoom.id,
  categories: ['CORRECTIVE'],
});

console.log(`Work order #${wo.id} linked to asset ${pump.id}`);
```

## Output
- Location hierarchy created with parent-child relationships
- Assets registered with serial numbers, models, and location links
- Paginated asset and location queries
- Work orders linked to specific assets and locations

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 404 Not Found | Invalid asset or location ID | Verify ID exists with a GET request first |
| 400 Bad Request | Missing `name` field | Assets and locations require at least `name` |
| 409 Conflict | Duplicate serial number | Use unique serial numbers per asset |
| Empty results | Wrong filter or no data | Check query parameters, try without filters |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [Assets Help](https://help.getmaintainx.com/about-assets)
- [Locations Help](https://help.getmaintainx.com/about-locations)

## Next Steps
For troubleshooting common issues, see `maintainx-common-errors`.

## Examples

**Bulk import assets from CSV**:

```typescript
import { parse } from 'csv-parse/sync';
import { readFileSync } from 'fs';

const csv = readFileSync('assets.csv', 'utf-8');
const rows = parse(csv, { columns: true });

for (const row of rows) {
  await client.request('POST', '/assets', {
    name: row.name,
    serialNumber: row.serial_number,
    locationId: parseInt(row.location_id),
    model: row.model,
    manufacturer: row.manufacturer,
  });
  console.log(`Imported: ${row.name}`);
}
```

**Get maintenance history for an asset**:

```bash
# Fetch all work orders linked to a specific asset
curl -s "https://api.getmaintainx.com/v1/workorders?assetId=98765&limit=50" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  | jq '.workOrders[] | {id, title, status, completedAt}'
```
