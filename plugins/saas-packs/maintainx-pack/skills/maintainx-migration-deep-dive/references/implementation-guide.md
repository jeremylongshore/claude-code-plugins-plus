# MaintainX Migration Deep Dive - Implementation Guide

> Full implementation details and code examples for the `maintainx-migration-deep-dive` skill.

# MaintainX Migration Deep Dive

## Overview

Comprehensive guide for migrating to MaintainX from legacy CMMS systems, spreadsheets, or other maintenance management tools.

## Prerequisites

- MaintainX account with API access
- Access to source system data
- Understanding of both systems' data models

## Migration Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Migration Strategy Overview                       │
│                                                                      │
│  Phase 1          Phase 2          Phase 3          Phase 4         │
│  ASSESS           PREPARE          MIGRATE          VALIDATE        │
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │Inventory │    │Data      │    │Parallel  │    │Testing   │      │
│  │data      │───▶│cleansing │───▶│run       │───▶│& cutover │      │
│  │          │    │& mapping │    │          │    │          │      │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
│                                                                      │
│  Week 1-2        Week 3-4        Week 5-6        Week 7-8          │
└─────────────────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Source System Assessment

```typescript
// scripts/migration-assessment.ts

interface SourceSystemAssessment {
  system: string;
  dataVolume: {
    workOrders: number;
    assets: number;
    locations: number;
    users: number;
    procedures: number;
  };
  dataQuality: {
    completeness: number;  // Percentage
    duplicates: number;
    invalidRecords: number;
  };
  customizations: string[];
  integrations: string[];
  risks: string[];
}

async function assessSourceSystem(sourceData: any): Promise<SourceSystemAssessment> {
  console.log('=== Migration Assessment ===\n');

  const assessment: SourceSystemAssessment = {
    system: sourceData.systemName || 'Unknown',
    dataVolume: {
      workOrders: 0,
      assets: 0,
      locations: 0,
      users: 0,
      procedures: 0,
    },
    dataQuality: {
      completeness: 0,
      duplicates: 0,
      invalidRecords: 0,
    },
    customizations: [],
    integrations: [],
    risks: [],
  };

  // Count records
  console.log('Counting records...');
  assessment.dataVolume.workOrders = sourceData.workOrders?.length || 0;
  assessment.dataVolume.assets = sourceData.assets?.length || 0;
  assessment.dataVolume.locations = sourceData.locations?.length || 0;
  assessment.dataVolume.users = sourceData.users?.length || 0;
  assessment.dataVolume.procedures = sourceData.procedures?.length || 0;

  // Analyze data quality
  console.log('Analyzing data quality...');
  const workOrders = sourceData.workOrders || [];

  // Check completeness (required fields)
  const requiredFields = ['title', 'createdAt'];
  let completeRecords = 0;
  workOrders.forEach((wo: any) => {
    const hasAllRequired = requiredFields.every(f => wo[f]);
    if (hasAllRequired) completeRecords++;
  });
  assessment.dataQuality.completeness = workOrders.length > 0
    ? (completeRecords / workOrders.length) * 100
    : 100;

  // Check for duplicates
  const titles = workOrders.map((wo: any) => wo.title);
  const uniqueTitles = new Set(titles);
  assessment.dataQuality.duplicates = titles.length - uniqueTitles.size;

  // Identify risks
  if (assessment.dataVolume.workOrders > 10000) {
    assessment.risks.push('Large data volume may require batched migration');
  }
  if (assessment.dataQuality.completeness < 80) {
    assessment.risks.push('Low data completeness - may need data enrichment');
  }
  if (assessment.dataQuality.duplicates > 100) {
    assessment.risks.push('Significant duplicates - deduplication recommended');
  }

  return assessment;
}

// Print assessment report
function printAssessmentReport(assessment: SourceSystemAssessment): void {
  console.log('\n=== Assessment Report ===\n');

  console.log('Data Volume:');
  console.log(`  Work Orders: ${assessment.dataVolume.workOrders.toLocaleString()}`);
  console.log(`  Assets: ${assessment.dataVolume.assets.toLocaleString()}`);
  console.log(`  Locations: ${assessment.dataVolume.locations.toLocaleString()}`);
  console.log(`  Users: ${assessment.dataVolume.users.toLocaleString()}`);
  console.log(`  Procedures: ${assessment.dataVolume.procedures.toLocaleString()}`);

  console.log('\nData Quality:');
  console.log(`  Completeness: ${assessment.dataQuality.completeness.toFixed(1)}%`);
  console.log(`  Duplicates: ${assessment.dataQuality.duplicates}`);
  console.log(`  Invalid Records: ${assessment.dataQuality.invalidRecords}`);

  if (assessment.risks.length > 0) {
    console.log('\nRisks:');
    assessment.risks.forEach(r => console.log(`  - ${r}`));
  }
}
```

