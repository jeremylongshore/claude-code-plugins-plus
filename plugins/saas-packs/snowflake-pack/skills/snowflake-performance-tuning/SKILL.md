---
name: snowflake-performance-tuning
description: |
  Optimize Snowflake query performance with clustering, materialized views, caching, and query profiling.
  Use when queries are slow, analyzing QUERY_HISTORY for bottlenecks,
  or optimizing warehouse utilization and data scanning.
  Trigger with phrases like "snowflake performance", "optimize snowflake",
  "snowflake slow query", "snowflake clustering", "snowflake query profile".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Performance Tuning

## Overview

Optimize Snowflake query performance using clustering keys, materialized views, result caching, query profiling, and warehouse tuning.

## Prerequisites

- Access to `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY`
- Understanding of micro-partitions and pruning
- Role with `MONITOR` privilege on warehouses

## Instructions

### Step 1: Identify Slow Queries

```sql
-- Top 20 slowest queries in last 24 hours
SELECT query_id, query_text, total_elapsed_time / 1000 AS seconds,
       bytes_scanned / 1e9 AS gb_scanned,
       partitions_scanned, partitions_total,
       ROUND(partitions_scanned / NULLIF(partitions_total, 0) * 100, 1) AS pct_scanned,
       warehouse_name, warehouse_size
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE execution_status = 'SUCCESS'
  AND start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
  AND query_type = 'SELECT'
ORDER BY total_elapsed_time DESC
LIMIT 20;

-- Queries scanning too many partitions (poor pruning)
SELECT query_id, query_text,
       partitions_scanned, partitions_total,
       bytes_scanned / 1e9 AS gb_scanned
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE partitions_scanned > partitions_total * 0.5
  AND partitions_total > 100
  AND start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
ORDER BY partitions_scanned DESC
LIMIT 10;
```

### Step 2: Add Clustering Keys

```sql
-- Clustering improves pruning for large tables (> 1TB)
-- Choose columns used in WHERE and JOIN clauses

-- Cluster by date (most common filter)
ALTER TABLE orders CLUSTER BY (order_date);

-- Multi-column clustering
ALTER TABLE events CLUSTER BY (event_date, event_type);

-- Check clustering depth (lower = better)
SELECT SYSTEM$CLUSTERING_INFORMATION('orders', '(order_date)');

-- Monitor automatic reclustering
SELECT table_name, num_rows, bytes,
       SYSTEM$CLUSTERING_DEPTH('orders') AS clustering_depth
FROM INFORMATION_SCHEMA.TABLES
WHERE table_name = 'ORDERS';
```

### Step 3: Use Materialized Views

```sql
-- Pre-compute expensive aggregations
CREATE OR REPLACE MATERIALIZED VIEW daily_revenue_mv
  CLUSTER BY (metric_date)
AS
  SELECT
    DATE_TRUNC('day', order_date) AS metric_date,
    COUNT(*) AS order_count,
    SUM(amount) AS total_revenue,
    AVG(amount) AS avg_order_value
  FROM orders
  GROUP BY DATE_TRUNC('day', order_date);

-- Query the MV instead of base table — automatic rewrite may also apply
SELECT * FROM daily_revenue_mv
WHERE metric_date >= DATEADD(days, -30, CURRENT_DATE());

-- Check MV freshness
SELECT name, is_secure, text, refresh_on
FROM INFORMATION_SCHEMA.MATERIALIZED_VIEWS
WHERE name = 'DAILY_REVENUE_MV';
```

### Step 4: Leverage Result Caching

```sql
-- Result cache is ON by default — same query returns instantly
-- Cache is valid for 24 hours if underlying data hasn't changed

-- Check if a query used cache
SELECT query_id, query_text,
       CASE WHEN bytes_scanned = 0 AND rows_produced > 0
            THEN 'CACHE HIT' ELSE 'CACHE MISS' END AS cache_status,
       total_elapsed_time
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD(hours, -1, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;

-- Disable cache for benchmarking
ALTER SESSION SET USE_CACHED_RESULT = FALSE;
-- Re-enable
ALTER SESSION SET USE_CACHED_RESULT = TRUE;
```

