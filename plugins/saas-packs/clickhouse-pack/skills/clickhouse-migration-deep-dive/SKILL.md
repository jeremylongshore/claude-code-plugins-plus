---
name: clickhouse-migration-deep-dive
description: |
  Execute ClickHouse schema migrations — ALTER TABLE operations, data migration
  between engines, versioned migration runners, and zero-downtime schema changes.
  Use when modifying ClickHouse schemas, migrating data between tables,
  or implementing versioned migration workflows.
  Trigger: "clickhouse migration", "clickhouse ALTER TABLE", "clickhouse schema change",
  "migrate clickhouse", "clickhouse add column", "clickhouse schema migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Migration Deep Dive

## Overview

Plan and execute ClickHouse schema migrations: column changes, engine migrations,
ORDER BY modifications, and versioned migration runners.

## Prerequisites

- ClickHouse admin access
- Backup of production data (see `clickhouse-prod-checklist`)
- Test environment for validation

## Instructions

### Step 1: Understanding ClickHouse DDL

ClickHouse ALTER operations are **mutations** — they run asynchronously and
rewrite data parts in the background. This is fundamentally different from
PostgreSQL/MySQL where ALTER is often instant or blocking.

```sql
-- Lightweight operations (instant, metadata only)
ALTER TABLE events ADD COLUMN country LowCardinality(String) DEFAULT '';
ALTER TABLE events RENAME COLUMN old_name TO new_name;
ALTER TABLE events COMMENT COLUMN user_id 'Unique user identifier';

-- Heavyweight operations (mutations — rewrite parts in background)
ALTER TABLE events MODIFY COLUMN properties String CODEC(ZSTD(3));
ALTER TABLE events DROP COLUMN deprecated_field;
ALTER TABLE events DELETE WHERE user_id = 0;
ALTER TABLE events UPDATE email = '' WHERE created_at < '2024-01-01';

-- Check mutation progress
SELECT database, table, mutation_id, command, is_done,
       parts_to_do, create_time
FROM system.mutations
WHERE NOT is_done ORDER BY create_time;
```

### Step 2: Column Operations

```sql
-- Add a column (instant — no data rewrite)
ALTER TABLE analytics.events
    ADD COLUMN IF NOT EXISTS country LowCardinality(String) DEFAULT ''
    AFTER user_id;

-- Add column with materialized default (fills new data, not old)
ALTER TABLE analytics.events
    ADD COLUMN IF NOT EXISTS event_date Date
    MATERIALIZED toDate(created_at);

-- Modify column type (mutation — rewrites all parts)
ALTER TABLE analytics.events
    MODIFY COLUMN user_id UInt64;   -- Was UInt32, now UInt64

-- Drop a column
ALTER TABLE analytics.events
    DROP COLUMN IF EXISTS deprecated_field;

-- Change default value
ALTER TABLE analytics.events
    MODIFY COLUMN created_at DateTime DEFAULT now();

-- Add codec to existing column (mutation)
ALTER TABLE analytics.events
    MODIFY COLUMN properties String CODEC(ZSTD(3));
```

### Step 3: Change ORDER BY (Requires Table Recreation)

ClickHouse does **not** support `ALTER TABLE ... MODIFY ORDER BY`. You must
create a new table and migrate data.

```sql
-- Step 1: Create new table with desired ORDER BY
CREATE TABLE analytics.events_v2 AS analytics.events
ENGINE = MergeTree()
ORDER BY (tenant_id, event_type, toDate(created_at))  -- New key
PARTITION BY toYYYYMM(created_at);

-- Step 2: Copy data
INSERT INTO analytics.events_v2 SELECT * FROM analytics.events;

-- Step 3: Atomic swap (zero-downtime if app handles reconnect)
RENAME TABLE
    analytics.events TO analytics.events_old,
    analytics.events_v2 TO analytics.events;

-- Step 4: Verify and drop old table
SELECT count() FROM analytics.events;
SELECT count() FROM analytics.events_old;
-- When satisfied:
DROP TABLE analytics.events_old;
```

### Step 4: Change Engine (MergeTree to ReplacingMergeTree)

```sql
-- Create new table with ReplacingMergeTree
CREATE TABLE analytics.users_v2 (
    user_id    UInt64,
    email      String,
    plan       LowCardinality(String),
    updated_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY user_id;

-- Migrate data
INSERT INTO analytics.users_v2 SELECT * FROM analytics.users;

-- Atomic swap
RENAME TABLE
    analytics.users TO analytics.users_old,
    analytics.users_v2 TO analytics.users;

DROP TABLE analytics.users_old;
```

