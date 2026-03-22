---
name: clerk-migration-deep-dive
description: |
  Execute Clerk major re-architecture and migration strategies with strangler fig pattern.
  Use when migrating to or from Clerk, performing major version upgrades,
  or re-platforming existing integrations to Clerk.
  Trigger with phrases like "migrate clerk", "clerk migration",
  "switch to clerk", "clerk replatform", "clerk upgrade major".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clerk]
---

# Clerk Migration Deep Dive

## Overview
Comprehensive guide for migrating to or from Clerk, or major version upgrades.

## Prerequisites
- Current system documentation
- Clerk SDK installed
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
# Document current implementation
find . -name "*.ts" -o -name "*.py" | xargs grep -l "clerk" > clerk-files.txt

# Count integration points
wc -l clerk-files.txt

# Identify dependencies
npm list | grep clerk
pip freeze | grep clerk
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

async function assessClerkMigration(): Promise<MigrationInventory> {
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
│   System    │ ──▶ │  Clerk   │
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
# Install Clerk SDK
npm install @clerk/sdk

# Configure credentials
cp .env.example .env.clerk
# Edit with new credentials

# Verify connectivity
node -e "require('@clerk/sdk').ping()"
```

### Phase 2: Adapter Layer (Week 3-4)
```typescript
// src/adapters/clerk.ts
interface ServiceAdapter {
  create(data: CreateInput): Promise<Resource>;
  read(id: string): Promise<Resource>;
  update(id: string, data: UpdateInput): Promise<Resource>;
  delete(id: string): Promise<void>;
}

class ClerkAdapter implements ServiceAdapter {
  async create(data: CreateInput): Promise<Resource> {
    const clerkData = this.transform(data);
    return clerkClient.create(clerkData);
  }

  private transform(data: CreateInput): ClerkInput {
    // Map from old format to Clerk format
  }
}
```

### Phase 3: Data Migration (Week 5-6)
```typescript
async function migrateClerkData(): Promise<MigrationResult> {
  const batchSize = 100;
  let processed = 0;
  let errors: MigrationError[] = [];

  for await (const batch of oldSystem.iterateBatches(batchSize)) {
    try {
      const transformed = batch.map(transform);
      await clerkClient.batchCreate(transformed);
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
  const clerkPercentage = getFeatureFlag('clerk_migration_percentage');

  if (Math.random() * 100 < clerkPercentage) {
    return new ClerkAdapter();
  }

  return new LegacyAdapter();
}
```

## Rollback Plan

```bash
# Immediate rollback
kubectl set env deployment/app CLERK_ENABLED=false
kubectl rollout restart deployment/app

# Data rollback (if needed)
./scripts/restore-from-backup.sh --date YYYY-MM-DD

# Verify rollback
curl https://app.yourcompany.com/health | jq '.services.clerk'
```

## Post-Migration Validation

```typescript
async function validateClerkMigration(): Promise<ValidationReport> {
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

### Step 1: Assess Current State
Document existing implementation and data inventory.

### Step 2: Build Adapter Layer
Create abstraction layer for gradual migration.

### Step 3: Migrate Data
Run batch data migration with error handling.

### Step 4: Shift Traffic
Gradually route traffic to new Clerk integration.

## Output
- Migration assessment complete
- Adapter layer implemented
- Data migrated successfully
- Traffic fully shifted to Clerk

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
const status = await validateClerkMigration();
console.log(`Migration ${status.passed ? 'PASSED' : 'FAILED'}`);
status.checks.forEach(c => console.log(`  ${c.name}: ${c.result.success}`));
```

## Resources
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Clerk Migration Guide](https://docs.clerk.com/migration)

## Flagship+ Skills
For advanced troubleshooting, see `clerk-advanced-troubleshooting`.