### Step 5: Optimize Common Query Patterns

```sql
-- ANTI-PATTERN: SELECT * on wide tables
-- SELECT * FROM events;  -- Scans all columns

-- BETTER: Select only needed columns
SELECT event_id, event_type, event_date FROM events WHERE event_date = CURRENT_DATE();

-- ANTI-PATTERN: Cartesian joins
-- SELECT * FROM a, b WHERE a.id = b.id;

-- BETTER: Explicit JOIN with filter pushdown
SELECT a.id, a.name, b.amount
FROM customers a
INNER JOIN orders b ON a.id = b.customer_id
WHERE b.order_date >= '2026-01-01';

-- ANTI-PATTERN: LIKE with leading wildcard
-- WHERE name LIKE '%smith%'  -- Full scan

-- BETTER: Use search optimization service for LIKE queries
ALTER TABLE customers ADD SEARCH OPTIMIZATION ON EQUALITY(name), SUBSTRING(name);

-- ANTI-PATTERN: Many small queries in a loop
-- for row in rows: execute(f"INSERT INTO t VALUES ({row})")

-- BETTER: Batch inserts
INSERT INTO target_table
SELECT * FROM source_table WHERE condition;
```

### Step 6: Query Profile Analysis

```sql
-- Use EXPLAIN to see execution plan
EXPLAIN SELECT * FROM orders WHERE order_date = CURRENT_DATE();

-- Get query profile data programmatically
SELECT *
FROM TABLE(GET_QUERY_OPERATOR_STATS('<query_id>'));

-- Key metrics to watch:
-- TableScan: partitions_scanned vs partitions_total
-- Filter: if filter is AFTER scan, consider clustering
-- Sort: high spilling_to_remote_storage = needs bigger warehouse
-- Join: broadcast vs hash, skew detection
```

### Step 7: Warehouse Tuning

```sql
-- Match warehouse size to workload
-- Small: simple queries, < 100GB scans
-- Medium: moderate joins, 100GB-1TB
-- Large: complex analytics, > 1TB scans

-- Scale up for single-query performance
ALTER WAREHOUSE ANALYTICS_WH SET WAREHOUSE_SIZE = 'LARGE';

-- Scale out for concurrent queries (multi-cluster)
ALTER WAREHOUSE ANALYTICS_WH SET
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 4
  SCALING_POLICY = 'STANDARD';

-- Monitor warehouse efficiency
SELECT warehouse_name,
       SUM(credits_used) AS total_credits,
       COUNT(DISTINCT query_id) AS total_queries,
       SUM(credits_used) / NULLIF(COUNT(DISTINCT query_id), 0) AS credits_per_query
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q
JOIN SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY w
  ON q.warehouse_name = w.warehouse_name
  AND DATE_TRUNC('hour', q.start_time) = w.start_time
WHERE q.start_time >= DATEADD(days, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY total_credits DESC;
```

## Performance Benchmarks

| Optimization | Typical Improvement |
|-------------|-------------------|
| Clustering key on filter column | 10-100x fewer partitions scanned |
| Materialized view | 10-1000x for aggregation queries |
| Result cache hit | Instant (0ms scan) |
| Column pruning (SELECT specific cols) | 2-10x less data scanned |
| Search optimization service | 10-100x for point lookups |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Spilling to disk | Warehouse too small for query | Scale up warehouse size |
| High partition scan ratio | No clustering on filter column | Add clustering key |
| MV stale | Background refresh delayed | Check MV refresh status |
| Cache miss on same query | Data changed or session setting | Verify `USE_CACHED_RESULT = TRUE` |

## Resources

- [Query Performance](https://docs.snowflake.com/en/user-guide/performance-query-exploring)
- [Clustering Keys](https://docs.snowflake.com/en/user-guide/tables-clustering-keys)
- [Materialized Views](https://docs.snowflake.com/en/user-guide/views-materialized)
- [Search Optimization](https://docs.snowflake.com/en/user-guide/search-optimization-service)

## Next Steps

For cost optimization, see `snowflake-cost-tuning`.
