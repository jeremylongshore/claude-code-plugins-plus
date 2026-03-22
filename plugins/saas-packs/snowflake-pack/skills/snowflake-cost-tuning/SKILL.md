---
name: snowflake-cost-tuning
description: |
  Optimize Snowflake costs with resource monitors, warehouse auto-suspend,
  right-sizing, and credit consumption analysis.
  Use when analyzing Snowflake billing, reducing credit consumption,
  or implementing cost controls and budget alerts.
  Trigger with phrases like "snowflake cost", "snowflake billing",
  "reduce snowflake cost", "snowflake credits", "snowflake expensive", "snowflake budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Cost Tuning

## Overview

Optimize Snowflake costs through resource monitors, warehouse right-sizing, auto-suspend tuning, and credit consumption analysis.

## Snowflake Pricing Model

| Cost Component | What It Measures | Typical % of Bill |
|---------------|-----------------|-------------------|
| Compute (credits) | Warehouse running time | 60-80% |
| Storage | Data at rest (compressed) | 10-20% |
| Cloud services | Metadata ops, auth, compilation | 5-10% |
| Data transfer | Egress between regions/clouds | 0-5% |
| Serverless | Snowpipe, auto-clustering, MV refresh | Variable |

**Credit rates by warehouse size:**

| Size | Credits/Hour | Nodes |
|------|-------------|-------|
| X-Small | 1 | 1 |
| Small | 2 | 2 |
| Medium | 4 | 4 |
| Large | 8 | 8 |
| X-Large | 16 | 16 |
| 2X-Large | 32 | 32 |

## Instructions

### Step 1: Analyze Current Credit Consumption

```sql
-- Credits by warehouse (last 30 days)
SELECT warehouse_name,
       SUM(credits_used) AS total_credits,
       SUM(credits_used_compute) AS compute_credits,
       SUM(credits_used_cloud_services) AS cloud_credits,
       ROUND(SUM(credits_used) * 3.0, 2) AS est_cost_usd  -- ~$3/credit standard
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(days, -30, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY total_credits DESC;

-- Daily credit trend
SELECT DATE_TRUNC('day', start_time) AS day,
       SUM(credits_used) AS credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD(days, -30, CURRENT_TIMESTAMP())
GROUP BY day
ORDER BY day;

-- Idle warehouse time (credits wasted while no queries running)
SELECT warehouse_name,
       SUM(credits_used) AS total_credits,
       COUNT(DISTINCT query_id) AS queries,
       CASE WHEN COUNT(DISTINCT query_id) = 0 THEN SUM(credits_used)
            ELSE 0 END AS idle_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY w
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q
  ON w.warehouse_name = q.warehouse_name
  AND DATE_TRUNC('hour', w.start_time) = DATE_TRUNC('hour', q.start_time)
WHERE w.start_time >= DATEADD(days, -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY idle_credits DESC;
```

### Step 2: Set Up Resource Monitors

```sql
-- Account-level resource monitor
CREATE OR REPLACE RESOURCE MONITOR account_monthly
  WITH CREDIT_QUOTA = 5000
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 50 PERCENT DO NOTIFY
    ON 75 PERCENT DO NOTIFY
    ON 90 PERCENT DO NOTIFY
    ON 100 PERCENT DO SUSPEND
    ON 110 PERCENT DO SUSPEND_IMMEDIATE;

ALTER ACCOUNT SET RESOURCE_MONITOR = account_monthly;

-- Per-warehouse monitor for ETL
CREATE OR REPLACE RESOURCE MONITOR etl_daily
  WITH CREDIT_QUOTA = 100
  FREQUENCY = DAILY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 80 PERCENT DO NOTIFY
    ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE PROD_ETL_WH SET RESOURCE_MONITOR = etl_daily;
```

### Step 3: Optimize Auto-Suspend

```sql
-- Short auto-suspend for bursty workloads (ETL)
ALTER WAREHOUSE ETL_WH SET AUTO_SUSPEND = 60;     -- 1 minute

-- Longer for interactive analytics (avoids constant resume)
ALTER WAREHOUSE ANALYTICS_WH SET AUTO_SUSPEND = 300;  -- 5 minutes

-- Check current auto-suspend settings
SELECT name, size, auto_suspend, auto_resume,
       CASE WHEN auto_suspend > 300 THEN 'REVIEW: high auto_suspend'
            ELSE 'OK' END AS recommendation
FROM INFORMATION_SCHEMA.WAREHOUSES;

-- Never set auto_suspend = 0 in production (warehouse runs forever)
```

