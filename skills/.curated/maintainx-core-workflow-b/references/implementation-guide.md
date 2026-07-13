# MaintainX Core Workflow B: Asset & Location Management - Implementation Guide

> Full implementation details and code examples for the `maintainx-core-workflow-b` skill.

# MaintainX Core Workflow B: Asset & Location Management

## Overview

Manage equipment assets and locations in MaintainX. Assets represent equipment that requires maintenance; locations organize your facilities.

## Prerequisites

- Completed `maintainx-install-auth` setup
- Understanding of asset hierarchy concepts
- MaintainX account with asset management permissions

## Asset Hierarchy Model

```
Organization
├── Location: Main Plant
│   ├── Sub-Location: Building A
│   │   ├── Asset: HVAC Unit A1
│   │   │   └── Sub-Asset: Compressor
│   │   └── Asset: Conveyor Line 1
│   └── Sub-Location: Building B
│       └── Asset: Boiler System
└── Location: Warehouse
    └── Asset: Forklift Fleet
        ├── Sub-Asset: Forklift #1
        └── Sub-Asset: Forklift #2
```

## Instructions

### Step 1: Query Locations

```typescript
// src/workflows/asset-location.ts
import { MaintainXClient } from '../api/maintainx-client';

interface Location {
  id: string;
  name: string;
  address?: string;
  parentId?: string;
  children?: Location[];
}

// Get all locations
async function getAllLocations(client: MaintainXClient): Promise<Location[]> {
  const allLocations: Location[] = [];
  let cursor: string | undefined;

  do {
    const response = await client.getLocations({ cursor, limit: 100 });
    allLocations.push(...response.locations);
    cursor = response.nextCursor || undefined;
  } while (cursor);

  return allLocations;
}

// Build location hierarchy tree
function buildLocationTree(locations: Location[]): Location[] {
  const locationMap = new Map<string, Location>();
  const rootLocations: Location[] = [];

  // First pass: create map
  locations.forEach(loc => {
    locationMap.set(loc.id, { ...loc, children: [] });
  });

  // Second pass: build tree
  locations.forEach(loc => {
    const node = locationMap.get(loc.id)!;
    if (loc.parentId && locationMap.has(loc.parentId)) {
      const parent = locationMap.get(loc.parentId)!;
      parent.children!.push(node);
    } else {
      rootLocations.push(node);
    }
  });

  return rootLocations;
}

// Print location tree
function printLocationTree(locations: Location[], indent = 0) {
  const prefix = '  '.repeat(indent);
  locations.forEach(loc => {
    console.log(`${prefix}├── ${loc.name} (${loc.id})`);
    if (loc.children && loc.children.length > 0) {
      printLocationTree(loc.children, indent + 1);
    }
  });
}

// Usage
async function displayLocationHierarchy(client: MaintainXClient) {
  console.log('=== Location Hierarchy ===\n');
  const locations = await getAllLocations(client);
  const tree = buildLocationTree(locations);
  printLocationTree(tree);
}
```

### Step 2: Query Assets

```typescript
interface Asset {
  id: string;
  name: string;
  serialNumber?: string;
  model?: string;
  manufacturer?: string;
  status: 'OPERATIONAL' | 'NON_OPERATIONAL' | 'DECOMMISSIONED';
  locationId?: string;
  location?: Location;
  parentAssetId?: string;
  customFields?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

// Get all assets
async function getAllAssets(client: MaintainXClient): Promise<Asset[]> {
  const allAssets: Asset[] = [];
  let cursor: string | undefined;

  do {
    const response = await client.getAssets({ cursor, limit: 100 });
    allAssets.push(...response.assets);
    cursor = response.nextCursor || undefined;
  } while (cursor);

  return allAssets;
}

// Get assets by location
async function getAssetsByLocation(
  client: MaintainXClient,
  locationId: string
): Promise<Asset[]> {
  const response = await client.getAssets({ locationId, limit: 100 });
  return response.assets;
}

// Get asset details
async function getAssetDetails(
  client: MaintainXClient,
  assetId: string
): Promise<Asset> {
  return client.getAsset(assetId);
}
```

### Step 3: Asset Analysis

