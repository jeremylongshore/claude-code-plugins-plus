# Apollo Migration Deep Dive - Implementation Guide

> Full implementation details and code examples for the `apollo-migration-deep-dive` skill.

# Apollo Migration Deep Dive

## Overview
Comprehensive guide for migrating to Apollo.io from other CRMs and data sources, including data mapping, validation, and rollback strategies.

## Migration Planning

### Pre-Migration Assessment

```typescript
// scripts/migration-assessment.ts
interface MigrationAssessment {
  source: {
    system: string;
    recordCount: number;
    dataQuality: DataQualityReport;
    fieldMapping: FieldMappingAnalysis;
  };
  target: {
    apolloPlan: string;
    creditBudget: number;
    apiLimits: APILimits;
  };
  risk: {
    level: 'low' | 'medium' | 'high';
    factors: string[];
    mitigations: string[];
  };
  timeline: {
    estimatedDuration: string;
    phases: Phase[];
  };
}

async function assessMigration(sourceConfig: any): Promise<MigrationAssessment> {
  // Analyze source data
  const sourceAnalysis = await analyzeSourceData(sourceConfig);

  // Check Apollo capacity
  const apolloCapacity = await checkApolloCapacity();

  // Calculate risks
  const risks = calculateRisks(sourceAnalysis, apolloCapacity);

  // Estimate timeline
  const timeline = estimateTimeline(sourceAnalysis, apolloCapacity);

  return {
    source: sourceAnalysis,
    target: apolloCapacity,
    risk: risks,
    timeline,
  };
}

async function analyzeSourceData(config: any): Promise<SourceAnalysis> {
  const records = await fetchSourceRecords(config);

  return {
    system: config.system,
    recordCount: records.length,
    dataQuality: {
      emailValid: records.filter(r => isValidEmail(r.email)).length / records.length,
      emailPresent: records.filter(r => r.email).length / records.length,
      phonePresent: records.filter(r => r.phone).length / records.length,
      companyPresent: records.filter(r => r.company).length / records.length,
      duplicates: findDuplicates(records).length,
    },
    fieldMapping: analyzeFields(records),
  };
}
```

### Field Mapping

```typescript
// src/migration/field-mapper.ts
interface FieldMapping {
  sourceField: string;
  targetField: string;
  transform?: (value: any) => any;
  required: boolean;
  validation?: (value: any) => boolean;
}

const SALESFORCE_TO_APOLLO: FieldMapping[] = [
  {
    sourceField: 'Email',
    targetField: 'email',
    required: true,
    validation: isValidEmail,
  },
  {
    sourceField: 'FirstName',
    targetField: 'first_name',
    required: false,
  },
  {
    sourceField: 'LastName',
    targetField: 'last_name',
    required: false,
  },
  {
    sourceField: 'Title',
    targetField: 'title',
    required: false,
    transform: normalizeTitle,
  },
  {
    sourceField: 'Phone',
    targetField: 'phone',
    required: false,
    transform: normalizePhone,
  },
  {
    sourceField: 'Account.Name',
    targetField: 'organization_name',
    required: false,
  },
  {
    sourceField: 'Account.Website',
    targetField: 'organization_domain',
    transform: extractDomain,
    required: false,
  },
  {
    sourceField: 'LinkedIn_URL__c',
    targetField: 'linkedin_url',
    required: false,
    validation: isValidLinkedInUrl,
  },
];

const HUBSPOT_TO_APOLLO: FieldMapping[] = [
  { sourceField: 'properties.email', targetField: 'email', required: true },
  { sourceField: 'properties.firstname', targetField: 'first_name', required: false },
  { sourceField: 'properties.lastname', targetField: 'last_name', required: false },
  { sourceField: 'properties.jobtitle', targetField: 'title', required: false },
  { sourceField: 'properties.phone', targetField: 'phone', required: false },
  { sourceField: 'properties.company', targetField: 'organization_name', required: false },
  { sourceField: 'properties.website', targetField: 'organization_domain', transform: extractDomain, required: false },
];

function transformRecord(record: any, mappings: FieldMapping[]): any {
  const transformed: any = {};
  const errors: string[] = [];

  for (const mapping of mappings) {
    const value = getNestedValue(record, mapping.sourceField);

    if (mapping.required && !value) {
      errors.push(`Missing required field: ${mapping.sourceField}`);
      continue;
    }

    if (value) {
      let transformedValue = mapping.transform ? mapping.transform(value) : value;

      if (mapping.validation && !mapping.validation(transformedValue)) {
        errors.push(`Invalid value for ${mapping.sourceField}: ${value}`);
        continue;
      }

      transformed[mapping.targetField] = transformedValue;
    }
  }

  return { data: transformed, errors };
}
```

## Migration Execution

### Phased Migration Strategy

