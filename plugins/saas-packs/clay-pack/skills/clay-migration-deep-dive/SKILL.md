---
name: clay-migration-deep-dive
description: |
  Execute Clay major re-architecture and migration strategies with strangler fig pattern.
  Use when migrating to or from Clay, performing major version upgrades,
  or re-platforming existing integrations to Clay.
  Trigger with phrases like "migrate clay", "clay migration",
  "switch to clay", "clay replatform", "clay upgrade major".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview

Comprehensive guide for migrating to or from Clay, or major version upgrades using the strangler fig pattern.

## Prerequisites

- Current system documentation
- Clay SDK installed
- Feature flag infrastructure
- Rollback strategy tested

## Migration Types

| Type | Complexity | Duration | Risk |
|------|-----------|----------|------|
| Fresh install | Low | Days | Low |
| From competitor | Medium | Weeks | Medium |
| Major version | Medium | Weeks | Medium |
| Full replatform | High | Months | High |

## Instructions

### Assess current configuration (Week 1-2)

Inventory all files referencing Clay, count integration points, and document dependencies. Build a `MigrationInventory` with data types, record counts, and customizations.

### Step 2: Build Adapter Layer (Week 3-4)

Create a `ServiceAdapter` interface with CRUD operations. Implement `ClayAdapter` with data transformation from old format to Clay format. This enables gradual migration.

### Step 3: Migrate Data (Week 5-6)

Run batch data migration (100 records per batch) with error collection. Track progress and log failed batches for retry.

### Step 4: Shift Traffic (Week 7-8)

Use feature flags to gradually route traffic: start at 0%, increase to 10%, 50%, then 100%. Use `getServiceAdapter()` to select Clay vs legacy based on flag percentage.

### Step 5: Validate and Cut Over

Run validation checks: data count match, API functionality, performance baseline, and error rates. All must pass before completing the migration.

### Rollback Plan

Disable Clay via environment variable and restart pods. For data rollback, restore from backup. Verify via health endpoint.

For complete TypeScript implementations, assessment scripts, and validation code, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- Migration assessment complete
- Adapter layer implemented
- Data migrated successfully
- Traffic fully shifted to Clay

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Data mismatch | Transform errors | Validate transform logic |
| Performance drop | No caching | Add caching layer |
| Rollback triggered | Errors spiked | Reduce traffic percentage |
| Validation failed | Missing data | Check batch processing |

## Resources

- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Clay Migration Guide](https://docs.clay.com/migration)

## Next Steps

For advanced troubleshooting, see `clay-advanced-troubleshooting`.

## Examples

**Basic usage**: Apply clay migration deep dive to a standard project setup with default configuration options.

**Advanced scenario**: Customize clay migration deep dive for production environments with multiple constraints and team-specific requirements.