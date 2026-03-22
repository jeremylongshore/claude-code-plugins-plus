---
name: snowflake-rate-limits
description: |
  Handle Snowflake concurrency limits, warehouse queuing, and query throttling.
  Use when queries are queuing, hitting concurrency limits,
  or needing to optimize warehouse sizing for throughput.
  Trigger with phrases like "snowflake rate limit", "snowflake throttling",
  "snowflake queuing", "snowflake concurrency", "snowflake warehouse sizing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Rate Limits & Concurrency

## Overview

Snowflake doesn't use traditional API rate limits. Instead, concurrency is governed by warehouse size, multi-cluster configuration, and per-session/account limits.

## Key Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Concurrent queries per warehouse | 8 (XS) to 64+ (4XL) | Depends on warehouse size |
| Queued queries per warehouse | Unlimited (queued, not rejected) | But users experience latency |
| SQL API requests | 10 concurrent per user | Via REST `/api/v2/statements` |
| Snowpipe file notifications | 10,000/sec per pipe | Per-pipe limit |
| Login rate | Throttled per account | Avoid rapid connect/disconnect |
| COPY INTO files per command | 1,000 files recommended | Performance degrades beyond |

## Instructions

### Step 1: Detect Queuing Issues

```sql
-- Check warehouse load — avg_queued_load > 0 means queries are waiting
SELECT warehouse_name, start_time,
       avg_running, avg_queued_load, avg_blocked
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_LOAD_HISTORY(
  DATE_RANGE_START => DATEADD(hours, -4, CURRENT_TIMESTAMP())
))
WHERE avg_queued_load > 0
ORDER BY start_time DESC;

-- Find queries that waited in queue
SELECT query_id, query_text, queued_overload_time / 1000 AS queue_seconds,
       total_elapsed_time / 1000 AS total_seconds, warehouse_name
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE queued_overload_time > 0
  AND start_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP())
ORDER BY queued_overload_time DESC
LIMIT 20;
```

### Step 2: Right-Size Your Warehouse

```sql
-- Size recommendations based on workload type
-- XSMALL: Simple queries, dev/test, low concurrency
-- SMALL/MEDIUM: Standard analytics, dashboards
-- LARGE/XLARGE: Complex joins, large scans
-- 2XL+: Heavy ELT, ML training

-- Create right-sized warehouses per workload
CREATE WAREHOUSE IF NOT EXISTS ETL_WH
  WAREHOUSE_SIZE = 'LARGE'
  AUTO_SUSPEND = 120
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

CREATE WAREHOUSE IF NOT EXISTS ANALYTICS_WH
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

CREATE WAREHOUSE IF NOT EXISTS DASHBOARD_WH
  WAREHOUSE_SIZE = 'SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;
```

### Step 3: Multi-Cluster Warehouse for High Concurrency

```sql
-- Auto-scale from 1 to 5 clusters based on demand
CREATE OR REPLACE WAREHOUSE HIGH_CONCURRENCY_WH
  WAREHOUSE_SIZE = 'MEDIUM'
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 5
  SCALING_POLICY = 'STANDARD'     -- Start new cluster when queries queue
  AUTO_SUSPEND = 120
  AUTO_RESUME = TRUE;

-- Economy scaling: minimize clusters, tolerate some queuing
ALTER WAREHOUSE HIGH_CONCURRENCY_WH SET
  SCALING_POLICY = 'ECONOMY';    -- Only scale when 6+ min queue
```

### Step 4: Application-Level Concurrency Control

```typescript
import PQueue from 'p-queue';

// Limit concurrent Snowflake queries from your application
const snowflakeQueue = new PQueue({
  concurrency: 5,           // Max 5 concurrent queries
  intervalCap: 20,           // Max 20 queries per interval
  interval: 60000,           // Per minute
  timeout: 300000,           // 5-minute timeout per query
});

async function rateLimitedQuery<T>(
  conn: snowflake.Connection,
  sqlText: string,
  binds?: any[]
): Promise<T[]> {
  return snowflakeQueue.add(async () => {
    const result = await query<T>(conn, sqlText, binds);
    return result.rows;
  });
}

// Queue status monitoring
setInterval(() => {
  console.log({
    pending: snowflakeQueue.pending,
    size: snowflakeQueue.size,
  });
}, 30000);
```

### Step 5: SQL API Rate Limiting

```typescript
// When using Snowflake SQL REST API (/api/v2/statements)
// Limit: 10 concurrent requests per user

async function sqlApiQuery(
  accountUrl: string,
  token: string,
  sqlText: string
): Promise<any> {
  const response = await fetch(
    `https://${accountUrl}/api/v2/statements`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT',
      },
      body: JSON.stringify({
        statement: sqlText,
        timeout: 60,
        database: 'MY_DB',
        schema: 'PUBLIC',
        warehouse: 'COMPUTE_WH',
        role: 'MY_ROLE',
      }),
    }
  );

  if (response.status === 429) {
    // SQL API throttled — back off and retry
    const retryAfter = parseInt(response.headers.get('Retry-After') || '10');
    await new Promise((r) => setTimeout(r, retryAfter * 1000));
    return sqlApiQuery(accountUrl, token, sqlText);
  }

  return response.json();
}
```

## Error Handling

| Symptom | Cause | Solution |
|---------|-------|----------|
| Queries queuing (high latency) | Warehouse undersized | Scale up or enable multi-cluster |
| 429 from SQL API | >10 concurrent API requests | Reduce concurrency, use driver instead |
| `000630: Statement timeout` | Query too slow for timeout | Optimize query or increase timeout |
| Login throttled | Too many connect/disconnect | Use connection pooling |
| Snowpipe backlog | High file volume | Increase pipe throughput, split files |

## Resources

- [Warehouse Considerations](https://docs.snowflake.com/en/user-guide/warehouses-considerations)
- [Multi-Cluster Warehouses](https://docs.snowflake.com/en/user-guide/warehouses-multicluster)
- [SQL API Reference](https://docs.snowflake.com/en/developer-guide/sql-api/reference)

## Next Steps

For security configuration, see `snowflake-security-basics`.