### Step 2: Data Mapping

```typescript
// src/migration/data-mapping.ts

interface FieldMapping {
  sourceField: string;
  targetField: string;
  transform?: (value: any) => any;
  required: boolean;
  defaultValue?: any;
}

interface DataMapping {
  workOrders: FieldMapping[];
  assets: FieldMapping[];
  locations: FieldMapping[];
  users: FieldMapping[];
}

// Common mappings from legacy systems
const legacyCmmsToMaintainX: DataMapping = {
  workOrders: [
    { sourceField: 'wo_number', targetField: 'externalId', required: false },
    { sourceField: 'wo_title', targetField: 'title', required: true },
    { sourceField: 'wo_description', targetField: 'description', required: false },
    {
      sourceField: 'wo_priority',
      targetField: 'priority',
      required: false,
      defaultValue: 'MEDIUM',
      transform: (value) => {
        const map: Record<string, string> = {
          '1': 'HIGH', 'high': 'HIGH', 'urgent': 'HIGH',
          '2': 'MEDIUM', 'medium': 'MEDIUM', 'normal': 'MEDIUM',
          '3': 'LOW', 'low': 'LOW', 'minor': 'LOW',
        };
        return map[String(value).toLowerCase()] || 'MEDIUM';
      },
    },
    {
      sourceField: 'wo_status',
      targetField: 'status',
      required: false,
      defaultValue: 'OPEN',
      transform: (value) => {
        const map: Record<string, string> = {
          'new': 'OPEN', 'open': 'OPEN', 'pending': 'OPEN',
          'in_progress': 'IN_PROGRESS', 'active': 'IN_PROGRESS', 'working': 'IN_PROGRESS',
          'hold': 'ON_HOLD', 'waiting': 'ON_HOLD', 'paused': 'ON_HOLD',
          'complete': 'DONE', 'completed': 'DONE', 'closed': 'DONE', 'done': 'DONE',
        };
        return map[String(value).toLowerCase()] || 'OPEN';
      },
    },
    { sourceField: 'created_date', targetField: 'createdAt', required: false },
    { sourceField: 'due_date', targetField: 'dueDate', required: false },
    { sourceField: 'equipment_id', targetField: 'assetId', required: false },
    { sourceField: 'location_id', targetField: 'locationId', required: false },
  ],

  assets: [
    { sourceField: 'asset_id', targetField: 'externalId', required: false },
    { sourceField: 'asset_name', targetField: 'name', required: true },
    { sourceField: 'serial_number', targetField: 'serialNumber', required: false },
    { sourceField: 'model_number', targetField: 'model', required: false },
    { sourceField: 'manufacturer', targetField: 'manufacturer', required: false },
    {
      sourceField: 'asset_status',
      targetField: 'status',
      required: false,
      defaultValue: 'OPERATIONAL',
      transform: (value) => {
        const map: Record<string, string> = {
          'active': 'OPERATIONAL', 'operational': 'OPERATIONAL', 'running': 'OPERATIONAL',
          'down': 'NON_OPERATIONAL', 'broken': 'NON_OPERATIONAL', 'offline': 'NON_OPERATIONAL',
          'retired': 'DECOMMISSIONED', 'decommissioned': 'DECOMMISSIONED',
        };
        return map[String(value).toLowerCase()] || 'OPERATIONAL';
      },
    },
  ],

  locations: [
    { sourceField: 'location_id', targetField: 'externalId', required: false },
    { sourceField: 'location_name', targetField: 'name', required: true },
    { sourceField: 'address', targetField: 'address', required: false },
    { sourceField: 'parent_location_id', targetField: 'parentId', required: false },
  ],

  users: [
    { sourceField: 'user_id', targetField: 'externalId', required: false },
    { sourceField: 'first_name', targetField: 'firstName', required: true },
    { sourceField: 'last_name', targetField: 'lastName', required: true },
    { sourceField: 'email', targetField: 'email', required: true },
  ],
};

// Apply mapping to transform data
function applyMapping<T>(
  sourceRecords: any[],
  mappings: FieldMapping[]
): T[] {
  return sourceRecords.map(source => {
    const target: any = {};

    mappings.forEach(mapping => {
      let value = source[mapping.sourceField];

      // Apply transform if defined
      if (mapping.transform && value !== undefined && value !== null) {
        value = mapping.transform(value);
      }

      // Apply default if value is missing
      if ((value === undefined || value === null) && mapping.defaultValue !== undefined) {
        value = mapping.defaultValue;
      }

      // Skip if no value and not required
      if (value === undefined || value === null) {
        if (mapping.required) {
          throw new Error(`Required field missing: ${mapping.sourceField}`);
        }
        return;
      }

      target[mapping.targetField] = value;
    });

    return target as T;
  });
}
```

