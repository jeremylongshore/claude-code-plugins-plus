# Juicebox Migration Deep Dive - Implementation Guide

Detailed implementation examples and code patterns.

## Migration Sources

| Source | Complexity | Common Issues |
|--------|------------|---------------|
| LinkedIn Recruiter | Medium | Rate limits, field mapping |
| Greenhouse | Low | Well-documented API |
| Lever | Low | Standard export format |
| Custom ATS | High | Custom transformation needed |
| CSV/Excel | Low | Data quality issues |

## Instructions

### Step 1: Data Assessment
```typescript
// scripts/assess-source-data.ts
interface DataAssessment {
  totalRecords: number;
  uniqueProfiles: number;
  duplicates: number;
  fieldCoverage: Record<string, number>;
  dataQualityScore: number;
  estimatedMigrationTime: string;
}

export async function assessSourceData(
  source: string,
  sampleSize: number = 1000
): Promise<DataAssessment> {
  const sample = await loadSampleData(source, sampleSize);

  const assessment: DataAssessment = {
    totalRecords: sample.total,
    uniqueProfiles: new Set(sample.records.map(r => r.email)).size,
    duplicates: sample.total - new Set(sample.records.map(r => r.email)).size,
    fieldCoverage: calculateFieldCoverage(sample.records),
    dataQualityScore: calculateQualityScore(sample.records),
    estimatedMigrationTime: estimateMigrationTime(sample.total)
  };

  return assessment;
}

function calculateFieldCoverage(records: any[]): Record<string, number> {
  const fields = ['name', 'email', 'title', 'company', 'location', 'phone'];
  const coverage: Record<string, number> = {};

  for (const field of fields) {
    const count = records.filter(r => r[field] && r[field].trim()).length;
    coverage[field] = (count / records.length) * 100;
  }

  return coverage;
}
```

### Step 2: Schema Mapping
```typescript
// lib/migration/schema-mapper.ts
export interface FieldMapping {
  sourceField: string;
  targetField: string;
  transform?: (value: any) => any;
  required: boolean;
}

export const linkedInMapping: FieldMapping[] = [
  { sourceField: 'firstName', targetField: 'first_name', required: true },
  { sourceField: 'lastName', targetField: 'last_name', required: true },
  {
    sourceField: 'fullName',
    targetField: 'name',
    transform: (v) => v || undefined,
    required: false
  },
  { sourceField: 'headline', targetField: 'title', required: false },
  { sourceField: 'companyName', targetField: 'company', required: false },
  {
    sourceField: 'location',
    targetField: 'location',
    transform: normalizeLocation,
    required: false
  },
  {
    sourceField: 'profileUrl',
    targetField: 'linkedin_url',
    transform: normalizeLinkedInUrl,
    required: false
  },
  {
    sourceField: 'connectionDegree',
    targetField: 'metadata.connection_degree',
    required: false
  }
];

export class SchemaMapper {
  constructor(private mappings: FieldMapping[]) {}

  mapRecord(source: Record<string, any>): Record<string, any> {
    const target: Record<string, any> = {};

    for (const mapping of this.mappings) {
      let value = this.getNestedValue(source, mapping.sourceField);

      if (mapping.transform) {
        value = mapping.transform(value);
      }

      if (value !== undefined && value !== null && value !== '') {
        this.setNestedValue(target, mapping.targetField, value);
      } else if (mapping.required) {
        throw new Error(`Required field missing: ${mapping.sourceField}`);
      }
    }

    return target;
  }
}
```

### Step 3: Data Transformation Pipeline
```typescript
// lib/migration/pipeline.ts
import { Transform, pipeline } from 'stream';
import { promisify } from 'util';

const pipelineAsync = promisify(pipeline);

export class MigrationPipeline {
  private stages: Transform[] = [];

  addStage(name: string, transform: (record: any) => any): this {
    this.stages.push(new Transform({
      objectMode: true,
      transform(record, encoding, callback) {
        try {
          const result = transform(record);
          if (result) {
            this.push(result);
          }
          callback();
        } catch (error) {
          callback(error as Error);
        }
      }
    }));
    return this;
  }

  async run(source: Readable, destination: Writable): Promise<MigrationStats> {
    const stats = new MigrationStats();

    const statsTracker = new Transform({
      objectMode: true,
      transform(record, encoding, callback) {
        stats.increment();
        this.push(record);
        callback();
      }
    });

    await pipelineAsync(
      source,
      ...this.stages,
      statsTracker,
      destination
    );

    return stats;
  }
}

// Usage
const pipeline = new MigrationPipeline()
  .addStage('parse', parseCSVRecord)
  .addStage('validate', validateRecord)
  .addStage('deduplicate', deduplicateRecord)
  .addStage('transform', transformToJuiceboxSchema)
  .addStage('enrich', enrichWithMetadata);
```

