---
name: coderabbit-migration-deep-dive
description: |
  Execute CodeRabbit major re-architecture and migration strategies with strangler fig pattern.
  Use when migrating to or from CodeRabbit, performing major version upgrades,
  or re-platforming existing integrations to CodeRabbit.
  Trigger with phrases like "migrate coderabbit", "coderabbit migration",
  "switch to coderabbit", "coderabbit replatform", "coderabbit upgrade major".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Comprehensive guide for migrating to or from CodeRabbit, or major version upgrades.

## Prerequisites
- Current system documentation
- CodeRabbit SDK installed
- Feature flag infrastructure
- Rollback strategy tested

## Migration Types

| Type | Complexity | Duration | Risk |
|------|-----------|----------|------|
| Fresh install | Low | Days | Low |
| From competitor | Medium | Weeks | Medium |
| Major version | Medium | Weeks | Medium |
| Full replatform | High | Months | High |

## Pre-Migration Assessment

### Step 1: Current State Analysis
```bash
set -euo pipefail
# Document current implementation
find . -name "*.ts" -o -name "*.py" | xargs grep -l "coderabbit" > coderabbit-files.txt

# Count integration points
wc -l coderabbit-files.txt

# Identify dependencies
npm list | grep coderabbit
pip freeze | grep coderabbit
```

### Step 2: Data Inventory
```typescript
interface MigrationInventory {
  dataTypes: string[];
  recordCounts: Record<string, number>;
  dependencies: string[];
  integrationPoints: string[];
  customizations: string[];
}

async function assessCodeRabbitMigration(): Promise<MigrationInventory> {
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
│   System    │ ──▶ │  CodeRabbit   │
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
set -euo pipefail
# Install CodeRabbit SDK
npm install @coderabbit/sdk

# Configure credentials
cp .env.example .env.coderabbit
# Edit with new credentials

# Verify connectivity
node -e "require('@coderabbit/sdk').ping()"
```

### Phase 2: Adapter Layer (Week 3-4)
```typescript
// src/adapters/coderabbit.ts
interface ServiceAdapter {
  create(data: CreateInput): Promise<Resource>;
  read(id: string): Promise<Resource>;
  update(id: string, data: UpdateInput): Promise<Resource>;
  delete(id: string): Promise<void>;
}

class CodeRabbitAdapter implements ServiceAdapter {
  async create(data: CreateInput): Promise<Resource> {
    const coderabbitData = this.transform(data);
    return coderabbitClient.create(coderabbitData);
  }

  private transform(data: CreateInput): CodeRabbitInput {
    // Map from old format to CodeRabbit format
  }
}
```

### Phase 3: Data Migration (Week 5-6)
```typescript
async function migrateCodeRabbitData(): Promise<MigrationResult> {
  const batchSize = 100;
  let processed = 0;
  let errors: MigrationError[] = [];

  for await (const batch of oldSystem.iterateBatches(batchSize)) {
    try {
      const transformed = batch.map(transform);
      await coderabbitClient.batchCreate(transformed);
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
  const coderabbitPercentage = getFeatureFlag('coderabbit_migration_percentage');

  if (Math.random() * 100 < coderabbitPercentage) {
    return new CodeRabbitAdapter();
  }

  return new LegacyAdapter();
}
```

## Rollback Plan

```bash
set -euo pipefail
# Immediate rollback
kubectl set env deployment/app CODERABBIT_ENABLED=false
kubectl rollout restart deployment/app

# Data rollback (if needed)
./scripts/restore-from-backup.sh --date YYYY-MM-DD

# Verify rollback
curl https://app.yourcompany.com/health | jq '.services.coderabbit'
```

## Post-Migration Validation

```typescript
async function validateCodeRabbitMigration(): Promise<ValidationReport> {
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

## Instructions

### Assess current configuration
Document existing implementation and data inventory.

### Step 2: Build Adapter Layer
Create abstraction layer for gradual migration.

### Step 3: Migrate Data
Run batch data migration with error handling.

### Step 4: Shift Traffic
Gradually route traffic to new CodeRabbit integration.

## Output
- Migration assessment complete
- Adapter layer implemented
- Data migrated successfully
- Traffic fully shifted to CodeRabbit

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Data mismatch | Transform errors | Validate transform logic |
| Performance drop | No caching | Add caching layer |
| Rollback triggered | Errors spiked | Reduce traffic percentage |
| Validation failed | Missing data | Check batch processing |

## Examples

### Quick Migration Status
```typescript
const status = await validateCodeRabbitMigration();
console.log(`Migration ${status.passed ? 'PASSED' : 'FAILED'}`);
status.checks.forEach(c => console.log(`  ${c.name}: ${c.result.success}`));
```

## Resources
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [CodeRabbit Migration Guide](https://docs.coderabbit.com/migration)

## Flagship+ Skills
For advanced troubleshooting, see `coderabbit-advanced-troubleshooting`.