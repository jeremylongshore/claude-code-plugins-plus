---
name: snowflake-advanced-troubleshooting
description: |
  Apply advanced Snowflake debugging with query profiling, spill analysis,
  lock contention, and performance deep-dives using ACCOUNT_USAGE views.
  Use when standard troubleshooting fails, investigating slow queries,
  or diagnosing warehouse performance issues.
  Trigger with phrases like "snowflake hard bug", "snowflake slow query debug",
  "snowflake query profile", "snowflake spilling", "snowflake deep debug".
allowed-tools: Read, Grep, Bash(snowsql:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Advanced Troubleshooting

## Overview

Deep debugging techniques for complex Snowflake issues: query profile analysis, spill detection, lock contention, transaction conflicts, and metadata operation bottlenecks.

## Instructions

### Step 1: Query Profile Deep Dive

```sql
-- Get detailed execution stats for a specific query
SELECT *
FROM TABLE(GET_QUERY_OPERATOR_STATS('<query_id>'));

-- Key operators to look for:
-- TableScan: Check partitions_scanned vs partitions_total
-- Sort: Check spilling_to_local_storage, spilling_to_remote_storage
-- Join: Check type (broadcast vs hash), probe/build side sizes
-- Aggregate: Check if grouping cardinality causes spill

-- Identify queries with excessive spilling
SELECT query_id, query_text,
       bytes_spilled_to_local_storage / 1e9 AS local_spill_gb,
       bytes_spilled_to_remote_storage / 1e9 AS remote_spill_gb,
       total_elapsed_time / 1000 AS seconds,
       warehouse_size
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE (bytes_spilled_to_local_storage > 0 OR bytes_spilled_to_remote_storage > 0)
  AND start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
ORDER BY bytes_spilled_to_remote_storage DESC
LIMIT 20;

-- Remote spill = warehouse too small for the query
-- Fix: Scale up warehouse or optimize query to reduce intermediate data
```

### Step 2: Lock and Transaction Contention

```sql
-- Find blocked/waiting queries
SELECT query_id, query_text, blocked_query_id,
       DATEDIFF('second', start_time, CURRENT_TIMESTAMP()) AS wait_seconds,
       user_name, warehouse_name
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE execution_status = 'BLOCKED'
  AND start_time >= DATEADD(minutes, -30, CURRENT_TIMESTAMP());

-- Find long-running transactions (holding locks)
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE execution_status = 'RUNNING'
  AND DATEDIFF('minute', start_time, CURRENT_TIMESTAMP()) > 30
ORDER BY start_time;

-- Kill a blocking query
SELECT SYSTEM$CANCEL_QUERY('<blocking_query_id>');

-- Common lock scenarios:
-- DDL on table blocks DML (ALTER TABLE blocks INSERT)
-- Concurrent MERGE on same table → serialization
-- Long COPY INTO blocks other COPY INTO on same table
```

### Step 3: Metadata Operation Analysis

```sql
-- Cloud services credit spike (metadata-heavy operations)
SELECT DATE_TRUNC('hour', start_time) AS hour,
       SUM(credits_used_cloud_services) AS cloud_credits,
       COUNT(*) AS query_count,
       SUM(credits_used_cloud_services) / NULLIF(COUNT(*), 0) AS credits_per_query
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
  AND credits_used_cloud_services > 0
GROUP BY hour
ORDER BY cloud_credits DESC;

-- Excessive metadata queries (SHOW, DESCRIBE, INFORMATION_SCHEMA)
SELECT query_type, COUNT(*) AS count,
       AVG(total_elapsed_time) AS avg_ms
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
  AND query_type IN ('SHOW', 'DESCRIBE', 'GET_DDL')
GROUP BY query_type
ORDER BY count DESC;
-- If very high, consider caching INFORMATION_SCHEMA results in your app
```

### Step 4: Partition Pruning Analysis

```sql
-- Queries scanning too many partitions (candidate for clustering)
SELECT query_id,
       SUBSTR(query_text, 1, 200) AS query_preview,
       partitions_scanned,
       partitions_total,
       ROUND(partitions_scanned * 100.0 / NULLIF(partitions_total, 0), 1) AS scan_pct,
       bytes_scanned / 1e9 AS gb_scanned,
       total_elapsed_time / 1000 AS seconds
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE partitions_total > 100
  AND partitions_scanned > partitions_total * 0.5
  AND start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
  AND query_type = 'SELECT'
ORDER BY partitions_scanned DESC
LIMIT 10;

-- Check if table would benefit from clustering
SELECT SYSTEM$CLUSTERING_INFORMATION('my_db.my_schema.orders', '(order_date)');
-- Look at average_depth: > 5 means clustering would help
-- Look at partition_depth_histogram: should be concentrated at depth 1-2
```

### Step 5: Network and Connectivity Debugging

```bash
# DNS resolution test
dig +short $(echo $SNOWFLAKE_ACCOUNT).snowflakecomputing.com

# TLS handshake test
openssl s_client -connect ${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com:443 \
  -servername ${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com < /dev/null 2>/dev/null \
  | openssl x509 -noout -subject -dates

# Latency test
curl -o /dev/null -s -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTLS: %{time_appconnect}s\nTotal: %{time_total}s\n" \
  "https://${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/"

# Check if OCSP responder is reachable (Snowflake uses OCSP for cert validation)
curl -s -o /dev/null -w "%{http_code}" "http://ocsp.snowflakecomputing.com/ocsp"
```

### Step 6: Driver-Level Debugging

```typescript
// Enable debug logging in Node.js driver
import snowflake from 'snowflake-sdk';

snowflake.configure({
  logLevel: 'TRACE',  // DEBUG, INFO, WARN, ERROR, TRACE
});

// Log all SQL statements with timing
const originalExecute = connection.execute.bind(connection);
connection.execute = function(opts: any) {
  const start = Date.now();
  const sql = opts.sqlText;
  console.log(`[SF] Executing: ${sql.substring(0, 200)}`);

  const originalComplete = opts.complete;
  opts.complete = (err: any, stmt: any, rows: any) => {
    const duration = Date.now() - start;
    if (err) {
      console.error(`[SF] FAILED (${duration}ms): ${err.code} ${err.message}`);
    } else {
      console.log(`[SF] OK (${duration}ms): ${rows?.length || 0} rows`);
    }
    originalComplete(err, stmt, rows);
  };

  return originalExecute(opts);
};
```

```python
# Enable debug logging in Python connector
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('snowflake.connector')
logger.setLevel(logging.DEBUG)

# Connection with debug parameters
conn = snowflake.connector.connect(
    # ...
    login_timeout=30,
    network_timeout=60,
    socket_timeout=60,
)
```

### Step 7: Systematic Isolation Checklist

```
1. Can you connect at all? → SELECT 1;
2. Can you reach the right context? → SELECT CURRENT_DATABASE(), CURRENT_ROLE();
3. Does the object exist? → SHOW TABLES LIKE 'xxx';
4. Do you have permissions? → SHOW GRANTS TO ROLE xxx;
5. Is the warehouse available? → SHOW WAREHOUSES LIKE 'xxx';
6. Does a simple query work? → SELECT COUNT(*) FROM table;
7. Does the specific query work on smaller data? → Add LIMIT 100
8. Is there spilling? → Check bytes_spilled_to_remote_storage
9. Is there partition skew? → Check partition scan ratio
10. Is there contention? → Check blocked queries
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Remote spilling | Warehouse too small | Scale up, or optimize query |
| Blocked queries | Lock contention | Cancel blocking query, serialize DDL |
| High cloud services credits | Too many metadata ops | Cache metadata, batch DDL |
| Partition full scan | No clustering or wrong filter | Add clustering key on filter columns |
| Intermittent timeout | Network/proxy issue | Check OCSP, proxy config |

## Resources

- [Query Profile](https://docs.snowflake.com/en/user-guide/ui-query-profile)
- [Monitoring Warehouse Load](https://docs.snowflake.com/en/user-guide/warehouses-load-monitoring)
- [GET_QUERY_OPERATOR_STATS](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats)

## Next Steps

For load testing, see `snowflake-load-scale`.
