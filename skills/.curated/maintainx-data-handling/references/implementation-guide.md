# MaintainX Data Handling - Implementation Guide

> Full implementation details and code examples for the `maintainx-data-handling` skill.

# MaintainX Data Handling

## Overview

Patterns and best practices for synchronizing, transforming, and managing data between MaintainX and external systems.

## Prerequisites

- MaintainX API access
- Database for local storage
- Understanding of data pipeline concepts

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MaintainX Data Flow                               │
│                                                                      │
│  ┌───────────────┐                         ┌───────────────┐        │
│  │   MaintainX   │                         │ External      │        │
│  │   Platform    │                         │ Systems       │        │
│  │               │                         │               │        │
│  │ - Work Orders │                         │ - ERP         │        │
│  │ - Assets      │                         │ - BI/Reports  │        │
│  │ - Locations   │                         │ - Data Lake   │        │
│  │ - Users       │                         │ - SCADA       │        │
│  └───────┬───────┘                         └───────▲───────┘        │
│          │                                         │                │
│          │  ┌─────────────────────────────┐       │                │
│          └─▶│     ETL Pipeline            │───────┘                │
│             │                             │                         │
│             │  Extract → Transform → Load │                         │
│             │                             │                         │
│             └─────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Data Extraction

```typescript
// src/etl/extract.ts

interface ExtractionOptions {
  since?: Date;
  batchSize?: number;
  resources: ('workorders' | 'assets' | 'locations' | 'users')[];
}

interface ExtractedData {
  workOrders: WorkOrder[];
  assets: Asset[];
  locations: Location[];
  users: User[];
  extractedAt: Date;
  cursor?: string;
}

class MaintainXExtractor {
  private client: MaintainXClient;

  async extract(options: ExtractionOptions): Promise<ExtractedData> {
    const data: ExtractedData = {
      workOrders: [],
      assets: [],
      locations: [],
      users: [],
      extractedAt: new Date(),
    };

    for (const resource of options.resources) {
      switch (resource) {
        case 'workorders':
          data.workOrders = await this.extractWorkOrders(options);
          break;
        case 'assets':
          data.assets = await this.extractAssets(options);
          break;
        case 'locations':
          data.locations = await this.extractLocations(options);
          break;
        case 'users':
          data.users = await this.extractUsers(options);
          break;
      }
    }

    return data;
  }

  private async extractWorkOrders(options: ExtractionOptions): Promise<WorkOrder[]> {
    const allWorkOrders: WorkOrder[] = [];
    let cursor: string | undefined;

    do {
      const response = await this.client.getWorkOrders({
        cursor,
        limit: options.batchSize || 100,
        // Filter by update time if doing incremental extract
        ...(options.since && { updatedAfter: options.since.toISOString() }),
      });

      allWorkOrders.push(...response.workOrders);
      cursor = response.nextCursor || undefined;

      console.log(`Extracted ${allWorkOrders.length} work orders...`);
    } while (cursor);

    return allWorkOrders;
  }

  private async extractAssets(options: ExtractionOptions): Promise<Asset[]> {
    const allAssets: Asset[] = [];
    let cursor: string | undefined;

    do {
      const response = await this.client.getAssets({
        cursor,
        limit: options.batchSize || 100,
      });

      allAssets.push(...response.assets);
      cursor = response.nextCursor || undefined;
    } while (cursor);

    return allAssets;
  }

  // Similar for locations and users...
}
```

### Step 2: Data Transformation

