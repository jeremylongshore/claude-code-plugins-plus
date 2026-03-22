---
name: snowflake-load-scale
description: |
  Implement Snowflake load testing, warehouse scaling, and capacity planning.
  Use when testing query performance at scale, configuring multi-cluster warehouses,
  or planning capacity for production Snowflake workloads.
  Trigger with phrases like "snowflake load test", "snowflake scale",
  "snowflake capacity", "snowflake benchmark", "snowflake multi-cluster".
allowed-tools: Read, Write, Edit, Bash(python3:*), Bash(snowsql:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Load & Scale

## Overview

Load testing, scaling strategies, and capacity planning for Snowflake workloads using warehouse sizing, multi-cluster configuration, and concurrent query simulation.

## Scaling Model

| Dimension | How to Scale | When |
|-----------|-------------|------|
| Single query speed | Scale UP (bigger warehouse) | Complex queries, large scans |
| Concurrent queries | Scale OUT (multi-cluster) | Many users, dashboard refresh |
| Data volume | Scale UP + clustering | Tables > 1TB |
| Mixed workloads | Separate warehouses | ETL + analytics on same data |

## Instructions

### Step 1: Benchmark Current Performance

```sql
-- Baseline metrics for critical queries
-- Run each query 3 times and record results

-- Disable result cache for accurate benchmarking
ALTER SESSION SET USE_CACHED_RESULT = FALSE;

-- Test query 1: Point lookup
SELECT * FROM orders WHERE order_id = 12345;

-- Test query 2: Aggregation
SELECT DATE_TRUNC('month', order_date) AS month,
       COUNT(*) AS orders, SUM(amount) AS revenue
FROM orders
WHERE order_date >= '2025-01-01'
GROUP BY month ORDER BY month;

-- Test query 3: Join + filter
SELECT c.name, SUM(o.amount) AS total_spend
FROM customers c
JOIN orders o ON c.id = o.customer_id
WHERE o.order_date >= DATEADD(days, -90, CURRENT_DATE())
GROUP BY c.name
ORDER BY total_spend DESC
LIMIT 100;

-- Record results
SELECT query_id, query_text, warehouse_name, warehouse_size,
       total_elapsed_time / 1000 AS seconds,
       bytes_scanned / 1e9 AS gb_scanned,
       rows_produced, partitions_scanned, partitions_total,
       bytes_spilled_to_local_storage, bytes_spilled_to_remote_storage
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY_BY_SESSION())
ORDER BY start_time DESC
LIMIT 10;

-- Re-enable cache
ALTER SESSION SET USE_CACHED_RESULT = TRUE;
```

### Step 2: Test Warehouse Size Impact

```sql
-- Run same query on different warehouse sizes to find optimal
-- XS → S → M → L → XL

ALTER WAREHOUSE BENCHMARK_WH SET WAREHOUSE_SIZE = 'XSMALL';
ALTER SESSION SET USE_CACHED_RESULT = FALSE;

-- Run your benchmark query
SELECT /* BENCHMARK_XS */ ...;

ALTER WAREHOUSE BENCHMARK_WH SET WAREHOUSE_SIZE = 'SMALL';
SELECT /* BENCHMARK_S */ ...;

ALTER WAREHOUSE BENCHMARK_WH SET WAREHOUSE_SIZE = 'MEDIUM';
SELECT /* BENCHMARK_M */ ...;

-- Compare results
SELECT warehouse_size, query_id,
       total_elapsed_time / 1000 AS seconds,
       bytes_scanned / 1e9 AS gb_scanned
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY_BY_SESSION())
WHERE query_text LIKE '%BENCHMARK_%'
ORDER BY start_time DESC;

-- Typical scaling: doubling size halves runtime for scan-heavy queries
-- Diminishing returns for small/simple queries
```

### Step 3: Concurrent Load Testing

```python
# load_test.py — simulate concurrent Snowflake queries
import snowflake.connector
import threading
import time
import os
from statistics import mean, median

CONCURRENT_USERS = 20
QUERIES_PER_USER = 10
WAREHOUSE = 'LOAD_TEST_WH'

TEST_QUERIES = [
    "SELECT COUNT(*) FROM orders WHERE order_date = CURRENT_DATE() - 1",
    "SELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id LIMIT 100",
    "SELECT * FROM orders WHERE order_id = %s",
]

results = []
errors = []

def run_user_session(user_id: int):
    conn = snowflake.connector.connect(
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        user=os.environ['SNOWFLAKE_USER'],
        password=os.environ['SNOWFLAKE_PASSWORD'],
        warehouse=WAREHOUSE,
        database='PROD_DW',
        schema='GOLD',
    )
    cursor = conn.cursor()
    for i in range(QUERIES_PER_USER):
        query = TEST_QUERIES[i % len(TEST_QUERIES)]
        start = time.time()
        try:
            if '%s' in query:
                cursor.execute(query, (user_id * 1000 + i,))
            else:
                cursor.execute(query)
            cursor.fetchall()
            elapsed = time.time() - start
            results.append({'user': user_id, 'query': i, 'seconds': elapsed})
        except Exception as e:
            errors.append({'user': user_id, 'query': i, 'error': str(e)})
    conn.close()

# Run concurrent sessions
threads = []
start_time = time.time()
for uid in range(CONCURRENT_USERS):
    t = threading.Thread(target=run_user_session, args=(uid,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()
total_time = time.time() - start_time

# Report
times = [r['seconds'] for r in results]
print(f"=== Load Test Results ===")
print(f"Users: {CONCURRENT_USERS}, Queries/user: {QUERIES_PER_USER}")
print(f"Total queries: {len(results)}, Errors: {len(errors)}")
print(f"Total time: {total_time:.1f}s")
print(f"Avg latency: {mean(times):.3f}s")
print(f"Median: {median(times):.3f}s")
print(f"P95: {sorted(times)[int(len(times)*0.95)]:.3f}s")
print(f"QPS: {len(results)/total_time:.1f}")
```

### Step 4: Multi-Cluster Warehouse Configuration

```sql
-- Standard scaling: Snowflake adds clusters when queries queue
CREATE OR REPLACE WAREHOUSE ANALYTICS_WH
  WAREHOUSE_SIZE = 'MEDIUM'
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 6
  SCALING_POLICY = 'STANDARD'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE;

-- Economy scaling: tolerates queuing, minimizes cost
ALTER WAREHOUSE ANALYTICS_WH SET SCALING_POLICY = 'ECONOMY';

-- Maximized mode: all clusters always running (predictable latency)
CREATE WAREHOUSE DASHBOARD_WH
  WAREHOUSE_SIZE = 'SMALL'
  MIN_CLUSTER_COUNT = 3
  MAX_CLUSTER_COUNT = 3    -- Same = maximized mode
  AUTO_SUSPEND = 120
  AUTO_RESUME = TRUE;

-- Monitor multi-cluster behavior
SELECT start_time, warehouse_name,
       avg_running, avg_queued_load, avg_queued_provisioning
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_LOAD_HISTORY(
  DATE_RANGE_START => DATEADD(hours, -4, CURRENT_TIMESTAMP()),
  WAREHOUSE_NAME => 'ANALYTICS_WH'
))
WHERE avg_queued_load > 0
ORDER BY start_time DESC;
```

### Step 5: Capacity Planning

```sql
-- Weekly growth analysis
SELECT DATE_TRUNC('week', start_time) AS week,
       SUM(credits_used) AS weekly_credits,
       COUNT(DISTINCT query_id) AS weekly_queries,
       ROUND(SUM(credits_used) / NULLIF(COUNT(DISTINCT query_id), 0), 4) AS credits_per_query
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY w
JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q
  ON w.warehouse_name = q.warehouse_name
WHERE w.start_time >= DATEADD(months, -3, CURRENT_TIMESTAMP())
GROUP BY week
ORDER BY week;

-- Storage growth trend
SELECT usage_date,
       ROUND(storage_bytes / 1e12, 3) AS data_tb,
       LAG(ROUND(storage_bytes / 1e12, 3)) OVER (ORDER BY usage_date) AS prev_tb,
       ROUND((storage_bytes - LAG(storage_bytes) OVER (ORDER BY usage_date)) / 1e9, 1) AS daily_growth_gb
FROM SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE
WHERE usage_date >= DATEADD(days, -30, CURRENT_DATE())
ORDER BY usage_date;
```

## Benchmark Results Template

```
## Snowflake Performance Benchmark
Date: YYYY-MM-DD
Environment: [staging/production]
Table size: [X rows, Y GB]

| Warehouse | Query Type | Avg (s) | P95 (s) | GB Scanned | Spill |
|-----------|-----------|---------|---------|-----------|-------|
| XS        | Agg       |         |         |           |       |
| S         | Agg       |         |         |           |       |
| M         | Agg       |         |         |           |       |

Concurrent: [N users, M queries, QPS achieved]
Recommendation: [sizing/clustering/multi-cluster advice]
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Queries queuing | Concurrency > capacity | Add multi-cluster or separate warehouse |
| Linear scaling fails | Query not parallelizable | Optimize SQL (reduce shuffle) |
| Spilling on larger warehouse | Data skew | Check for hot partition/join skew |
| Load test throttled | Login rate limit | Use connection pooling |

## Resources

- [Warehouse Considerations](https://docs.snowflake.com/en/user-guide/warehouses-considerations)
- [Multi-Cluster Warehouses](https://docs.snowflake.com/en/user-guide/warehouses-multicluster)
- [Warehouse Load Monitoring](https://docs.snowflake.com/en/user-guide/warehouses-load-monitoring)

## Next Steps

For reliability patterns, see `snowflake-reliability-patterns`.