```typescript
// src/migration/phased-migration.ts
interface MigrationPhase {
  name: string;
  percentage: number;
  criteria: any;
  validation: () => Promise<boolean>;
  rollbackPlan: () => Promise<void>;
}

const MIGRATION_PHASES: MigrationPhase[] = [
  {
    name: 'Pilot',
    percentage: 1,
    criteria: { createdAt: { gt: '2024-01-01' }, hasEmail: true },
    validation: async () => {
      const migrated = await getMigratedCount('pilot');
      const errors = await getErrorCount('pilot');
      return errors / migrated < 0.01; // Less than 1% error rate
    },
    rollbackPlan: async () => {
      await deleteApolloContacts({ tag: 'migration-pilot' });
    },
  },
  {
    name: 'Early Adopters',
    percentage: 10,
    criteria: { hasEmail: true, engagementScore: { gt: 50 } },
    validation: async () => {
      // Validate data integrity
      const sample = await sampleMigratedRecords(100);
      const integrity = await validateDataIntegrity(sample);
      return integrity.score > 0.95;
    },
    rollbackPlan: async () => {
      await deleteApolloContacts({ tag: 'migration-early' });
    },
  },
  {
    name: 'Main Migration',
    percentage: 75,
    criteria: { hasEmail: true },
    validation: async () => {
      // Full validation suite
      return await runFullValidation();
    },
    rollbackPlan: async () => {
      // This is risky - need careful planning
      console.warn('Full rollback required - contact support');
    },
  },
  {
    name: 'Cleanup',
    percentage: 14,
    criteria: {}, // Remaining records
    validation: async () => true,
    rollbackPlan: async () => {},
  },
];

async function executePhasedMigration(): Promise<void> {
  for (const phase of MIGRATION_PHASES) {
    console.log(`Starting phase: ${phase.name} (${phase.percentage}%)`);

    // Get records for this phase
    const records = await getRecordsForPhase(phase);
    console.log(`Found ${records.length} records for ${phase.name}`);

    // Migrate in batches
    const batchSize = 100;
    for (let i = 0; i < records.length; i += batchSize) {
      const batch = records.slice(i, i + batchSize);
      await migrateBatch(batch, phase.name);

      // Progress update
      console.log(`Progress: ${i + batch.length}/${records.length}`);

      // Rate limit
      await sleep(1000);
    }

    // Validate phase
    const isValid = await phase.validation();
    if (!isValid) {
      console.error(`Phase ${phase.name} validation failed!`);
      await phase.rollbackPlan();
      throw new Error(`Migration failed at phase: ${phase.name}`);
    }

    console.log(`Phase ${phase.name} completed successfully`);
  }
}
```

### Batch Migration Worker

```typescript
// src/migration/batch-worker.ts
import { Queue, Worker, Job } from 'bullmq';

interface MigrationJob {
  records: any[];
  phase: string;
  batchNumber: number;
}

const migrationQueue = new Queue('apollo-migration');

// Producer
async function enqueueMigrationBatch(
  records: any[],
  phase: string,
  batchNumber: number
): Promise<void> {
  await migrationQueue.add('migrate', {
    records,
    phase,
    batchNumber,
  }, {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 5000,
    },
    removeOnComplete: 100,
    removeOnFail: false,
  });
}

// Consumer
const worker = new Worker('apollo-migration', async (job: Job<MigrationJob>) => {
  const { records, phase, batchNumber } = job.data;

  const results = {
    success: 0,
    failed: 0,
    errors: [] as any[],
  };

  for (const record of records) {
    try {
      // Transform record
      const transformed = transformRecord(record, getMapping(record.source));

      if (transformed.errors.length > 0) {
        results.failed++;
        results.errors.push({ record, errors: transformed.errors });
        continue;
      }

      // Create in Apollo
      await apollo.createContact(transformed.data);

      // Store mapping for rollback
      await storeMigrationMapping(record.id, transformed.data.id, phase);

      results.success++;
    } catch (error: any) {
      results.failed++;
      results.errors.push({ record, error: error.message });
    }

    // Update job progress
    await job.updateProgress((results.success + results.failed) / records.length * 100);
  }

  // Log results
  console.log(`Batch ${batchNumber}: ${results.success} success, ${results.failed} failed`);

  if (results.errors.length > 0) {
    await storeFailedRecords(results.errors, phase, batchNumber);
  }

  return results;
});
```

## Validation & Reconciliation