```typescript
// src/etl/transform.ts

interface TransformationConfig {
  fieldMappings: Record<string, string>;
  enrichments: Enrichment[];
  filters: Filter[];
}

interface TransformedWorkOrder {
  externalId: string;
  title: string;
  description: string;
  status: string;
  priority: number;  // Numeric for sorting
  assetName?: string;
  locationPath?: string;
  assigneeNames: string[];
  createdDate: Date;
  completedDate?: Date;
  durationHours?: number;
  customFields: Record<string, any>;
}

class DataTransformer {
  private config: TransformationConfig;
  private assetMap: Map<string, Asset>;
  private locationMap: Map<string, Location>;
  private userMap: Map<string, User>;

  constructor(config: TransformationConfig) {
    this.config = config;
  }

  setLookupData(assets: Asset[], locations: Location[], users: User[]) {
    this.assetMap = new Map(assets.map(a => [a.id, a]));
    this.locationMap = new Map(locations.map(l => [l.id, l]));
    this.userMap = new Map(users.map(u => [u.id, u]));
  }

  transformWorkOrders(workOrders: WorkOrder[]): TransformedWorkOrder[] {
    return workOrders
      .filter(wo => this.applyFilters(wo))
      .map(wo => this.transformWorkOrder(wo));
  }

  private transformWorkOrder(wo: WorkOrder): TransformedWorkOrder {
    const asset = wo.assetId ? this.assetMap.get(wo.assetId) : undefined;
    const location = wo.locationId ? this.locationMap.get(wo.locationId) : undefined;

    return {
      externalId: wo.id,
      title: wo.title,
      description: wo.description || '',
      status: this.mapStatus(wo.status),
      priority: this.mapPriority(wo.priority),
      assetName: asset?.name,
      locationPath: this.buildLocationPath(location),
      assigneeNames: this.resolveAssignees(wo.assignees || []),
      createdDate: new Date(wo.createdAt),
      completedDate: wo.completedAt ? new Date(wo.completedAt) : undefined,
      durationHours: this.calculateDuration(wo),
      customFields: this.extractCustomFields(wo),
    };
  }

  private mapPriority(priority: string): number {
    const priorityMap: Record<string, number> = {
      'NONE': 0,
      'LOW': 1,
      'MEDIUM': 2,
      'HIGH': 3,
    };
    return priorityMap[priority] || 0;
  }

  private mapStatus(status: string): string {
    const statusMap: Record<string, string> = {
      'OPEN': 'Pending',
      'IN_PROGRESS': 'In Progress',
      'ON_HOLD': 'Paused',
      'DONE': 'Completed',
    };
    return statusMap[status] || status;
  }

  private buildLocationPath(location?: Location): string {
    if (!location) return '';

    const parts: string[] = [location.name];
    let current = location;

    while (current.parentId) {
      const parent = this.locationMap.get(current.parentId);
      if (!parent) break;
      parts.unshift(parent.name);
      current = parent;
    }

    return parts.join(' > ');
  }

  private resolveAssignees(assignees: any[]): string[] {
    return assignees.map(a => {
      if (typeof a === 'string') {
        const user = this.userMap.get(a);
        return user ? `${user.firstName} ${user.lastName}` : a;
      }
      return `${a.firstName} ${a.lastName}`;
    });
  }

  private calculateDuration(wo: WorkOrder): number | undefined {
    if (!wo.completedAt) return undefined;

    const start = new Date(wo.createdAt).getTime();
    const end = new Date(wo.completedAt).getTime();
    return (end - start) / (1000 * 60 * 60);  // Hours
  }
}
```

### Step 3: Data Loading

```typescript
// src/etl/load.ts

interface LoadResult {
  inserted: number;
  updated: number;
  skipped: number;
  errors: LoadError[];
}

interface LoadError {
  record: any;
  error: string;
}

class DataLoader {
  private db: Database;

  async loadWorkOrders(
    workOrders: TransformedWorkOrder[],
    options: { upsert: boolean }
  ): Promise<LoadResult> {
    const result: LoadResult = {
      inserted: 0,
      updated: 0,
      skipped: 0,
      errors: [],
    };

    for (const wo of workOrders) {
      try {
        if (options.upsert) {
          const existing = await this.db.workOrders.findOne({
            externalId: wo.externalId,
          });

          if (existing) {
            await this.db.workOrders.update(
              { externalId: wo.externalId },
              { $set: wo }
            );
            result.updated++;
          } else {
            await this.db.workOrders.insert(wo);
            result.inserted++;
          }
        } else {
          await this.db.workOrders.insert(wo);
          result.inserted++;
        }
      } catch (error: any) {
        result.errors.push({
          record: wo,
          error: error.message,
        });
      }
    }

    return result;
  }

  // Export to CSV
  async exportToCsv(
    workOrders: TransformedWorkOrder[],
    filePath: string
  ): Promise<void> {
    const headers = [
      'ID', 'Title', 'Status', 'Priority', 'Asset', 'Location',
      'Assignees', 'Created', 'Completed', 'Duration (hrs)'
    ];

    const rows = workOrders.map(wo => [
      wo.externalId,
      `"${wo.title.replace(/"/g, '""')}"`,
      wo.status,
      wo.priority,
      wo.assetName || '',
      wo.locationPath || '',
      wo.assigneeNames.join('; '),
      wo.createdDate.toISOString(),
      wo.completedDate?.toISOString() || '',
      wo.durationHours?.toFixed(2) || '',
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    await fs.writeFile(filePath, csv);
  }

  // Export to BigQuery
  async exportToBigQuery(
    workOrders: TransformedWorkOrder[],
    datasetId: string,
    tableId: string
  ): Promise<void> {
    const bigquery = new BigQuery();

    await bigquery
      .dataset(datasetId)
      .table(tableId)
      .insert(workOrders);
  }
}
```

### Step 4: Incremental Sync

```typescript
// src/etl/incremental-sync.ts

interface SyncState {
  lastSyncTime: Date;
  lastCursor?: string;
  status: 'idle' | 'running' | 'failed';
}

class IncrementalSync {
  private extractor: MaintainXExtractor;
  private transformer: DataTransformer;
  private loader: DataLoader;
  private stateStore: StateStore;

