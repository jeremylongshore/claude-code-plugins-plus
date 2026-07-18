---
name: clickhouse-core-workflow-a
description: |
  Design ClickHouse schemas with MergeTree engines, ORDER BY keys, and
  partitioning.

  Use when creating new tables, choosing an engine, designing sort keys, or
  modeling data for analytical workloads on ClickHouse or ClickHouse Cloud.

  Trigger with "clickhouse schema design", "clickhouse table design",
  "clickhouse ORDER BY", "clickhouse partitioning", "MergeTree table".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
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
# ClickHouse Schema Design (Core Workflow A)

## Overview

Design ClickHouse tables with correct engine selection, ORDER BY keys,
partitioning, and codec choices for analytical workloads. This skill covers the
four schema decisions that determine query speed and storage cost — engine,
sort key, partition expression, and column codecs — then points to
`references/` for full DDL and the programmatic apply path.

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

### Step 3: Write the Table DDL

Start from the append-only event skeleton below, then adapt the engine and sort
key to your access pattern. Full DDL for the three canonical shapes — event
analytics (`MergeTree`), user profiles (`ReplacingMergeTree`), and daily
aggregation (`AggregatingMergeTree`) — plus column codec choices is in
[schema examples](references/schema-examples.md).

```sql
CREATE TABLE analytics.events (
    event_id     UUID DEFAULT generateUUIDv4(),
    tenant_id    UInt32,
    event_type   LowCardinality(String),
    user_id      UInt64,
    properties   String CODEC(ZSTD(3)),  -- JSON blob, compress well
    created_at   DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
ORDER BY (tenant_id, event_type, toDate(created_at), user_id)
PARTITION BY toYYYYMM(created_at)
TTL created_at + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;
```

### Step 4: Choose a Partition Expression

`toYYYYMM(date)` (monthly) is the right default for most time-series tables —
target 10-1000 parts per partition. Each partition creates separate parts on
disk, so over-partitioning (e.g., by `user_id`) creates millions of tiny parts
and kills performance. Full partition matrix and the Node.js apply path are in
[partitioning and applying schema](references/implementation.md).

## Output

Applying this skill produces:

- **Table DDL** — a `CREATE TABLE` statement with an engine, ORDER BY sort key,
  `PARTITION BY` expression, per-column codecs, and (optionally) a `TTL` clause.
- **A rationale** for each decision — why this engine, why this sort-key order,
  why this partition granularity — so the schema is reviewable, not cargo-culted.
- **Optional apply script** — a `@clickhouse/client` `command()` call that runs
  the DDL from application code (see the reference), keeping schema in version
  control alongside the service.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ORDER BY expression not in primary key` | PRIMARY KEY != ORDER BY | Remove explicit PRIMARY KEY or align |
| `Too many parts (300+)` | Over-partitioning | Use coarser partition expression |
| `Cannot convert String to UInt64` | Wrong data type | Match insert types to schema |
| `TTL expression type mismatch` | TTL on non-date column | TTL must reference DateTime column |

## Examples

- **Append-only clickstream** — `MergeTree`, sort key `(tenant_id, event_type,
  toDate(created_at), user_id)`, monthly partitions, 1-year TTL.
- **Mutable user profiles (upserts)** — `ReplacingMergeTree(updated_at)`,
  `ORDER BY user_id`, read with `FINAL` for deduplicated rows.
- **Pre-aggregated daily rollups** — `AggregatingMergeTree` targeting a
  materialized view, storing `AggregateFunction(uniq, UInt64)` state.

Full DDL for all three shapes plus column codec choices:
[schema examples](references/schema-examples.md). The Node.js apply path
(`client.command()` with `@clickhouse/client`) and the full partition matrix:
[partitioning and applying schema](references/implementation.md).

## Resources

- [MergeTree Engine](https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree)
- [ReplacingMergeTree](https://clickhouse.com/docs/engines/table-engines/mergetree-family/replacingmergetree)
- [Codecs & Compression](https://clickhouse.com/docs/sql-reference/statements/create/table#column_compression_codec)

## Next Steps

For inserting and querying data — batch inserts, async inserts, and query
patterns against these tables — see `clickhouse-core-workflow-b`.
