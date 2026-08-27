# ClickHouse Performance Tuning — Full Implementation

The full 7-step tuning workflow. Each step is independent — apply the ones that
match your bottleneck (diagnose first with Step 1, then reach for the fix).

## Step 1: Diagnose Slow Queries

```sql
-- Find the slowest queries in the last 24 hours
SELECT
    event_time,
    query_duration_ms,
    read_rows,
    read_bytes,
    result_rows,
    memory_usage,
    substring(query, 1, 300) AS query_preview
FROM system.query_log
WHERE type = 'QueryFinish'
  AND event_time >= now() - INTERVAL 24 HOUR
  AND query_duration_ms > 1000   -- > 1 second
ORDER BY query_duration_ms DESC
LIMIT 20;

-- Analyze a specific query with EXPLAIN
EXPLAIN PLAN
SELECT event_type, count() FROM events WHERE created_at >= today() - 7 GROUP BY event_type;

-- Full pipeline analysis
EXPLAIN PIPELINE
SELECT event_type, count() FROM events WHERE created_at >= today() - 7 GROUP BY event_type;
```

## Step 2: ORDER BY Key Optimization

The ORDER BY key is ClickHouse's primary performance lever. Queries that filter
on the ORDER BY prefix skip entire granules (8192-row chunks — the default
`index_granularity`, so each skipped granule avoids reading 8192 rows).

```sql
-- Check what your current ORDER BY key is
SELECT
    database, table, sorting_key, primary_key,
    formatReadableSize(sum(bytes_on_disk)) AS size
FROM system.tables
JOIN system.parts ON tables.name = parts.table AND tables.database = parts.database
WHERE tables.database = 'analytics' AND tables.name = 'events' AND parts.active
GROUP BY database, table, sorting_key, primary_key;

-- If your queries filter on (tenant_id, event_type, created_at)
-- but ORDER BY is (created_at), you're scanning too much data.
-- Fix: recreate table with correct ORDER BY
CREATE TABLE analytics.events_v2 AS analytics.events
ENGINE = MergeTree()
ORDER BY (tenant_id, event_type, toDate(created_at));

INSERT INTO analytics.events_v2 SELECT * FROM analytics.events;
RENAME TABLE analytics.events TO analytics.events_old,
             analytics.events_v2 TO analytics.events;
```

## Step 3: Data Skipping Indexes

```sql
-- Add a bloom filter index for high-cardinality lookups
ALTER TABLE analytics.events
    ADD INDEX idx_session_id session_id TYPE bloom_filter(0.01) GRANULARITY 4;

-- Add a set index for low-cardinality columns
ALTER TABLE analytics.events
    ADD INDEX idx_country country TYPE set(100) GRANULARITY 4;

-- Add a minmax index for range queries on non-ORDER-BY columns
ALTER TABLE analytics.events
    ADD INDEX idx_amount amount TYPE minmax GRANULARITY 4;

-- Materialize indexes for existing data
ALTER TABLE analytics.events MATERIALIZE INDEX idx_session_id;

-- Verify index usage
EXPLAIN indexes = 1
SELECT * FROM analytics.events WHERE session_id = 'abc-123';
```

## Step 4: Projections (Automatic Pre-Aggregation)

```sql
-- Add a projection for a common aggregation pattern
ALTER TABLE analytics.events
    ADD PROJECTION events_by_hour (
        SELECT
            toStartOfHour(created_at) AS hour,
            tenant_id,
            event_type,
            count() AS cnt,
            uniq(user_id) AS unique_users
        GROUP BY hour, tenant_id, event_type
    );

-- Materialize for existing data
ALTER TABLE analytics.events MATERIALIZE PROJECTION events_by_hour;

-- ClickHouse automatically uses the projection when the query matches
SELECT toStartOfHour(created_at) AS hour, count()
FROM analytics.events
WHERE tenant_id = 1
GROUP BY hour;
-- ^ This query reads from the projection (much smaller) instead of full table
```

## Step 5: Key Server Settings

```sql
-- Per-query performance settings
SET max_threads = 8;                       -- Threads per query (default: CPU cores)
SET max_memory_usage = 10000000000;        -- 10GB per query
SET max_bytes_before_external_sort = 10000000000;  -- Spill sorts to disk
SET max_bytes_before_external_group_by = 10000000000;  -- Spill GROUP BY to disk
SET optimize_read_in_order = 1;            -- Skip sorting if ORDER BY matches
SET compile_expressions = 1;               -- JIT compile expressions
SET max_execution_time = 60;               -- 60s timeout

-- Insert performance settings
SET async_insert = 1;                      -- Server-side batching for small inserts
SET async_insert_max_data_size = 10000000; -- 10MB flush threshold
SET async_insert_busy_timeout_ms = 5000;   -- 5s flush interval
SET min_insert_block_size_rows = 100000;   -- Min rows per insert block
```

## Step 6: Materialized Views for Dashboards

```sql
-- Pre-aggregate for dashboard queries (runs on INSERT, not on query)
CREATE TABLE analytics.dashboard_daily (
    date          Date,
    tenant_id     UInt32,
    total_events  UInt64,
    unique_users  AggregateFunction(uniq, UInt64),
    p95_latency   AggregateFunction(quantile(0.95), Float64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, date);

CREATE MATERIALIZED VIEW analytics.dashboard_daily_mv
TO analytics.dashboard_daily
AS SELECT
    toDate(created_at) AS date,
    tenant_id,
    count() AS total_events,
    uniqState(user_id) AS unique_users,
    quantileState(0.95)(latency_ms) AS p95_latency
FROM analytics.events
GROUP BY date, tenant_id;

-- Query pre-aggregated data (milliseconds instead of seconds)
SELECT
    date,
    sum(total_events)                       AS events,
    uniqMerge(unique_users)                 AS users,
    quantileMerge(0.95)(p95_latency)        AS p95
FROM analytics.dashboard_daily
WHERE tenant_id = 1 AND date >= today() - 30
GROUP BY date ORDER BY date;
```

## Step 7: Query Optimization Patterns

```sql
-- Use PREWHERE for large tables (reads less data than WHERE)
SELECT * FROM analytics.events
PREWHERE event_type = 'purchase'   -- Evaluated first, skips non-matching granules
WHERE user_id > 1000;              -- Evaluated second, only on matching granules

-- Use LIMIT BY for top-N per group (more efficient than window functions)
SELECT tenant_id, event_type, count() AS cnt
FROM analytics.events
GROUP BY tenant_id, event_type
ORDER BY cnt DESC
LIMIT 5 BY tenant_id;   -- Top 5 event types per tenant

-- Use FINAL sparingly with ReplacingMergeTree
-- Instead of: SELECT * FROM users FINAL  (slow, full scan)
-- Prefer: SELECT argMax(email, updated_at) AS email FROM users GROUP BY user_id
```