### Step 3: Migration Execution

```typescript
// src/migration/migrator.ts

interface MigrationPlan {
  phases: MigrationPhase[];
  rollbackPlan: RollbackStep[];
  validationRules: ValidationRule[];
}

interface MigrationPhase {
  name: string;
  order: number;
  resource: 'locations' | 'assets' | 'users' | 'workOrders';
  batchSize: number;
  dependsOn?: string[];
}

interface MigrationResult {
  phase: string;
  status: 'success' | 'partial' | 'failed';
  processed: number;
  succeeded: number;
  failed: number;
  errors: MigrationError[];
  duration: number;
}

class MaintainXMigrator {
  private client: MaintainXClient;
  private idMapping: Map<string, string> = new Map();  // sourceId -> maintainxId

  async executeMigration(
    sourceData: any,
    plan: MigrationPlan
  ): Promise<MigrationResult[]> {
    const results: MigrationResult[] = [];

    // Sort phases by order and dependencies
    const sortedPhases = this.sortPhases(plan.phases);

    for (const phase of sortedPhases) {
      console.log(`\n=== Executing Phase: ${phase.name} ===\n`);

      const result = await this.executePhase(
        phase,
        sourceData[phase.resource],
        plan.validationRules
      );

      results.push(result);

      // Stop if critical phase failed
      if (result.status === 'failed') {
        console.error(`Phase ${phase.name} failed. Migration halted.`);
        break;
      }
    }

    return results;
  }

  private async executePhase(
    phase: MigrationPhase,
    sourceRecords: any[],
    validationRules: ValidationRule[]
  ): Promise<MigrationResult> {
    const startTime = Date.now();
    const result: MigrationResult = {
      phase: phase.name,
      status: 'success',
      processed: 0,
      succeeded: 0,
      failed: 0,
      errors: [],
      duration: 0,
    };

    // Transform data
    const mappings = legacyCmmsToMaintainX[phase.resource];
    let transformedRecords: any[];

    try {
      transformedRecords = applyMapping(sourceRecords, mappings);
    } catch (error: any) {
      result.status = 'failed';
      result.errors.push({ record: null, error: error.message });
      result.duration = Date.now() - startTime;
      return result;
    }

    // Process in batches
    for (let i = 0; i < transformedRecords.length; i += phase.batchSize) {
      const batch = transformedRecords.slice(i, i + phase.batchSize);

      for (const record of batch) {
        result.processed++;

        try {
          // Resolve ID references
          if (record.assetId && this.idMapping.has(record.assetId)) {
            record.assetId = this.idMapping.get(record.assetId);
          }
          if (record.locationId && this.idMapping.has(record.locationId)) {
            record.locationId = this.idMapping.get(record.locationId);
          }
          if (record.parentId && this.idMapping.has(record.parentId)) {
            record.parentId = this.idMapping.get(record.parentId);
          }

          // Create in MaintainX
          const created = await this.createRecord(phase.resource, record);

          // Store ID mapping for references
          if (record.externalId) {
            this.idMapping.set(record.externalId, created.id);
          }

          result.succeeded++;
        } catch (error: any) {
          result.failed++;
          result.errors.push({
            record,
            error: error.message,
          });
        }
      }

      console.log(`Progress: ${result.processed}/${transformedRecords.length}`);

      // Rate limit protection
      await new Promise(r => setTimeout(r, 100));
    }

    result.status = result.failed === 0 ? 'success' :
                    result.succeeded > 0 ? 'partial' : 'failed';
    result.duration = Date.now() - startTime;

    return result;
  }

  private async createRecord(resource: string, data: any): Promise<any> {
    switch (resource) {
      case 'workOrders':
        return this.client.createWorkOrder(data);
      // Add other resources as API supports
      default:
        throw new Error(`Unsupported resource: ${resource}`);
    }
  }
}
```

### Step 4: Validation & Verification

