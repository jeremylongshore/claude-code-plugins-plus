---
name: clickhouse-reference-architecture
description: |
  Production reference architecture for ClickHouse-backed applications —
  project layout, data flow, multi-tenant patterns, and operational topology.
  Use when designing new ClickHouse systems, reviewing architecture,
  or establishing standards for ClickHouse integrations.
  Trigger: "clickhouse architecture", "clickhouse project structure",
  "clickhouse design", "clickhouse multi-tenant", "clickhouse reference".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Reference Architecture

## Overview

Production-grade architecture for ClickHouse analytics platforms covering
project layout, data flow, multi-tenancy, and operational patterns.

## Prerequisites

- Understanding of ClickHouse fundamentals (engines, ORDER BY, partitioning)
- TypeScript/Node.js project

## Instructions

### Step 1: Project Structure

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
│   │   │   ├── events.ts
│   │   │   ├── users.ts
│   │   │   └── dashboards.ts
│   │   └── migrations/         # Schema migrations
│   │       ├── runner.ts
│   │       └── 001-add-country.sql
│   ├── ingestion/
│   │   ├── webhook-receiver.ts # HTTP webhook endpoint
│   │   ├── kafka-consumer.ts   # Kafka consumer (if applicable)
│   │   └── buffer.ts           # Insert batching buffer
│   ├── api/
│   │   ├── routes.ts           # API endpoints
│   │   └── middleware.ts       # Auth, rate limiting
│   └── jobs/
│       ├── daily-rollup.ts     # Scheduled aggregations
│       └── cleanup.ts          # TTL enforcement
├── tests/
│   ├── unit/
│   └── integration/
├── docker-compose.yml          # Local ClickHouse
├── init-db/                    # Docker init scripts
└── config/
    ├── development.env
    ├── staging.env
    └── production.env
```

### Step 2: Data Flow Architecture

```
                    ┌─────────────────┐
                    │   Data Sources   │
                    │  (Webhooks, API, │
                    │   Kafka, S3)     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Ingestion Layer │
                    │  (Buffer + Batch │
                    │   10K+ rows/ins) │
                    └────────┬────────┘
                             │
              ┌──────────────▼──────────────┐
              │       ClickHouse Server      │
              │                              │
              │  ┌────────────────────────┐  │
              │  │   Raw Event Tables     │  │
              │  │   (MergeTree, append)  │  │
              │  └───────────┬────────────┘  │
              │              │               │
              │  ┌───────────▼────────────┐  │
              │  │  Materialized Views    │  │
              │  │  (Auto-aggregate on    │  │
              │  │   INSERT — hourly,     │  │
              │  │   daily, tenant-level) │  │
              │  └───────────┬────────────┘  │
              │              │               │
              │  ┌───────────▼────────────┐  │
              │  │  Aggregate Tables      │  │
              │  │  (AggregatingMergeTree)│  │
              │  └────────────────────────┘  │
              └──────────────┬──────────────┘
                             │
                    ┌────────▼────────┐
                    │    API Layer     │
                    │  (Query aggregate│
                    │   tables, not    │
                    │   raw events)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Dashboards /   │
                    │   Client Apps    │
                    └─────────────────┘
```

### Step 3: Schema Design (3-Layer Pattern)

```sql
-- Layer 1: Raw events (append-only, full fidelity)
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