```typescript
// src/migration/validation.ts
interface ValidationResult {
  totalSource: number;
  totalTarget: number;
  matched: number;
  mismatched: number;
  missing: number;
  extra: number;
  fieldDiscrepancies: FieldDiscrepancy[];
}

interface FieldDiscrepancy {
  recordId: string;
  field: string;
  sourceValue: any;
  targetValue: any;
}

async function validateMigration(): Promise<ValidationResult> {
  // Get all source records
  const sourceRecords = await fetchAllSourceRecords();
  const sourceMap = new Map(sourceRecords.map(r => [r.email, r]));

  // Get all migrated records from Apollo
  const apolloRecords = await fetchAllApolloContacts();
  const apolloMap = new Map(apolloRecords.map(r => [r.email, r]));

  const result: ValidationResult = {
    totalSource: sourceRecords.length,
    totalTarget: apolloRecords.length,
    matched: 0,
    mismatched: 0,
    missing: 0,
    extra: 0,
    fieldDiscrepancies: [],
  };

  // Check source records exist in Apollo
  for (const [email, sourceRecord] of sourceMap) {
    const apolloRecord = apolloMap.get(email);

    if (!apolloRecord) {
      result.missing++;
      continue;
    }

    // Compare fields
    const discrepancies = compareRecords(sourceRecord, apolloRecord);
    if (discrepancies.length === 0) {
      result.matched++;
    } else {
      result.mismatched++;
      result.fieldDiscrepancies.push(...discrepancies);
    }
  }

  // Check for extra records in Apollo
  for (const [email] of apolloMap) {
    if (!sourceMap.has(email)) {
      result.extra++;
    }
  }

  return result;
}

function compareRecords(source: any, target: any): FieldDiscrepancy[] {
  const discrepancies: FieldDiscrepancy[] = [];
  const fieldsToCompare = ['first_name', 'last_name', 'title', 'phone'];

  for (const field of fieldsToCompare) {
    const sourceValue = normalizeValue(source[field]);
    const targetValue = normalizeValue(target[field]);

    if (sourceValue !== targetValue) {
      discrepancies.push({
        recordId: source.id,
        field,
        sourceValue,
        targetValue,
      });
    }
  }

  return discrepancies;
}
```

## Rollback Strategy

```typescript
// src/migration/rollback.ts
interface RollbackPlan {
  phase: string;
  recordIds: string[];
  timestamp: Date;
}

async function createRollbackPlan(phase: string): Promise<RollbackPlan> {
  const mappings = await prisma.migrationMapping.findMany({
    where: { phase },
  });

  return {
    phase,
    recordIds: mappings.map(m => m.apolloId),
    timestamp: new Date(),
  };
}

async function executeRollback(plan: RollbackPlan): Promise<void> {
  console.log(`Rolling back ${plan.recordIds.length} records from phase: ${plan.phase}`);

  // Delete from Apollo in batches
  const batchSize = 50;
  for (let i = 0; i < plan.recordIds.length; i += batchSize) {
    const batch = plan.recordIds.slice(i, i + batchSize);

    await Promise.all(
      batch.map(async (id) => {
        try {
          // Apollo may not have delete API - mark as inactive instead
          await apollo.updateContact(id, { status: 'inactive' });
        } catch (error) {
          console.error(`Failed to rollback contact ${id}:`, error);
        }
      })
    );

    console.log(`Rollback progress: ${i + batch.length}/${plan.recordIds.length}`);
    await sleep(1000);
  }

  // Update migration mappings
  await prisma.migrationMapping.updateMany({
    where: { phase: plan.phase },
    data: { rolledBack: true, rolledBackAt: new Date() },
  });

  console.log(`Rollback complete for phase: ${plan.phase}`);
}
```

## Migration Dashboard

```typescript
// src/routes/admin/migration.ts
router.get('/migration/status', async (req, res) => {
  const status = {
    phases: await getMigrationPhaseStatus(),
    progress: await getOverallProgress(),
    errors: await getRecentErrors(50),
    queue: await getQueueStatus(),
  };

  res.json(status);
});

router.post('/migration/pause', async (req, res) => {
  await migrationQueue.pause();
  res.json({ status: 'paused' });
});

router.post('/migration/resume', async (req, res) => {
  await migrationQueue.resume();
  res.json({ status: 'resumed' });
});

router.post('/migration/rollback/:phase', async (req, res) => {
  const plan = await createRollbackPlan(req.params.phase);
  await executeRollback(plan);
  res.json({ status: 'rolled back', plan });
});
```

## Output
- Pre-migration assessment framework
- Field mapping configurations
- Phased migration strategy
- Batch processing workers
- Validation and reconciliation
- Rollback procedures

## Error Handling
| Issue | Resolution |
|-------|------------|
| Field mapping error | Review and fix mapping |
| Batch failure | Retry with smaller batch |
| Validation mismatch | Investigate and re-migrate |
| Rollback needed | Execute phase rollback |

## Resources
- [Apollo Import Documentation](https://knowledge.apollo.io/hc/en-us/articles/4415154183053)
- [Salesforce Export Guide](https://help.salesforce.com/s/articleView?id=sf.exporting_data.htm)
- [HubSpot Export Guide](https://knowledge.hubspot.com/crm-setup/export-contacts-companies-deals-or-tickets)

## Completion
This completes the Apollo skill pack. All 24 skills are now available for Claude Code users integrating with Apollo.io.
