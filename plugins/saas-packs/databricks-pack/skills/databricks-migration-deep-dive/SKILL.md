---
name: databricks-migration-deep-dive
description: |
  Execute comprehensive platform migrations to Databricks from legacy systems.
  Use when migrating from on-premises Hadoop, other cloud platforms,
  or legacy data warehouses to Databricks.
  Trigger with phrases like "migrate to databricks", "hadoop migration",
  "snowflake to databricks", "legacy migration", "data warehouse migration".
allowed-tools: Read, Write, Edit, Bash(databricks:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive migration strategies for moving to Databricks from Hadoop, Snowflake, Redshift, Synapse, or legacy data warehouses.

## Prerequisites
- Access to source and target systems
- Understanding of current data architecture
- Migration timeline and stakeholder alignment

## Migration Patterns

| Source | Pattern | Complexity | Timeline |
|--------|---------|------------|----------|
| On-prem Hadoop | Lift-and-shift + modernize | High | 6-12 months |
| Snowflake | Parallel run + cutover | Medium | 3-6 months |
| AWS Redshift | ETL rewrite + data copy | Medium | 3-6 months |
| Legacy DW (Oracle/Teradata) | Full rebuild | High | 12-18 months |

## Instructions

### Step 1: Discovery and Assessment
Inventory all source tables with metadata (size, partitions, dependencies, data classification). Generate prioritized migration plan with wave assignments.

### Step 2: Schema Migration
Convert source schemas to Delta Lake compatible types. Handle type conversions (char->string, tinyint->int). Enable auto-optimize on target tables.

### Step 3: Data Migration
Batch large tables by partition. Validate row counts and schema match after each table migration.

### Step 4: ETL/Pipeline Migration
Convert spark-submit/Oozie jobs to Databricks jobs. Update paths, remove Hive metastore references, adapt for Unity Catalog.

### Step 5: Cutover Planning
Execute 6-step cutover: validate -> disable source -> final sync -> enable Databricks -> update apps -> monitor. Each step has rollback procedure.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for assessment scripts, schema conversion, data migration with batching, ETL conversion, and cutover plan generation.

## Output
- Migration assessment with prioritized plan
- Schema migration automated
- Data migration pipeline with validation
- Cutover plan with rollback procedures

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Schema incompatibility | Unsupported types | Use type conversion mappings |
| Data loss | Truncation during migration | Validate counts at each step |
| Performance issues | Large tables | Use partitioned migration |
| Dependency conflicts | Wrong migration order | Analyze dependencies first |

## Examples

### Quick Validation
```sql
SELECT 'source' as system, COUNT(*) FROM hive_metastore.db.table
UNION ALL SELECT 'target' as system, COUNT(*) FROM migrated.db.table;
```

## Resources
- [Databricks Migration Guide](https://docs.databricks.com/migration/index.html)
- [Delta Lake Migration](https://docs.databricks.com/delta/migration.html)
- [Unity Catalog Migration](https://docs.databricks.com/data-governance/unity-catalog/migrate.html)

## Completion
Provides coverage for Databricks platform migrations.