-- Layer 2: Hourly aggregation (auto-populated via materialized view)
CREATE TABLE analytics.events_hourly (
    hour        DateTime,
    tenant_id   UInt32,
    event_type  LowCardinality(String),
    cnt         UInt64,
    users       AggregateFunction(uniq, UInt64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, event_type, hour);

CREATE MATERIALIZED VIEW analytics.events_hourly_mv TO analytics.events_hourly AS
SELECT toStartOfHour(created_at) AS hour, tenant_id, event_type,
       count() AS cnt, uniqState(user_id) AS users
FROM analytics.events_raw GROUP BY hour, tenant_id, event_type;

-- Layer 3: Daily rollup for dashboards
CREATE TABLE analytics.events_daily (
    date        Date,
    tenant_id   UInt32,
    total       UInt64,
    users       AggregateFunction(uniq, UInt64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, date);

CREATE MATERIALIZED VIEW analytics.events_daily_mv TO analytics.events_daily AS
SELECT toDate(created_at) AS date, tenant_id,
       count() AS total, uniqState(user_id) AS users
FROM analytics.events_raw GROUP BY date, tenant_id;
```

### Step 4: Multi-Tenant Patterns

**Approach A: Shared table with tenant_id in ORDER BY (recommended)**

```sql
-- Tenant_id first in ORDER BY = queries filter on tenant efficiently
ORDER BY (tenant_id, event_type, created_at)

-- Query: only scans data for this tenant
SELECT count() FROM events_raw WHERE tenant_id = 42;
```

**Approach B: Database per tenant (for strict isolation)**

```sql
CREATE DATABASE tenant_42;
CREATE TABLE tenant_42.events (...) ENGINE = MergeTree() ...;

-- Pros: Full isolation, easy to drop tenant
-- Cons: Schema changes need per-tenant DDL, more operational overhead
```

**Approach C: Row-level security (ClickHouse RBAC)**

```sql
CREATE ROW POLICY tenant_isolation ON analytics.events_raw
    FOR SELECT USING tenant_id = getSetting('custom_tenant_id')
    TO app_user;
```

### Step 5: Client Module

```typescript
// src/clickhouse/client.ts
import { createClient, ClickHouseClient } from '@clickhouse/client';

let instance: ClickHouseClient | null = null;

export function getClient(): ClickHouseClient {
  if (!instance) {
    instance = createClient({
      url: process.env.CLICKHOUSE_HOST!,
      username: process.env.CLICKHOUSE_USER!,
      password: process.env.CLICKHOUSE_PASSWORD!,
      database: process.env.CLICKHOUSE_DATABASE ?? 'analytics',
      max_open_connections: Number(process.env.CH_MAX_CONNECTIONS ?? 10),
      request_timeout: 30_000,
      compression: { request: true, response: true },
    });
  }
  return instance;
}

// src/clickhouse/queries/dashboards.ts
export async function getTenantDashboard(tenantId: number, days = 30) {
  const client = getClient();
  const rs = await client.query({
    query: `
      SELECT date, sum(total) AS events, uniqMerge(users) AS unique_users
      FROM analytics.events_daily
      WHERE tenant_id = {tid:UInt32} AND date >= today() - {days:UInt32}
      GROUP BY date ORDER BY date
    `,
    query_params: { tid: tenantId, days },
    format: 'JSONEachRow',
  });
  return rs.json<{ date: string; events: string; unique_users: string }>();
}
```

## Architecture Decision Records

| Decision | Choice | Why |
|----------|--------|-----|
| Engine | MergeTree (raw) + AggregatingMergeTree (rollups) | Best for append + pre-agg |
| Multi-tenant | Shared table + tenant_id in ORDER BY | Scales to 10K+ tenants |
| Ingestion | Buffer + batch INSERT | Avoids "too many parts" |
| Aggregation | Materialized views (not cron) | Real-time, zero-lag |
| Format | JSONEachRow | Client support, debugging |
| Compression | ZSTD(3) for strings, Delta for ints | 10-20x compression |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cross-tenant data leak | Missing WHERE tenant_id | Use row policies or middleware |
| Stale dashboard data | MV not created | Verify MV exists and is attached |
| Schema drift | Manual DDL changes | Use migration runner |
| Slow dashboard queries | Querying raw table | Query aggregate tables instead |

## Resources

- [ClickHouse Architecture](https://clickhouse.com/docs/development/architecture)
- [SharedMergeTree (Cloud)](https://clickhouse.com/docs/cloud/reference/shared-merge-tree)
- [Materialized Views](https://clickhouse.com/blog/using-materialized-views-in-clickhouse)

## Next Steps

For multi-environment configuration, see `clickhouse-multi-env-setup`.
