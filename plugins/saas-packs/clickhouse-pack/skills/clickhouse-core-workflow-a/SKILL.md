---
name: clickhouse-core-workflow-a
description: |
  Design ClickHouse schemas with MergeTree engines, ORDER BY keys, and partitioning.
  Use when creating new tables, choosing engines, designing sort keys,
  or modeling data for analytical workloads.
  Trigger: "clickhouse schema design", "clickhouse table design",
  "clickhouse ORDER BY", "clickhouse partitioning", "MergeTree table".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Schema Design (Core Workflow A)

## Overview

Design ClickHouse tables with correct engine selection, ORDER BY keys,
partitioning, and codec choices for analytical workloads.

## Prerequisites

- `@clickhouse/client` connected (see `clickhouse-install-auth`)
- Understanding of your query patterns (what you filter and group on)

## Instructions

### Step 1: Choose the Right Engine

| Engine | Best For | Dedup? | Example |
|--------|----------|--------|---------|
| `MergeTree` | General analytics, append-only logs | No | Clickstream, IoT |
| `ReplacingMergeTree` | Mutable rows (upserts) | Yes (on merge) | User profiles, state |
| `SummingMergeTree` | Pre-aggregated counters | Sums numerics | Page view counts |
| `AggregatingMergeTree` | Materialized view targets | Merges states | Dashboards |
| `CollapsingMergeTree` | Stateful row updates | Collapses +-1 | Shopping carts |

**ClickHouse Cloud uses `SharedMergeTree`** — it is a drop-in replacement for
`MergeTree` on Cloud. You do not need to change your DDL.

### Step 2: Design the ORDER BY (Sort Key)

The `ORDER BY` clause is the single most important schema decision. It defines:
- **Primary index** — sparse index over sort-key granules (8192 rows default)
- **Data layout on disk** — rows sorted physically by these columns
- **Query speed** — queries filtering on ORDER BY prefix columns hit fewer granules

**Rules of thumb:**
1. Put low-cardinality filter columns first (`event_type`, `status`)
2. Then high-cardinality columns you filter on (`user_id`, `tenant_id`)
3. End with a time column if you use range filters (`created_at`)
4. Do NOT put high-cardinality columns you never filter on in ORDER BY

```sql
-- Good: filter by tenant, then by time ranges
ORDER BY (tenant_id, event_type, created_at)

-- Bad: UUID first means every query scans the full index
ORDER BY (event_id, created_at)  -- event_id is random UUID
```

### Step 3: Schema Examples

#### Event Analytics Table

```sql
CREATE TABLE analytics.events (
    event_id     UUID DEFAULT generateUUIDv4(),
    tenant_id    UInt32,
    event_type   LowCardinality(String),
    user_id      UInt64,
    session_id   String,
    properties   String CODEC(ZSTD(3)),  -- JSON blob, compress well
    url          String CODEC(ZSTD(1)),
    ip_address   IPv4,
    country      LowCardinality(FixedString(2)),
    created_at   DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
ORDER BY (tenant_id, event_type, toDate(created_at), user_id)
PARTITION BY toYYYYMM(created_at)
TTL created_at + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;
```

#### User Profile Table (Upserts)

```sql
CREATE TABLE analytics.users (
    user_id      UInt64,
    email        String,
    plan         LowCardinality(String),
    mrr_cents    UInt32,
    properties   String CODEC(ZSTD(3)),
    updated_at   DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)   -- keeps latest row per ORDER BY key
ORDER BY user_id;

-- Query with FINAL to get deduplicated results
SELECT * FROM analytics.users FINAL WHERE user_id = 42;
```

#### Daily Aggregation Table

```sql
CREATE TABLE analytics.daily_stats (
    date         Date,
    tenant_id    UInt32,
    event_type   LowCardinality(String),
    event_count  UInt64,
    unique_users AggregateFunction(uniq, UInt64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, event_type, date);
```

### Step 4: Partitioning Guidelines

| Partition Expression | Typical Use | Parts Per Partition |
|---------------------|-------------|---------------------|
| `toYYYYMM(date)` | Most common — monthly | Target 10-1000 |
| `toMonday(date)` | Weekly rollups | More parts, finer drops |
| `toYYYYMMDD(date)` | Daily TTL drops | Many parts — use carefully |
| None | Small tables (<1M rows) | Fine |

**Warning:** Each partition creates separate parts on disk. Over-partitioning
(e.g., by `user_id`) creates millions of tiny parts and kills performance.

### Step 5: Codecs and Compression

```sql
-- Column-level compression codecs
column1  UInt64 CODEC(Delta, ZSTD(3)),      -- Time series / sequential IDs
column2  Float64 CODEC(Gorilla, ZSTD(1)),   -- Floating point (similar values)
column3  String CODEC(ZSTD(3)),              -- General text / JSON
column4  DateTime CODEC(DoubleDelta, ZSTD),  -- Timestamps (near-sequential)
```

## Applying Schema via Node.js

```typescript
import { createClient } from '@clickhouse/client';

const client = createClient({ url: process.env.CLICKHOUSE_HOST! });

async function applySchema() {
  await client.command({ query: 'CREATE DATABASE IF NOT EXISTS analytics' });

  await client.command({
    query: `
      CREATE TABLE IF NOT EXISTS analytics.events (
        event_id   UUID DEFAULT generateUUIDv4(),
        tenant_id  UInt32,
        event_type LowCardinality(String),
        user_id    UInt64,
        payload    String CODEC(ZSTD(3)),
        created_at DateTime DEFAULT now()
      )
      ENGINE = MergeTree()
      ORDER BY (tenant_id, event_type, created_at)
      PARTITION BY toYYYYMM(created_at)
    `,
  });

  console.log('Schema applied.');
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ORDER BY expression not in primary key` | PRIMARY KEY != ORDER BY | Remove explicit PRIMARY KEY or align |
| `Too many parts (300+)` | Over-partitioning | Use coarser partition expression |
| `Cannot convert String to UInt64` | Wrong data type | Match insert types to schema |
| `TTL expression type mismatch` | TTL on non-date column | TTL must reference DateTime column |

## Resources

- [MergeTree Engine](https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree)
- [ReplacingMergeTree](https://clickhouse.com/docs/engines/table-engines/mergetree-family/replacingmergetree)
- [Codecs & Compression](https://clickhouse.com/docs/sql-reference/statements/create/table#column_compression_codec)

## Next Steps

For inserting and querying data, see `clickhouse-core-workflow-b`.