### Step 4: Right-Size Warehouses

```sql
-- Find oversized warehouses (low utilization)
SELECT warehouse_name, warehouse_size,
       AVG(avg_running) AS avg_queries_running,
       AVG(avg_queued_load) AS avg_queries_queued,
       CASE
         WHEN AVG(avg_queued_load) > 1 THEN 'SCALE UP or add clusters'
         WHEN AVG(avg_running) < 1 THEN 'Consider DOWNSIZE'
         ELSE 'RIGHT-SIZED'
       END AS recommendation
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_LOAD_HISTORY(
  DATE_RANGE_START => DATEADD(days, -7, CURRENT_TIMESTAMP())
))
GROUP BY warehouse_name, warehouse_size;

-- Downsize underutilized warehouses
ALTER WAREHOUSE DEV_WH SET WAREHOUSE_SIZE = 'XSMALL';
```

### Step 5: Reduce Storage Costs

```sql
-- Find large unused tables
SELECT table_catalog, table_schema, table_name,
       bytes / 1e9 AS gb,
       row_count,
       last_altered,
       DATEDIFF('day', last_altered, CURRENT_DATE()) AS days_since_modified
FROM SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
WHERE bytes > 1e9  -- > 1 GB
  AND DATEDIFF('day', last_altered, CURRENT_DATE()) > 90
ORDER BY bytes DESC;

-- Reduce Time Travel retention for non-critical tables
ALTER TABLE staging.temp_data SET DATA_RETENTION_TIME_IN_DAYS = 1;

-- Use transient tables for staging (no Fail-safe storage)
CREATE TRANSIENT TABLE staging.temp_load (
  id INTEGER, data VARIANT
);
```

### Step 6: Serverless Feature Cost Control

```sql
-- Monitor Snowpipe costs
SELECT pipe_name, SUM(credits_used) AS credits
FROM SNOWFLAKE.ACCOUNT_USAGE.PIPE_USAGE_HISTORY
WHERE start_time >= DATEADD(days, -30, CURRENT_TIMESTAMP())
GROUP BY pipe_name
ORDER BY credits DESC;

-- Monitor auto-clustering costs
SELECT table_name, SUM(credits_used) AS credits
FROM SNOWFLAKE.ACCOUNT_USAGE.AUTOMATIC_CLUSTERING_HISTORY
WHERE start_time >= DATEADD(days, -30, CURRENT_TIMESTAMP())
GROUP BY table_name
ORDER BY credits DESC;

-- Monitor materialized view refresh costs
SELECT table_name, SUM(credits_used) AS credits
FROM SNOWFLAKE.ACCOUNT_USAGE.MATERIALIZED_VIEW_REFRESH_HISTORY
WHERE start_time >= DATEADD(days, -30, CURRENT_TIMESTAMP())
GROUP BY table_name
ORDER BY credits DESC;
```

## Cost Reduction Checklist

- [ ] Resource monitors on all production warehouses
- [ ] Auto-suspend < 5 minutes on all warehouses
- [ ] No `WAREHOUSE_SIZE > 'MEDIUM'` without justification
- [ ] Transient tables for staging/temp data
- [ ] Time Travel retention minimized for non-critical tables
- [ ] Clustering keys only on tables > 1TB with frequent filter queries
- [ ] Review serverless feature costs monthly

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected credit spike | Runaway query or always-on warehouse | Check QUERY_HISTORY, set auto-suspend |
| Resource monitor suspended warehouse | Exceeded quota | Increase quota or optimize workload |
| High cloud services cost | Many small metadata queries | Batch operations, reduce DDL frequency |
| Storage growing fast | No cleanup policy | Archive old data, use transient tables |

## Resources

- [Cost Controls](https://docs.snowflake.com/en/user-guide/cost-controlling-controls)
- [Resource Monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)
- [CREATE RESOURCE MONITOR](https://docs.snowflake.com/en/sql-reference/sql/create-resource-monitor)
- [Budgets](https://docs.snowflake.com/en/user-guide/budgets)

## Next Steps

For architecture patterns, see `snowflake-reference-architecture`.
