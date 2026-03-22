---
name: clickhouse-core-workflow-b
description: |
  Insert, query, and aggregate data in ClickHouse with real SQL patterns.
  Use when writing analytical queries, inserting data at scale,
  building dashboards, or implementing materialized views.
  Trigger: "clickhouse query", "clickhouse insert", "clickhouse aggregate",
  "clickhouse materialized view", "clickhouse SQL".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Insert & Query (Core Workflow B)

## Overview

Insert data efficiently and write analytical queries with aggregations,
window functions, and materialized views.

## Prerequisites

- Tables created (see `clickhouse-core-workflow-a`)
- `@clickhouse/client` connected

## Instructions

### Step 1: Bulk Insert Patterns

```typescript
import { createClient } from '@clickhouse/client';

const client = createClient({
  url: process.env.CLICKHOUSE_HOST!,
  username: process.env.CLICKHOUSE_USER ?? 'default',
  password: process.env.CLICKHOUSE_PASSWORD ?? '',
});

// Insert many rows efficiently — @clickhouse/client buffers internally
await client.insert({
  table: 'analytics.events',
  values: events,   // Array of objects matching table columns
  format: 'JSONEachRow',
});

// Insert from file (CSV, Parquet, etc.)
import { createReadStream } from 'fs';

await client.insert({
  table: 'analytics.events',
  values: createReadStream('./data/events.csv'),
  format: 'CSVWithNames',
});
```

**Insert best practices:**
- Batch rows: aim for 10K-100K rows per INSERT (not one at a time)
- ClickHouse creates a new "part" per INSERT — too many small inserts cause "too many parts"
- For real-time streams, buffer 1-5 seconds then flush

### Step 2: Analytical Queries

```sql
-- Top events by tenant in the last 7 days
SELECT
    tenant_id,
    event_type,
    count()                  AS event_count,
    uniqExact(user_id)       AS unique_users,
    min(created_at)          AS first_seen,
    max(created_at)          AS last_seen
FROM analytics.events
WHERE created_at >= now() - INTERVAL 7 DAY
GROUP BY tenant_id, event_type
ORDER BY event_count DESC
LIMIT 100;
```

```sql
-- Funnel analysis: signup → activation → purchase
SELECT
    level,
    count() AS users
FROM (
    SELECT
        user_id,
        groupArray(event_type) AS journey
    FROM analytics.events
    WHERE event_type IN ('signup', 'activation', 'purchase')
      AND created_at >= today() - 30
    GROUP BY user_id
)
ARRAY JOIN arrayEnumerate(journey) AS level
GROUP BY level
ORDER BY level;
```

```sql
-- Retention: users active this week who were also active last week
SELECT
    count(DISTINCT curr.user_id) AS retained_users
FROM analytics.events AS curr
INNER JOIN analytics.events AS prev
    ON curr.user_id = prev.user_id
WHERE curr.created_at >= toMonday(today())
  AND prev.created_at >= toMonday(today()) - 7
  AND prev.created_at < toMonday(today());
```

### Step 3: Parameterized Queries in Node.js

```typescript
// Use {param:Type} syntax for safe parameterized queries
const rs = await client.query({
  query: `
    SELECT event_type, count() AS cnt
    FROM analytics.events
    WHERE tenant_id = {tenant_id:UInt32}
      AND created_at >= {from_date:DateTime}
    GROUP BY event_type
    ORDER BY cnt DESC
  `,
  query_params: {
    tenant_id: 1,
    from_date: '2025-01-01 00:00:00',
  },
  format: 'JSONEachRow',
});
const rows = await rs.json();
```

### Step 4: Materialized Views (Pre-Aggregation)

```sql
-- Source table receives raw events
-- Materialized view aggregates automatically on INSERT

CREATE MATERIALIZED VIEW analytics.hourly_stats_mv
TO analytics.hourly_stats  -- target table
AS
SELECT
    toStartOfHour(created_at) AS hour,
    tenant_id,
    event_type,
    count()                   AS event_count,
    uniqState(user_id)        AS unique_users_state
FROM analytics.events
GROUP BY hour, tenant_id, event_type;

-- Target table uses AggregatingMergeTree
CREATE TABLE analytics.hourly_stats (
    hour              DateTime,
    tenant_id         UInt32,
    event_type        LowCardinality(String),
    event_count       UInt64,
    unique_users_state AggregateFunction(uniq, UInt64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, event_type, hour);

-- Query the materialized view (merge aggregation states)
SELECT
    hour,
    sum(event_count)           AS events,
    uniqMerge(unique_users_state) AS unique_users
FROM analytics.hourly_stats
WHERE tenant_id = 1
GROUP BY hour
ORDER BY hour;
```

### Step 5: Window Functions

```sql
-- Running total and rank within each tenant
SELECT
    tenant_id,
    event_type,
    count()   AS cnt,
    sum(count()) OVER (PARTITION BY tenant_id ORDER BY count() DESC) AS running_total,
    row_number() OVER (PARTITION BY tenant_id ORDER BY count() DESC) AS rank
FROM analytics.events
WHERE created_at >= today() - 7
GROUP BY tenant_id, event_type
ORDER BY tenant_id, rank;
```

### Step 6: Common ClickHouse Functions

| Function | Description | Example |
|----------|-------------|---------|
| `count()` | Row count | `count()` |
| `uniq(col)` | Approximate distinct count (HyperLogLog) | `uniq(user_id)` |
| `uniqExact(col)` | Exact distinct count | `uniqExact(user_id)` |
| `quantile(0.95)(col)` | Percentile | `quantile(0.95)(latency_ms)` |
| `arrayJoin(arr)` | Unnest array to rows | `arrayJoin(tags)` |
| `JSONExtractString(col, key)` | Extract from JSON string | `JSONExtractString(properties, 'plan')` |
| `toStartOfHour(dt)` | Truncate to hour | `toStartOfHour(created_at)` |
| `formatReadableSize(n)` | Human-readable bytes | `formatReadableSize(bytes)` |
| `if(cond, then, else)` | Conditional | `if(cnt > 0, cnt, NULL)` |
| `multiIf(...)` | Multi-branch conditional | `multiIf(x>10, 'high', x>5, 'med', 'low')` |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Too many parts (300)` | Frequent small inserts | Batch inserts, increase `parts_to_throw_insert` |
| `Memory limit exceeded` | Large GROUP BY / JOIN | Add WHERE filters, increase `max_memory_usage` |
| `UNKNOWN_FUNCTION` | Wrong ClickHouse version | Check `SELECT version()` |
| `Cannot parse datetime` | Wrong format | Use `YYYY-MM-DD HH:MM:SS` format |

## Resources

- [SQL Reference](https://clickhouse.com/docs/sql-reference)
- [Aggregate Functions](https://clickhouse.com/docs/sql-reference/aggregate-functions)
- [Materialized Views Guide](https://clickhouse.com/blog/using-materialized-views-in-clickhouse)

## Next Steps

For error troubleshooting, see `clickhouse-common-errors`.
