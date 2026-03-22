---
name: snowflake-core-workflow-b
description: |
  Execute Snowflake data transformation with streams, tasks, and dynamic tables.
  Use when building ELT pipelines, scheduling transformations,
  or implementing change data capture with Snowflake streams.
  Trigger with phrases like "snowflake transform", "snowflake ELT",
  "snowflake stream", "snowflake task", "snowflake pipeline",
  "snowflake dynamic table", "snowflake CDC".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Core Workflow B — Data Transformation

## Overview

Build ELT pipelines using streams (change data capture), tasks (scheduling), and dynamic tables (declarative transforms).

## Prerequisites

- Data loaded into Snowflake (via `snowflake-core-workflow-a`)
- Understanding of ELT vs ETL patterns
- Role with `CREATE TASK`, `CREATE STREAM` privileges

## Instructions

### Step 1: Create a Stream for Change Data Capture

```sql
-- Track changes on the raw orders table
CREATE OR REPLACE STREAM orders_stream ON TABLE raw_orders
  APPEND_ONLY = FALSE;

-- Append-only stream (lighter weight, inserts only)
CREATE OR REPLACE STREAM events_stream ON TABLE raw_events
  APPEND_ONLY = TRUE;

-- Check what's changed since last consumption
SELECT * FROM orders_stream;
-- METADATA$ACTION = 'INSERT' | 'DELETE'
-- METADATA$ISUPDATE = TRUE if row is part of an UPDATE
-- METADATA$ROW_ID = unique row identifier
```

### Step 2: Create a Task to Process Stream Data

```sql
-- Transform task runs when stream has data
CREATE OR REPLACE TASK transform_orders
  WAREHOUSE = TRANSFORM_WH
  SCHEDULE = '5 MINUTE'
  WHEN SYSTEM$STREAM_HAS_DATA('orders_stream')
AS
  MERGE INTO dim_orders AS target
  USING (
    SELECT
      order_id,
      customer_id,
      amount::DECIMAL(12,2) AS amount,
      order_date::TIMESTAMP_NTZ AS order_date,
      CASE
        WHEN amount >= 1000 THEN 'high_value'
        WHEN amount >= 100 THEN 'medium_value'
        ELSE 'standard'
      END AS order_tier,
      CURRENT_TIMESTAMP() AS processed_at
    FROM orders_stream
    WHERE METADATA$ACTION = 'INSERT'
  ) AS source
  ON target.order_id = source.order_id
  WHEN MATCHED THEN UPDATE SET
    target.amount = source.amount,
    target.order_tier = source.order_tier,
    target.processed_at = source.processed_at
  WHEN NOT MATCHED THEN INSERT
    (order_id, customer_id, amount, order_date, order_tier, processed_at)
  VALUES
    (source.order_id, source.customer_id, source.amount,
     source.order_date, source.order_tier, source.processed_at);

-- Enable the task
ALTER TASK transform_orders RESUME;
```

### Step 3: Build a Task DAG (Directed Acyclic Graph)

```sql
-- Root task: aggregate daily metrics
CREATE OR REPLACE TASK daily_metrics_root
  WAREHOUSE = TRANSFORM_WH
  SCHEDULE = 'USING CRON 0 6 * * * America/New_York'
AS
  INSERT INTO daily_order_metrics
  SELECT
    CURRENT_DATE() - 1 AS metric_date,
    COUNT(*) AS total_orders,
    SUM(amount) AS total_revenue,
    AVG(amount) AS avg_order_value,
    COUNT(DISTINCT customer_id) AS unique_customers
  FROM dim_orders
  WHERE order_date >= CURRENT_DATE() - 1
    AND order_date < CURRENT_DATE();

-- Child task: runs after root completes
CREATE OR REPLACE TASK update_customer_segments
  WAREHOUSE = TRANSFORM_WH
  AFTER daily_metrics_root
AS
  MERGE INTO customer_segments AS target
  USING (
    SELECT customer_id,
      COUNT(*) AS order_count,
      SUM(amount) AS lifetime_value,
      CASE
        WHEN SUM(amount) >= 10000 THEN 'platinum'
        WHEN SUM(amount) >= 5000 THEN 'gold'
        WHEN SUM(amount) >= 1000 THEN 'silver'
        ELSE 'bronze'
      END AS segment
    FROM dim_orders GROUP BY customer_id
  ) AS source
  ON target.customer_id = source.customer_id
  WHEN MATCHED THEN UPDATE SET
    target.order_count = source.order_count,
    target.lifetime_value = source.lifetime_value,
    target.segment = source.segment
  WHEN NOT MATCHED THEN INSERT VALUES
    (source.customer_id, source.order_count, source.lifetime_value, source.segment);

-- Resume tasks (children first, then root)
ALTER TASK update_customer_segments RESUME;
ALTER TASK daily_metrics_root RESUME;
```

### Step 4: Dynamic Tables (Declarative Alternative)

```sql
-- Auto-refreshes based on target freshness — no streams/tasks needed
CREATE OR REPLACE DYNAMIC TABLE customer_360
  TARGET_LAG = '10 minutes'
  WAREHOUSE = TRANSFORM_WH
AS
  SELECT
    c.customer_id, c.name, c.email,
    COUNT(o.order_id) AS total_orders,
    COALESCE(SUM(o.amount), 0) AS lifetime_value,
    MAX(o.order_date) AS last_order_date,
    DATEDIFF('day', MAX(o.order_date), CURRENT_DATE()) AS days_since_last_order
  FROM customers c
  LEFT JOIN dim_orders o ON c.customer_id = o.customer_id
  GROUP BY c.customer_id, c.name, c.email;

-- Monitor refresh status
SELECT name, target_lag, refresh_mode, scheduling_state
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLES())
WHERE name = 'CUSTOMER_360';
```

### Step 5: Monitor Pipelines

```sql
-- Task run history
SELECT name, state, error_message, scheduled_time
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
  SCHEDULED_TIME_RANGE_START => DATEADD(hours, -24, CURRENT_TIMESTAMP())
))
ORDER BY scheduled_time DESC;

-- Find failed runs
SELECT name, state, error_message, scheduled_time
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE state = 'FAILED'
  AND scheduled_time >= DATEADD(hours, -24, CURRENT_TIMESTAMP());

-- Stream lag check — if STALE = TRUE, data may be lost
SHOW STREAMS LIKE 'orders_stream';
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Task is suspended` | Not resumed after creation | `ALTER TASK x RESUME` |
| `Stream is stale` | Data retention exceeded | Recreate stream; increase `DATA_RETENTION_TIME_IN_DAYS` |
| `Warehouse does not exist` | Wrong warehouse in task | Verify warehouse name |
| `MERGE: duplicate rows` | Non-unique join key | Add dedup CTE before MERGE |
| `Dynamic table refresh failed` | Source schema changed | Check upstream table definitions |

## Resources

- [Streams and Tasks](https://docs.snowflake.com/en/user-guide/data-pipelines-intro)
- [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [CREATE TASK](https://docs.snowflake.com/en/sql-reference/sql/create-task)

## Next Steps

For common errors and troubleshooting, see `snowflake-common-errors`.