  async runSync(): Promise<SyncReport> {
    const state = await this.stateStore.getState('maintainx-sync');
    const report: SyncReport = {
      startTime: new Date(),
      endTime: null,
      status: 'running',
      extracted: 0,
      transformed: 0,
      loaded: { inserted: 0, updated: 0, errors: 0 },
    };

    try {
      // Mark sync as running
      await this.stateStore.setState('maintainx-sync', {
        ...state,
        status: 'running',
      });

      // Extract changes since last sync
      console.log(`Extracting changes since ${state.lastSyncTime}...`);
      const data = await this.extractor.extract({
        since: state.lastSyncTime,
        resources: ['workorders', 'assets', 'locations', 'users'],
      });
      report.extracted = data.workOrders.length;

      // Transform
      console.log('Transforming data...');
      this.transformer.setLookupData(data.assets, data.locations, data.users);
      const transformed = this.transformer.transformWorkOrders(data.workOrders);
      report.transformed = transformed.length;

      // Load
      console.log('Loading data...');
      const loadResult = await this.loader.loadWorkOrders(transformed, {
        upsert: true,
      });
      report.loaded = {
        inserted: loadResult.inserted,
        updated: loadResult.updated,
        errors: loadResult.errors.length,
      };

      // Update sync state
      await this.stateStore.setState('maintainx-sync', {
        lastSyncTime: data.extractedAt,
        status: 'idle',
      });

      report.status = 'success';
    } catch (error: any) {
      report.status = 'failed';
      report.error = error.message;

      await this.stateStore.setState('maintainx-sync', {
        ...state,
        status: 'failed',
      });
    }

    report.endTime = new Date();
    return report;
  }

  // Schedule periodic sync
  scheduleSync(intervalMinutes: number) {
    setInterval(() => this.runSync(), intervalMinutes * 60 * 1000);
    console.log(`Sync scheduled every ${intervalMinutes} minutes`);
  }
}
```

### Step 5: Data Reconciliation

```typescript
// src/etl/reconciliation.ts

interface ReconciliationResult {
  matches: number;
  missingInLocal: string[];
  missingInSource: string[];
  mismatches: DataMismatch[];
}

interface DataMismatch {
  id: string;
  field: string;
  sourceValue: any;
  localValue: any;
}

class DataReconciler {
  async reconcile(): Promise<ReconciliationResult> {
    const result: ReconciliationResult = {
      matches: 0,
      missingInLocal: [],
      missingInSource: [],
      mismatches: [],
    };

    // Get all IDs from both sources
    const sourceIds = await this.getSourceIds();
    const localIds = await this.getLocalIds();

    // Find missing
    result.missingInLocal = sourceIds.filter(id => !localIds.has(id));
    result.missingInSource = [...localIds].filter(id => !sourceIds.includes(id));

    // Compare matching records
    const matchingIds = sourceIds.filter(id => localIds.has(id));

    for (const id of matchingIds) {
      const sourceRecord = await this.getSourceRecord(id);
      const localRecord = await this.getLocalRecord(id);

      const mismatches = this.compareRecords(sourceRecord, localRecord);

      if (mismatches.length === 0) {
        result.matches++;
      } else {
        result.mismatches.push(...mismatches.map(m => ({ ...m, id })));
      }
    }

    return result;
  }

  private compareRecords(source: any, local: any): DataMismatch[] {
    const mismatches: DataMismatch[] = [];
    const fieldsToCompare = ['title', 'status', 'priority'];

    for (const field of fieldsToCompare) {
      if (source[field] !== local[field]) {
        mismatches.push({
          id: source.id,
          field,
          sourceValue: source[field],
          localValue: local[field],
        });
      }
    }

    return mismatches;
  }

  async fixMismatches(result: ReconciliationResult): Promise<void> {
    // Re-sync missing records
    for (const id of result.missingInLocal) {
      const record = await this.getSourceRecord(id);
      await this.loader.loadWorkOrders([record], { upsert: true });
    }

    // Update mismatched records
    for (const mismatch of result.mismatches) {
      const record = await this.getSourceRecord(mismatch.id);
      await this.loader.loadWorkOrders([record], { upsert: true });
    }
  }
}
```

## Output

- ETL pipeline implemented
- Incremental sync running
- Data reconciliation tools
- Export capabilities (CSV, BigQuery)

## Best Practices

1. **Always use incremental sync** - Full syncs are expensive
2. **Handle soft deletes** - Check for deleted records
3. **Log all transformations** - Audit trail for data changes
4. **Monitor data quality** - Track mismatches over time
5. **Implement idempotency** - Safe to re-run

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [Apache Airflow](https://airflow.apache.org/) - Workflow orchestration
- [dbt](https://www.getdbt.com/) - Data transformation

## Next Steps

For enterprise access control, see `maintainx-enterprise-rbac`.