```typescript
// src/migration/validation.ts

interface ValidationReport {
  phase: string;
  totalRecords: number;
  passed: number;
  failed: number;
  failures: ValidationFailure[];
}

interface ValidationFailure {
  sourceId: string;
  targetId?: string;
  issues: string[];
}

class MigrationValidator {
  async validateMigration(
    sourceData: any[],
    targetData: any[]
  ): Promise<ValidationReport> {
    const report: ValidationReport = {
      phase: 'post-migration',
      totalRecords: sourceData.length,
      passed: 0,
      failed: 0,
      failures: [],
    };

    // Create lookup maps
    const sourceMap = new Map(sourceData.map(s => [s.externalId || s.id, s]));
    const targetMap = new Map(targetData.map(t => [t.externalId, t]));

    // Validate each source record exists in target
    for (const [sourceId, source] of sourceMap) {
      const target = targetMap.get(sourceId);
      const issues: string[] = [];

      if (!target) {
        issues.push('Record not found in target system');
      } else {
        // Validate critical fields match
        if (source.title !== target.title) {
          issues.push(`Title mismatch: "${source.title}" vs "${target.title}"`);
        }

        // Add more field validations as needed
      }

      if (issues.length === 0) {
        report.passed++;
      } else {
        report.failed++;
        report.failures.push({
          sourceId,
          targetId: target?.id,
          issues,
        });
      }
    }

    return report;
  }

  async generateReconciliationReport(
    sourceData: any[],
    maintainxClient: MaintainXClient
  ): Promise<void> {
    console.log('=== Migration Reconciliation Report ===\n');

    // Get counts from MaintainX
    const woResponse = await maintainxClient.getWorkOrders({ limit: 1 });
    const assetResponse = await maintainxClient.getAssets({ limit: 1 });
    const locationResponse = await maintainxClient.getLocations({ limit: 1 });

    console.log('Record Counts:');
    console.log(`  Source work orders: ${sourceData.workOrders?.length || 0}`);
    console.log(`  MaintainX work orders: ${woResponse.workOrders.length}+`);
    console.log('');
    console.log(`  Source assets: ${sourceData.assets?.length || 0}`);
    console.log(`  MaintainX assets: ${assetResponse.assets.length}+`);
    console.log('');
    console.log(`  Source locations: ${sourceData.locations?.length || 0}`);
    console.log(`  MaintainX locations: ${locationResponse.locations.length}+`);
  }
}
```

### Step 5: Rollback Procedures

```typescript
// src/migration/rollback.ts

interface RollbackPlan {
  steps: RollbackStep[];
  checkpoint: Date;
}

interface RollbackStep {
  order: number;
  description: string;
  execute: () => Promise<void>;
}

class MigrationRollback {
  private client: MaintainXClient;
  private migratedIds: Map<string, string[]> = new Map();  // resource -> ids

  // Track migrated records for potential rollback
  trackMigrated(resource: string, id: string): void {
    if (!this.migratedIds.has(resource)) {
      this.migratedIds.set(resource, []);
    }
    this.migratedIds.get(resource)!.push(id);
  }

  // Generate rollback plan
  generateRollbackPlan(): RollbackPlan {
    const plan: RollbackPlan = {
      steps: [],
      checkpoint: new Date(),
    };

    // Note: Actual rollback depends on available API endpoints
    // MaintainX may not support programmatic deletion

    plan.steps.push({
      order: 1,
      description: 'Document migrated record IDs',
      execute: async () => {
        const report = {
          timestamp: new Date().toISOString(),
          records: Object.fromEntries(this.migratedIds),
        };
        await fs.writeFile(
          `rollback-data-${Date.now()}.json`,
          JSON.stringify(report, null, 2)
        );
        console.log('Rollback data saved');
      },
    });

    plan.steps.push({
      order: 2,
      description: 'Contact MaintainX support for bulk deletion',
      execute: async () => {
        console.log('Manual step required:');
        console.log('1. Contact MaintainX support');
        console.log('2. Provide list of migrated record IDs');
        console.log('3. Request bulk deletion or archival');
      },
    });

    plan.steps.push({
      order: 3,
      description: 'Verify rollback completion',
      execute: async () => {
        // Verify records are removed
        console.log('Verify records have been removed from MaintainX');
      },
    });

    return plan;
  }

  async executeRollback(plan: RollbackPlan): Promise<void> {
    console.log('=== Executing Rollback ===\n');

    for (const step of plan.steps.sort((a, b) => a.order - b.order)) {
      console.log(`Step ${step.order}: ${step.description}`);
      await step.execute();
      console.log('Done\n');
    }

    console.log('Rollback complete');
  }
}
```

## Migration Checklist

- [ ] Source system assessed
- [ ] Data mapping defined
- [ ] Test migration completed (subset)
- [ ] Full migration executed
- [ ] Validation passed
- [ ] User acceptance testing
- [ ] Cutover completed
- [ ] Source system decommissioned

## Output

- Assessment report
- Data mapping configuration
- Migration results
- Validation report
- Rollback plan

## Timeline Template

| Week | Phase | Activities |
|------|-------|------------|
| 1-2 | Assessment | Data inventory, quality analysis |
| 3-4 | Preparation | Mapping, test migration |
| 5-6 | Migration | Parallel run, data migration |
| 7-8 | Validation | Testing, cutover, decommission |

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [MaintainX Import Guide](https://help.getmaintainx.com/)
- [Data Migration Best Practices](https://martinfowler.com/articles/data-migration-patterns.html)

## Next Steps

Congratulations! You have completed the MaintainX skill pack. For additional support, contact MaintainX at support@getmaintainx.com.