### Step 5: Versioned Migration Runner

```typescript
// src/clickhouse/migrations/runner.ts
import { createClient } from '@clickhouse/client';
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';

const client = createClient({ url: process.env.CLICKHOUSE_HOST! });

async function runMigrations() {
  // Create migration tracking table
  await client.command({
    query: `
      CREATE TABLE IF NOT EXISTS _migrations (
          version     String,
          name        String,
          applied_at  DateTime DEFAULT now(),
          checksum    String
      )
      ENGINE = ReplacingMergeTree(applied_at)
      ORDER BY version
    `,
  });

  // Get applied migrations
  const rs = await client.query({
    query: 'SELECT version FROM _migrations FINAL',
    format: 'JSONEachRow',
  });
  const applied = new Set((await rs.json<{ version: string }>()).map((r) => r.version));

  // Read migration files
  const migrationsDir = join(__dirname, 'sql');
  const files = readdirSync(migrationsDir)
    .filter((f) => f.endsWith('.sql'))
    .sort();  // 001-create-events.sql, 002-add-country.sql, etc.

  for (const file of files) {
    const version = file.split('-')[0];  // "001"
    if (applied.has(version)) {
      console.log(`  [SKIP] ${file} (already applied)`);
      continue;
    }

    const sql = readFileSync(join(migrationsDir, file), 'utf-8');
    console.log(`  [APPLY] ${file}...`);

    try {
      // Split on semicolons to handle multi-statement files
      const statements = sql.split(';').filter((s) => s.trim());
      for (const stmt of statements) {
        await client.command({ query: stmt });
      }

      // Record migration
      await client.insert({
        table: '_migrations',
        values: [{ version, name: file, checksum: '' }],
        format: 'JSONEachRow',
      });
      console.log(`  [OK] ${file}`);
    } catch (err) {
      console.error(`  [FAIL] ${file}: ${(err as Error).message}`);
      throw err;  // Stop on first failure
    }
  }

  console.log('Migrations complete.');
}

runMigrations();
```

### Step 6: Example Migration Files

```sql
-- migrations/sql/001-create-events.sql
CREATE TABLE IF NOT EXISTS analytics.events (
    event_id    UUID DEFAULT generateUUIDv4(),
    event_type  LowCardinality(String),
    user_id     UInt64,
    properties  String CODEC(ZSTD(3)),
    created_at  DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (event_type, created_at)
PARTITION BY toYYYYMM(created_at);
```

```sql
-- migrations/sql/002-add-country.sql
ALTER TABLE analytics.events
    ADD COLUMN IF NOT EXISTS country LowCardinality(String) DEFAULT '';
```

```sql
-- migrations/sql/003-add-ttl.sql
ALTER TABLE analytics.events
    MODIFY TTL created_at + INTERVAL 90 DAY;
```

```sql
-- migrations/sql/004-add-bloom-index.sql
ALTER TABLE analytics.events
    ADD INDEX IF NOT EXISTS idx_session session_id TYPE bloom_filter(0.01) GRANULARITY 4;
ALTER TABLE analytics.events MATERIALIZE INDEX idx_session;
```

### Step 7: Migration Best Practices

| Operation | Downtime? | Notes |
|-----------|-----------|-------|
| ADD COLUMN | None | Instant metadata change |
| DROP COLUMN | None | Mutation runs in background |
| MODIFY COLUMN type | None* | Mutation rewrites — can be slow on large tables |
| Change ORDER BY | Brief | Requires table recreation + RENAME |
| Change ENGINE | Brief | Requires table recreation + RENAME |
| ADD INDEX | None | MATERIALIZE runs in background |
| ALTER TTL | None | Takes effect on next merge |

*No application downtime, but queries on the affected column may be slower during mutation.

## Pre-Migration Checklist

- [ ] Backup production data (`BACKUP TABLE ... TO S3(...)`)
- [ ] Test migration on staging with production-like data
- [ ] Check disk space (mutations create temporary extra parts)
- [ ] Schedule during low-traffic window (for heavy mutations)
- [ ] Prepare rollback procedure
- [ ] Verify mutation completes (`system.mutations WHERE NOT is_done`)

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

## Next Steps

For architecture patterns, see `clickhouse-reference-architecture`.
