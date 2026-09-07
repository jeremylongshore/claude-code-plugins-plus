---
name: clickhouse-reference-architecture
description: |
  Production reference architecture for ClickHouse-backed applications —
  project layout, data flow, multi-tenant patterns, and operational topology.
  Use when designing a new ClickHouse system, reviewing an existing analytics
  architecture, or establishing standards for ClickHouse integrations.
  Trigger with "clickhouse architecture", "clickhouse project structure",
  "clickhouse design", "clickhouse multi-tenant", "clickhouse reference".
allowed-tools: Read, Grep
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
# ClickHouse Reference Architecture

## Overview

Production-grade architecture for ClickHouse analytics platforms covering project
layout, data flow, multi-tenancy, and operational patterns. Work through the five
steps below to get the high-level shape, then drill into the linked reference files
for the full DDL, client code, and tenancy trade-offs.

## Prerequisites

- Understanding of ClickHouse fundamentals — table engines, `ORDER BY` sort keys,
  and partitioning.
- A TypeScript/Node.js project (the client examples use `@clickhouse/client`).
- When reviewing an existing codebase, `Grep` for `createClient(` to locate the
  current client module and `Read` the SQL files under `clickhouse/schemas/`.

## Instructions

### Step 1: Project Structure

Keep SQL DDL as the source of truth under `clickhouse/schemas/`, named query
functions under `clickhouse/queries/`, and ingestion/API/jobs in sibling modules.

```
my-analytics-platform/
├── src/
│   ├── clickhouse/
│   │   ├── client.ts           # Singleton client with health checks
│   │   ├── schemas/            # SQL DDL files (source of truth)
│   │   │   ├── 001-events.sql
│   │   │   ├── 002-users.sql
│   │   │   └── 003-materialized-views.sql
│   │   ├── queries/            # Named query functions
│   │   └── migrations/         # Schema migrations (runner.ts + *.sql)
│   ├── ingestion/              # webhook-receiver, kafka-consumer, buffer
│   ├── api/                    # routes.ts, middleware.ts (auth, rate limit)
│   └── jobs/                   # daily-rollup.ts, cleanup.ts (TTL enforcement)
├── tests/                      # unit/ + integration/
├── docker-compose.yml          # Local ClickHouse
├── init-db/                    # Docker init scripts
└── config/                     # development / staging / production .env
```

### Step 2: Data Flow Architecture

Data moves in one direction: sources → a batching ingestion layer → ClickHouse
(raw MergeTree → materialized views → aggregate tables) → an API that reads only
the aggregate tables → dashboards.

```
Data Sources (Webhooks, API, Kafka, S3)
        │
Ingestion Layer (Buffer + batch, 10K+ rows/insert)
        │
ClickHouse Server
   Raw Event Tables (MergeTree, append-only)
        │  auto-aggregate on INSERT
   Materialized Views (hourly, daily, tenant-level)
        │
   Aggregate Tables (AggregatingMergeTree)
        │
API Layer (queries aggregate tables, never raw events)
        │
Dashboards / Client Apps
```

### Step 3: Schema Design (3-Layer Pattern)

Three layers — raw append-only events, hourly aggregation, and a daily rollup for
dashboards — with materialized views auto-populating each aggregate on INSERT.
The essential raw-table skeleton:

```sql
CREATE TABLE analytics.events_raw (
    event_id    UUID DEFAULT generateUUIDv4(),
    tenant_id   UInt32,
    event_type  LowCardinality(String),
    user_id     UInt64,
    properties  String CODEC(ZSTD(3)),
    created_at  DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree()
ORDER BY (tenant_id, event_type, toDate(created_at), user_id)
PARTITION BY toYYYYMM(created_at)
TTL created_at + INTERVAL 90 DAY;
```

Full three-layer DDL, materialized views, and the rationale: see
[references/schema-design.md](references/schema-design.md).

### Step 4: Multi-Tenant Patterns