```typescript
interface AssetAnalysis {
  totalAssets: number;
  byStatus: Record<string, number>;
  byLocation: Record<string, number>;
  byManufacturer: Record<string, number>;
  noLocation: Asset[];
}

async function analyzeAssets(client: MaintainXClient): Promise<AssetAnalysis> {
  const assets = await getAllAssets(client);

  const analysis: AssetAnalysis = {
    totalAssets: assets.length,
    byStatus: {},
    byLocation: {},
    byManufacturer: {},
    noLocation: [],
  };

  assets.forEach(asset => {
    // Count by status
    const status = asset.status || 'UNKNOWN';
    analysis.byStatus[status] = (analysis.byStatus[status] || 0) + 1;

    // Count by location
    if (asset.location?.name) {
      const loc = asset.location.name;
      analysis.byLocation[loc] = (analysis.byLocation[loc] || 0) + 1;
    } else {
      analysis.noLocation.push(asset);
    }

    // Count by manufacturer
    if (asset.manufacturer) {
      analysis.byManufacturer[asset.manufacturer] =
        (analysis.byManufacturer[asset.manufacturer] || 0) + 1;
    }
  });

  return analysis;
}

// Print analysis report
function printAssetReport(analysis: AssetAnalysis) {
  console.log('=== Asset Analysis Report ===\n');
  console.log(`Total Assets: ${analysis.totalAssets}\n`);

  console.log('By Status:');
  Object.entries(analysis.byStatus).forEach(([status, count]) => {
    console.log(`  ${status}: ${count}`);
  });

  console.log('\nBy Location:');
  Object.entries(analysis.byLocation)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .forEach(([loc, count]) => {
      console.log(`  ${loc}: ${count}`);
    });

  console.log('\nBy Manufacturer:');
  Object.entries(analysis.byManufacturer)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .forEach(([mfr, count]) => {
      console.log(`  ${mfr}: ${count}`);
    });

  if (analysis.noLocation.length > 0) {
    console.log(`\nAssets without location: ${analysis.noLocation.length}`);
  }
}
```

### Step 4: Asset Work Order History

```typescript
// Get maintenance history for an asset
async function getAssetMaintenanceHistory(
  client: MaintainXClient,
  assetId: string
) {
  const workOrders = await client.getWorkOrders({
    assetId,
    limit: 100,
  });

  // Analyze work order history
  const history = {
    total: workOrders.workOrders.length,
    completed: workOrders.workOrders.filter(wo => wo.status === 'DONE').length,
    open: workOrders.workOrders.filter(wo => wo.status === 'OPEN').length,
    inProgress: workOrders.workOrders.filter(wo => wo.status === 'IN_PROGRESS').length,
    recentWorkOrders: workOrders.workOrders.slice(0, 5),
  };

  return history;
}

// Generate asset report card
async function generateAssetReportCard(
  client: MaintainXClient,
  assetId: string
) {
  const asset = await getAssetDetails(client, assetId);
  const history = await getAssetMaintenanceHistory(client, assetId);

  console.log('=== Asset Report Card ===\n');
  console.log(`Name: ${asset.name}`);
  console.log(`ID: ${asset.id}`);
  console.log(`Status: ${asset.status}`);
  console.log(`Serial Number: ${asset.serialNumber || 'N/A'}`);
  console.log(`Manufacturer: ${asset.manufacturer || 'N/A'}`);
  console.log(`Model: ${asset.model || 'N/A'}`);
  console.log(`Location: ${asset.location?.name || 'Not assigned'}`);
  console.log(`\nMaintenance History:`);
  console.log(`  Total Work Orders: ${history.total}`);
  console.log(`  Completed: ${history.completed}`);
  console.log(`  Open: ${history.open}`);
  console.log(`  In Progress: ${history.inProgress}`);

  if (history.recentWorkOrders.length > 0) {
    console.log('\nRecent Work Orders:');
    history.recentWorkOrders.forEach(wo => {
      console.log(`  - ${wo.title} (${wo.status})`);
    });
  }

  return { asset, history };
}
```

### Step 5: Location-Based Asset View