### Step 4: Bulk Import with Rate Limiting
```typescript
// lib/migration/bulk-importer.ts
export class BulkImporter {
  private rateLimiter: RateLimiter;
  private batchSize: number;
  private maxConcurrent: number;

  constructor(options: {
    requestsPerSecond: number;
    batchSize: number;
    maxConcurrent: number;
  }) {
    this.rateLimiter = new RateLimiter(options.requestsPerSecond);
    this.batchSize = options.batchSize;
    this.maxConcurrent = options.maxConcurrent;
  }

  async import(records: Profile[]): Promise<ImportResult> {
    const result: ImportResult = {
      total: records.length,
      successful: 0,
      failed: 0,
      errors: []
    };

    // Split into batches
    const batches = chunk(records, this.batchSize);

    // Process batches with concurrency limit
    const semaphore = new Semaphore(this.maxConcurrent);

    await Promise.all(batches.map(async (batch, index) => {
      await semaphore.acquire();
      try {
        await this.rateLimiter.wait();
        const batchResult = await this.importBatch(batch);

        result.successful += batchResult.successful;
        result.failed += batchResult.failed;
        result.errors.push(...batchResult.errors);

        logger.info(`Batch ${index + 1}/${batches.length} complete`, {
          successful: batchResult.successful,
          failed: batchResult.failed
        });
      } finally {
        semaphore.release();
      }
    }));

    return result;
  }

  private async importBatch(batch: Profile[]): Promise<BatchResult> {
    try {
      const response = await juiceboxClient.profiles.bulkImport(batch);
      return {
        successful: response.created + response.updated,
        failed: response.failed,
        errors: response.errors
      };
    } catch (error) {
      return {
        successful: 0,
        failed: batch.length,
        errors: [{ message: (error as Error).message, records: batch }]
      };
    }
  }
}
```

### Step 5: Validation and Reconciliation
```typescript
// lib/migration/validator.ts
export class MigrationValidator {
  async validateMigration(
    sourceCount: number,
    destinationQuery: string
  ): Promise<ValidationReport> {
    const report: ValidationReport = {
      sourceCount,
      destinationCount: 0,
      matchRate: 0,
      missingRecords: [],
      dataIntegrityIssues: []
    };

    // Count destination records
    const destResult = await juiceboxClient.search.people({
      query: destinationQuery,
      limit: 0
    });
    report.destinationCount = destResult.total;
    report.matchRate = (report.destinationCount / sourceCount) * 100;

    // Sample validation
    const sampleSize = Math.min(100, sourceCount);
    const sample = await this.getSampleFromSource(sampleSize);

    for (const record of sample) {
      const match = await this.findInDestination(record);
      if (!match) {
        report.missingRecords.push(record.id);
      } else {
        const issues = this.compareRecords(record, match);
        if (issues.length > 0) {
          report.dataIntegrityIssues.push({
            recordId: record.id,
            issues
          });
        }
      }
    }

    return report;
  }

  private compareRecords(source: any, dest: any): string[] {
    const issues: string[] = [];
    const criticalFields = ['name', 'email', 'company'];

    for (const field of criticalFields) {
      if (source[field] !== dest[field]) {
        issues.push(`${field} mismatch: "${source[field]}" vs "${dest[field]}"`);
      }
    }

    return issues;
  }
}
```

### Step 6: Rollback Strategy
```typescript
// lib/migration/rollback.ts
export class MigrationRollback {
  private checkpointFile: string;

  constructor(migrationId: string) {
    this.checkpointFile = `./checkpoints/${migrationId}.json`;
  }

  async saveCheckpoint(state: MigrationState): Promise<void> {
    await fs.writeFile(this.checkpointFile, JSON.stringify(state, null, 2));
  }

  async loadCheckpoint(): Promise<MigrationState | null> {
    try {
      const data = await fs.readFile(this.checkpointFile, 'utf-8');
      return JSON.parse(data);
    } catch {
      return null;
    }
  }

  async rollback(migrationId: string): Promise<RollbackResult> {
    const checkpoint = await this.loadCheckpoint();
    if (!checkpoint) {
      throw new Error('No checkpoint found for rollback');
    }

    // Delete imported records
    const deleted = await juiceboxClient.profiles.bulkDelete({
      filter: { migrationId }
    });

    return {
      recordsRolledBack: deleted.count,
      checkpoint: checkpoint.lastProcessedId
    };
  }
}
```

## Migration Checklist

```markdown

## Post-Migration

- [ ] Reconciliation complete
- [ ] Data integrity verified
- [ ] Source system archived
- [ ] Documentation updated
- [ ] Team training complete
```
