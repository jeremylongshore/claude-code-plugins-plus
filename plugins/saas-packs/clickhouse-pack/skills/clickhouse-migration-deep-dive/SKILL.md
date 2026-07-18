---
name: clickhouse-migration-deep-dive
description: |
  Execute ClickHouse schema migrations — ALTER TABLE operations, data migration
  between engines, versioned migration runners, and zero-downtime schema changes.
  Use when modifying ClickHouse schemas, migrating data between tables, or
  implementing versioned migration workflows.
  Trigger with "clickhouse migration", "clickhouse ALTER TABLE",
  "clickhouse schema change", "migrate clickhouse", "clickhouse add column",
  or "clickhouse schema migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Migration Deep Dive

## Overview

Plan and execute ClickHouse schema migrations: column changes, engine migrations,
ORDER BY modifications, and versioned migration runners. ClickHouse ALTER
operations behave unlike PostgreSQL/MySQL — most are asynchronous **mutations**
that rewrite data parts in the background, and some changes (ORDER BY, engine)
require full table recreation. This skill walks the safe path for each.

## Prerequisites

- ClickHouse admin access
- Backup of production data (see `clickhouse-prod-checklist`)
- Test environment for validation

## Instructions

Follow these steps in order. SQL and runner code for each step live in the
linked reference files — keep them open while you work.

### Step 1: Classify the operation

Decide whether your change is lightweight (instant, metadata only) or a
heavyweight mutation (rewrites parts in the background):

```sql
-- Lightweight (instant): ADD COLUMN, RENAME COLUMN, COMMENT COLUMN
ALTER TABLE events ADD COLUMN country LowCardinality(String) DEFAULT '';

-- Heavyweight (mutation): MODIFY COLUMN, DROP COLUMN, DELETE, UPDATE
ALTER TABLE events MODIFY COLUMN properties String CODEC(ZSTD(3));

-- Always monitor mutation progress
SELECT database, table, mutation_id, is_done, parts_to_do
FROM system.mutations WHERE NOT is_done ORDER BY create_time;
```

### Step 2: Run column operations

Use `Edit`/`Write` to author the `ALTER TABLE` statements, then apply them.
Add/modify/drop columns, set materialized defaults, and attach codecs. Full DDL
semantics and every column-operation variant:
[DDL & column operations](references/column-operations.md).

### Step 3: Recreate the table for ORDER BY / engine changes

ClickHouse has no `MODIFY ORDER BY` and no in-place engine change. Create a new
table, `INSERT ... SELECT` the data, then atomically `RENAME TABLE` to swap.
Full create → copy → swap → verify → drop recipe for both cases:
[table recreation](references/table-recreation.md).

### Step 4: Wire a versioned migration runner

For repeatable, tracked migrations, drive numbered `.sql` files through a runner
that records applied versions in a `_migrations` table and stops on first
failure. Use `Write` to scaffold `runner.ts` and the `sql/NNN-*.sql` files, then
run it with `npm`/`node`. Full runner, example migration files, and the
operation downtime matrix: [migration runner](references/migration-runner.md).

## Output

Applying this skill produces:

- **Executed ALTER statements** or recreated-and-swapped tables, with mutations
  confirmed complete via `system.mutations WHERE NOT is_done` (empty result).
- **Migration `.sql` files** under `migrations/sql/` (e.g. `001-create-events.sql`)
  and a `runner.ts` that records each applied version in the `_migrations` table.
- **Verification counts** — row counts on the new/old tables matching before the
  old table is dropped.

## Pre-Migration Checklist

- [ ] Backup production data (`BACKUP TABLE ... TO S3(...)`)
- [ ] Test migration on staging with production-like data
- [ ] Check disk space (mutations create temporary extra parts)
- [ ] Schedule during low-traffic window (for heavy mutations)
- [ ] Prepare rollback procedure
- [ ] Verify mutation completes (`system.mutations WHERE NOT is_done`)

## Examples

**Add a column (instant, no data rewrite):**

```sql
ALTER TABLE analytics.events
    ADD COLUMN IF NOT EXISTS country LowCardinality(String) DEFAULT ''
    AFTER user_id;
```

**Change ORDER BY via table recreation and atomic swap:**

```sql
CREATE TABLE analytics.events_v2 AS analytics.events
ENGINE = MergeTree()
ORDER BY (tenant_id, event_type, toDate(created_at))
PARTITION BY toYYYYMM(created_at);

INSERT INTO analytics.events_v2 SELECT * FROM analytics.events;

RENAME TABLE
    analytics.events TO analytics.events_old,
    analytics.events_v2 TO analytics.events;
```

More worked examples: column codecs and materialized defaults in
[column operations](references/column-operations.md), the MergeTree →
ReplacingMergeTree engine swap in [table recreation](references/table-recreation.md),
and end-to-end versioned files in [migration runner](references/migration-runner.md).

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot ALTER: table has mutations` | Mutation queue full | Wait or cancel: `KILL MUTATION WHERE ...` |
| `Column already exists` | Re-running migration | Use `IF NOT EXISTS` |
| `Cannot convert type` | Incompatible type change | Create new column, backfill, drop old |
| `Not enough disk space` | Mutation doubles data temporarily | Free space, then retry |

## Resources

- [ALTER TABLE Reference](https://clickhouse.com/docs/sql-reference/statements/alter)
- [Column Manipulations](https://clickhouse.com/docs/sql-reference/statements/alter/column)
- [Schema Migration Tools](https://clickhouse.com/docs/knowledgebase/schema_migration_tools)
- [Mutations](https://clickhouse.com/docs/guides/developer/mutations)
- For architecture patterns, see `clickhouse-reference-architecture`.