```typescript
// Get assets organized by location
async function getAssetsGroupedByLocation(client: MaintainXClient) {
  const locations = await getAllLocations(client);
  const assets = await getAllAssets(client);

  const assetsByLocation: Map<string, Asset[]> = new Map();

  // Group assets by location
  assets.forEach(asset => {
    const locId = asset.locationId || 'UNASSIGNED';
    if (!assetsByLocation.has(locId)) {
      assetsByLocation.set(locId, []);
    }
    assetsByLocation.get(locId)!.push(asset);
  });

  // Create location map for names
  const locationMap = new Map(
    locations.map(loc => [loc.id, loc.name])
  );

  // Print organized view
  console.log('=== Assets by Location ===\n');
  assetsByLocation.forEach((locAssets, locId) => {
    const locName = locationMap.get(locId) || locId;
    console.log(`\n${locName} (${locAssets.length} assets):`);
    locAssets.forEach(asset => {
      const status = asset.status === 'OPERATIONAL' ? '[OK]' : '[!]';
      console.log(`  ${status} ${asset.name}`);
    });
  });

  return assetsByLocation;
}
```

### Step 6: Preventive Maintenance Planning

```typescript
interface PMSchedule {
  assetId: string;
  assetName: string;
  lastMaintenanceDate?: Date;
  nextDueDate: Date;
  frequency: string; // e.g., "30 days", "quarterly"
  tasks: string[];
}

// Plan preventive maintenance based on asset types
function generatePMSchedule(assets: Asset[]): PMSchedule[] {
  const schedules: PMSchedule[] = [];

  assets.forEach(asset => {
    // Skip non-operational assets
    if (asset.status !== 'OPERATIONAL') return;

    // Example PM schedules based on asset type (infer from name)
    const name = asset.name.toLowerCase();

    if (name.includes('hvac') || name.includes('air')) {
      schedules.push({
        assetId: asset.id,
        assetName: asset.name,
        nextDueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
        frequency: '30 days',
        tasks: [
          'Replace air filters',
          'Check refrigerant levels',
          'Inspect belts and pulleys',
          'Clean coils',
          'Test thermostat',
        ],
      });
    } else if (name.includes('pump')) {
      schedules.push({
        assetId: asset.id,
        assetName: asset.name,
        nextDueDate: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000),
        frequency: '90 days',
        tasks: [
          'Check seal condition',
          'Inspect impeller',
          'Verify flow rates',
          'Lubricate bearings',
        ],
      });
    } else if (name.includes('conveyor')) {
      schedules.push({
        assetId: asset.id,
        assetName: asset.name,
        nextDueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        frequency: '7 days',
        tasks: [
          'Inspect belt tension',
          'Check motor operation',
          'Lubricate rollers',
          'Clean sensors',
        ],
      });
    }
  });

  return schedules;
}

// Create work orders from PM schedule
async function createPMWorkOrders(
  client: MaintainXClient,
  schedules: PMSchedule[]
) {
  const created = [];

  for (const schedule of schedules) {
    const workOrder = await client.createWorkOrder({
      title: `Scheduled PM - ${schedule.assetName}`,
      description: `
## Preventive Maintenance
Frequency: ${schedule.frequency}

## Tasks
${schedule.tasks.map(t => `- [ ] ${t}`).join('\n')}
      `,
      priority: 'MEDIUM',
      assetId: schedule.assetId,
      dueDate: schedule.nextDueDate.toISOString(),
    });
    created.push(workOrder);
  }

  return created;
}
```

## Output

- Complete location hierarchy view
- Asset inventory analysis
- Asset maintenance history
- Location-based asset groupings
- Preventive maintenance schedules

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 404 Not Found | Invalid asset/location ID | Verify ID exists |
| Empty Results | No data or wrong filter | Check query parameters |
| Pagination issues | Missing cursor handling | Use pagination helper |
| Permission denied | Insufficient access | Verify user permissions |

## Asset Status Reference

| Status | Description | Action |
|--------|-------------|--------|
| OPERATIONAL | Working normally | Schedule PM |
| NON_OPERATIONAL | Not functioning | Create repair WO |
| DECOMMISSIONED | Retired from use | Archive/remove |

## Resources

- [MaintainX Assets Guide](https://help.getmaintainx.com/)
- [MaintainX Locations](https://help.getmaintainx.com/)
- [API Documentation](https://maintainx.dev/)

## Next Steps

For troubleshooting common issues, see `maintainx-common-errors`.
