---
name: supabase-migration-deep-dive
description: |
  Supabase major re-architecture and migration strategies.
  Use when migrating to Supabase or performing major version upgrades.
  Trigger with phrases like "migrate supabase", "supabase migration",
  "switch to supabase", "supabase replatform".
allowed-tools: Read, Write, Edit, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Migration Deep Dive

## Overview
Comprehensive guide for migrating to or from Supabase, or major version upgrades.

## Prerequisites
- supabase-install-auth completed
- Current system fully documented
- Test environment available
- Rollback plan defined

## Instructions

### Step 1: Migration Types

| Type | Complexity | Duration | Risk |
|------|-----------|----------|------|
| Fresh install | Low | Days | Low |
| From competitor | Medium | Weeks | Medium |
| Major version | Medium | Weeks | Medium |
| Full replatform | High | Months | High |

## Pre-Migration Assessment

### 1. Current State Analysis
```bash
# Document current implementation
find . -name "*.ts" -o -name "*.py" | xargs grep -l "supabase" > supabase-files.txt

# Count integration points
wc -l supabase-files.txt

# Identify dependencies
npm list | grep supabase
pip freeze | grep supabase
```

### 2. Data Inventory
```typescript
interface MigrationInventory {
  dataTypes: string[];
  recordCounts: Record<string, number>;
  dependencies: string[];
  integrationPoints: string[];
  customizations: string[];
}

async function assessSupabaseMigration(): Promise<MigrationInventory> {
  return {
    dataTypes: await getDataTypes(),
    recordCounts: await getRecordCounts(),
    dependencies: await analyzeDependencies(),
    integrationPoints: await findIntegrationPoints(),
    customizations: await documentCustomizations(),
  };
}
```

## Migration Strategy: Strangler Fig Pattern

```
Phase 1: Parallel Run
┌─────────────┐     ┌─────────────┐
│   Old       │     │   New       │
│   System    │ ──▶ │  Supabase   │
│   (100%)    │     │   (0%)      │
└─────────────┘     └─────────────┘

Phase 2: Gradual Shift
┌─────────────┐     ┌─────────────┐
│   Old       │     │   New       │
│   (50%)     │ ──▶ │   (50%)     │
└─────────────┘     └─────────────┘

Phase 3: Complete
┌─────────────┐     ┌─────────────┐
│   Old       │     │   New       │
│   (0%)      │ ──▶ │   (100%)    │
└─────────────┘     └─────────────┘
```

## Implementation Plan

### Phase 1: Setup (Week 1-2)
```bash
# Install Supabase SDK
npm install @supabase/supabase-js

# Configure credentials
cp .env.example .env.supabase
# Edit with new credentials

# Verify connectivity
node -e "require('@supabase/supabase-js').ping()"
```

### Phase 2: Adapter Layer (Week 3-4)
```typescript
// src/adapters/supabase.ts
interface ServiceAdapter {
  create(data: CreateInput): Promise<Resource>;
  read(id: string): Promise<Resource>;
  update(id: string, data: UpdateInput): Promise<Resource>;
  delete(id: string): Promise<void>;
}

class SupabaseAdapter implements ServiceAdapter {
  async create(data: CreateInput): Promise<Resource> {
    const supabaseData = this.transform(data);
    return supabaseClient.create(supabaseData);
  }

  private transform(data: CreateInput): SupabaseInput {
    // Map from old format to Supabase format
  }
}
```

### Phase 3: Data Migration (Week 5-6)
```typescript
async function migrateSupabaseData(): Promise<MigrationResult> {
  const batchSize = 100;
  let processed = 0;
  let errors: MigrationError[] = [];

  for await (const batch of oldSystem.iterateBatches(batchSize)) {
    try {
      const transformed = batch.map(transform);
      await supabaseClient.batchCreate(transformed);
      processed += batch.length;
    } catch (error) {
      errors.push({ batch, error });
    }

    // Progress update
    console.log(`Migrated ${processed} records`);
  }

  return { processed, errors };
}
```

### Phase 4: Traffic Shift (Week 7-8)
```typescript
// Feature flag controlled traffic split
function getServiceAdapter(): ServiceAdapter {
  const supabasePercentage = getFeatureFlag('supabase_migration_percentage');

  if (Math.random() * 100 < supabasePercentage) {
    return new SupabaseAdapter();
  }

  return new LegacyAdapter();
}
```

## Rollback Plan

```bash
# Immediate rollback
kubectl set env deployment/app SUPABASE_ENABLED=false
kubectl rollout restart deployment/app

# Data rollback (if needed)
./scripts/restore-from-backup.sh --date YYYY-MM-DD

# Verify rollback
curl https://app.yourcompany.com/health | jq '.services.supabase'
```

### Step 2: Post-Migration Validation

```typescript
async function validateSupabaseMigration(): Promise<ValidationReport> {
  const checks = [
    { name: 'Data count match', fn: checkDataCounts },
    { name: 'API functionality', fn: checkApiFunctionality },
    { name: 'Performance baseline', fn: checkPerformance },
    { name: 'Error rates', fn: checkErrorRates },
  ];

  const results = await Promise.all(
    checks.map(async c => ({ name: c.name, result: await c.fn() }))
  );

  return { checks: results, passed: results.every(r => r.result.success) };
}
```

## Output
- Migration plan documented and approved
- Data migrated with validation
- Traffic shifted gradually
- Rollback tested and documented

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Data mismatch | Transform error | Review transformation logic, re-migrate |
| Performance regression | Missing optimization | Profile and optimize new implementation |
| Integration failures | API incompatibility | Update adapter layer for compatibility |
| Rollback needed | Critical issue found | Execute rollback procedure |

## Examples

### Migration Progress Tracking

```typescript
interface MigrationProgress {
  phase: string;
  recordsTotal: number;
  recordsMigrated: number;
  errors: number;
  startTime: Date;
  estimatedCompletion: Date;
}

async function trackMigrationProgress(): Promise<MigrationProgress> {
  const total = await oldSystem.count();
  const migrated = await supabaseClient.count();
  const errors = await getMigrationErrors();

  return {
    phase: 'data-migration',
    recordsTotal: total,
    recordsMigrated: migrated,
    errors: errors.length,
    startTime: migrationStartTime,
    estimatedCompletion: estimateCompletion(migrated, total),
  };
}
```

## Resources
- [Supabase Migration Guide](https://supabase.com/docs/migration)
- [Data Import API](https://supabase.com/docs/import)
- [Migration Best Practices](https://supabase.com/docs/migration-best-practices)

## Flagship+ Skills
For advanced troubleshooting, see `supabase-advanced-troubleshooting`.