Choose an isolation strategy. Default to Approach A (shared table, `tenant_id`
first in `ORDER BY`) — it scales to 10K+ tenants:

```sql
ORDER BY (tenant_id, event_type, created_at)
SELECT count() FROM events_raw WHERE tenant_id = 42;  -- scans only tenant 42
```

Database-per-tenant (strict isolation) and row-level security (RBAC) alternatives
with trade-offs: see [references/multi-tenant-patterns.md](references/multi-tenant-patterns.md).

### Step 5: Client Module

Use a singleton `@clickhouse/client` instance and parameterized queries that read
from the aggregate tables. Full client + query-function code:
[references/client-module.md](references/client-module.md).

## Architecture Decision Records

| Decision | Choice | Why |
|----------|--------|-----|
| Engine | MergeTree (raw) + AggregatingMergeTree (rollups) | Best for append + pre-agg |
| Multi-tenant | Shared table + tenant_id in ORDER BY | Scales to 10K+ tenants |
| Ingestion | Buffer + batch INSERT | Avoids "too many parts" |
| Aggregation | Materialized views (not cron) | Real-time, zero-lag |
| Format | JSONEachRow | Client support, debugging |
| Compression | ZSTD(3) for strings, Delta for ints | 10-20x compression |

## Output

Applying this skill produces a concrete architecture plan for a ClickHouse system:

- A **project directory layout** (Step 1) with DDL as the source of truth.
- A **3-layer schema** — raw MergeTree table, hourly and daily
  `AggregatingMergeTree` tables, each fed by a materialized view.
- A chosen **multi-tenant isolation strategy** (shared table / database-per-tenant /
  row policy) with the reasoning recorded.
- A **singleton client module** plus named, parameterized query functions that read
  only from aggregate tables.
- A filled-in **Architecture Decision Record** table capturing engine, tenancy,
  ingestion, aggregation, format, and compression choices.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cross-tenant data leak | Missing WHERE tenant_id | Use row policies or middleware |
| Stale dashboard data | MV not created | Verify MV exists and is attached |
| Schema drift | Manual DDL changes | Use migration runner |
| Slow dashboard queries | Querying raw table | Query aggregate tables instead |

## Examples

**Design a new multi-tenant analytics platform.** Start from the Step 1 layout and
the Step 3 raw-table skeleton, then open [references/schema-design.md](references/schema-design.md)
for the full three-layer DDL and [references/multi-tenant-patterns.md](references/multi-tenant-patterns.md)
to pick an isolation strategy.

**Query a tenant dashboard from Node.js.** Read from the daily rollup, not the raw
table — the pattern the client module in
[references/client-module.md](references/client-module.md) implements:

```sql
SELECT date, sum(total) AS events, uniqMerge(users) AS unique_users
FROM analytics.events_daily
WHERE tenant_id = {tid:UInt32} AND date >= today() - {days:UInt32}
GROUP BY date ORDER BY date;
```

**Review an existing ClickHouse integration.** `Grep` for `createClient(` and any
raw-table `SELECT`s in the API layer; flag queries hitting `events_raw` instead of
an aggregate table against the Error Handling table above.

## Resources

- [ClickHouse Architecture](https://clickhouse.com/docs/development/architecture)
- [SharedMergeTree (Cloud)](https://clickhouse.com/docs/cloud/reference/shared-merge-tree)
- [Materialized Views](https://clickhouse.com/blog/using-materialized-views-in-clickhouse)
- [references/schema-design.md](references/schema-design.md) — full 3-layer DDL
- [references/multi-tenant-patterns.md](references/multi-tenant-patterns.md) — tenancy trade-offs
- [references/client-module.md](references/client-module.md) — client + query code

## Next Steps

For multi-environment configuration, layer on the `clickhouse-multi-env-setup`
skill, which covers per-environment `.env` files, staging/production connection
settings, and migration promotion between environments.
