---
name: snowflake-known-pitfalls
description: |
  Identify and avoid Snowflake anti-patterns and common mistakes in SQL,
  warehouse management, data loading, and access control.
  Use when reviewing Snowflake configurations, onboarding new users,
  or auditing existing Snowflake deployments for best practices.
  Trigger with phrases like "snowflake mistakes", "snowflake anti-patterns",
  "snowflake pitfalls", "snowflake what not to do", "snowflake code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Known Pitfalls

## Overview

Common mistakes and anti-patterns when using Snowflake, with real SQL examples and fixes.

## Pitfall #1: Leaving Warehouses Running (Cost Killer)

**Anti-Pattern:**
```sql
-- Warehouse with auto_suspend = 0 (never suspends)
CREATE WAREHOUSE ALWAYS_ON_WH
  WAREHOUSE_SIZE = 'XLARGE'
  AUTO_SUSPEND = 0;
-- 16 credits/hour = ~$1,152/day at $3/credit
```

**Fix:**
```sql
ALTER WAREHOUSE ALWAYS_ON_WH SET
  AUTO_SUSPEND = 120,    -- Suspend after 2 min idle
  AUTO_RESUME = TRUE;    -- Resume on next query

-- Audit all warehouses for high auto_suspend
SELECT name, size, auto_suspend, state
FROM INFORMATION_SCHEMA.WAREHOUSES
WHERE auto_suspend > 600 OR auto_suspend = 0;
```

---

## Pitfall #2: Using ACCOUNTADMIN for Everything

**Anti-Pattern:**
```sql
-- Human users with ACCOUNTADMIN default role
ALTER USER analyst SET DEFAULT_ROLE = 'ACCOUNTADMIN';
-- One bad query can drop production databases
```

**Fix:**
```sql
-- Use least-privilege roles
ALTER USER analyst SET DEFAULT_ROLE = 'DATA_ANALYST';

-- Audit ACCOUNTADMIN usage
SELECT grantee_name, role
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
WHERE role = 'ACCOUNTADMIN' AND deleted_on IS NULL;
-- Should be < 3 users, all named admins
```

---

## Pitfall #3: SELECT * on Wide Tables

**Anti-Pattern:**
```sql
-- Scans ALL columns (Snowflake stores columnar — unused cols waste I/O)
SELECT * FROM events;  -- 200 columns, only need 3
```

**Fix:**
```sql
-- Select only needed columns — dramatically reduces bytes scanned
SELECT event_id, event_type, event_timestamp FROM events;

-- Check column pruning impact
SELECT bytes_scanned FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY_BY_SESSION())
ORDER BY start_time DESC LIMIT 1;
```

---

## Pitfall #4: Clustering Keys on Small Tables

**Anti-Pattern:**
```sql
-- Clustering key on a 10,000 row table
ALTER TABLE config_settings CLUSTER BY (category);
-- Costs credits for reclustering with zero performance benefit
```

**Fix:**
```sql
-- Only cluster tables > 1TB with frequent filter queries
-- Check table size before clustering
SELECT table_name, row_count, bytes / 1e9 AS gb
FROM INFORMATION_SCHEMA.TABLES
WHERE table_name = 'CONFIG_SETTINGS';
-- If < 1 GB, clustering is waste

-- Remove unnecessary clustering
ALTER TABLE config_settings DROP CLUSTERING KEY;
```

---

## Pitfall #5: Not Using MERGE for Idempotent Loads

**Anti-Pattern:**
```sql
-- INSERT creates duplicates on retry
INSERT INTO dim_orders SELECT * FROM staging_orders;
-- Network blip → retry → duplicate rows
```

**Fix:**
```sql
-- MERGE is idempotent — safe to retry
MERGE INTO dim_orders AS target
USING staging_orders AS source
ON target.order_id = source.order_id
WHEN MATCHED THEN UPDATE SET
  target.amount = source.amount,
  target.updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT
  (order_id, amount, created_at)
VALUES (source.order_id, source.amount, CURRENT_TIMESTAMP());
```

---

## Pitfall #6: Ignoring Stale Streams

**Anti-Pattern:**
```sql
-- Stream goes stale when retention period is exceeded
-- (source table changes exceed DATA_RETENTION_TIME_IN_DAYS)
-- Result: DATA LOSS — changes between old and new offset are gone
```

**Fix:**
```sql
-- Monitor stream staleness
SELECT stream_name, stale
FROM INFORMATION_SCHEMA.STREAMS
WHERE stale = TRUE;

-- Increase retention on source tables
ALTER TABLE raw_orders SET DATA_RETENTION_TIME_IN_DAYS = 14;

-- Set up alert for stale streams
CREATE ALERT stale_stream_alert
  WAREHOUSE = ADMIN_WH
  SCHEDULE = '30 MINUTE'
  IF (EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.STREAMS WHERE stale = TRUE))
  THEN CALL SYSTEM$SEND_EMAIL(...);
```

---

## Pitfall #7: Loading Many Small Files

**Anti-Pattern:**
```bash
# 100,000 small files (< 100KB each) in stage
# Each file = separate micro-partition = metadata overhead
```

**Fix:**
```sql
-- Combine small files before loading
-- Or use Snowpipe with recommended file sizes (100-250 MB)

-- Check COPY history for file size issues
SELECT file_name, file_size, row_count
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  TABLE_NAME => 'MY_TABLE',
  START_TIME => DATEADD(hours, -24, CURRENT_TIMESTAMP())
))
WHERE file_size < 100000  -- Files under 100KB
ORDER BY file_size;
```

---

## Pitfall #8: No Resource Monitors

**Anti-Pattern:**
```sql
-- No resource monitors = unlimited credit consumption
-- A runaway query or always-on warehouse can burn thousands of credits
```

**Fix:**
```sql
CREATE RESOURCE MONITOR monthly_budget
  WITH CREDIT_QUOTA = 2000
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 75 PERCENT DO NOTIFY
    ON 100 PERCENT DO SUSPEND
    ON 110 PERCENT DO SUSPEND_IMMEDIATE;

ALTER ACCOUNT SET RESOURCE_MONITOR = monthly_budget;
```

---

## Pitfall #9: Using Transient Tables for Important Data

**Anti-Pattern:**
```sql
-- Transient tables have NO Fail-safe (7 days of extra recovery)
-- and max 1 day of Time Travel
CREATE TRANSIENT TABLE critical_orders (...);
-- Data loss risk if table is accidentally dropped after 1 day
```

**Fix:**
```sql
-- Use permanent tables for important data
CREATE TABLE critical_orders (...);
ALTER TABLE critical_orders SET DATA_RETENTION_TIME_IN_DAYS = 14;

-- Use transient only for truly temporary data
CREATE TRANSIENT TABLE temp_staging_batch (...);
```

---

## Pitfall #10: Wrong Account Identifier Format

**Anti-Pattern:**
```typescript
// Using the full URL instead of account identifier
const conn = snowflake.createConnection({
  account: 'myaccount.us-east-1.snowflakecomputing.com',  // WRONG
});
// Results in: "Could not connect to Snowflake backend"
```

**Fix:**
```typescript
const conn = snowflake.createConnection({
  account: 'myorg-myaccount',  // Correct: orgname-accountname format
});
// For legacy locator format: 'xy12345.us-east-1' (include region)
```

## Quick Audit Script

```sql
-- Run this monthly to catch common pitfalls
SELECT 'Always-on warehouses' AS check,
       COUNT(*) AS issues
FROM INFORMATION_SCHEMA.WAREHOUSES
WHERE auto_suspend = 0 OR auto_suspend > 3600

UNION ALL

SELECT 'ACCOUNTADMIN default role',
       COUNT(*)
FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
WHERE default_role = 'ACCOUNTADMIN' AND disabled = 'false'

UNION ALL

SELECT 'Stale streams',
       COUNT(*)
FROM INFORMATION_SCHEMA.STREAMS
WHERE stale = TRUE

UNION ALL

SELECT 'No resource monitor',
       CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END
FROM INFORMATION_SCHEMA.RESOURCE_MONITORS

UNION ALL

SELECT 'Tables without clustering (>1TB)',
       COUNT(*)
FROM INFORMATION_SCHEMA.TABLES
WHERE bytes > 1e12
  AND auto_clustering_on = 'NO';
```

## Quick Reference Card

| Pitfall | Detection | Prevention |
|---------|-----------|------------|
| Always-on warehouse | `auto_suspend = 0` | Set 60-300s |
| ACCOUNTADMIN abuse | `GRANTS_TO_USERS` audit | Enforce least privilege |
| SELECT * | High `bytes_scanned` | Column pruning |
| Unnecessary clustering | Small table < 1TB | Only cluster large tables |
| INSERT duplicates | Row count mismatch | Use MERGE |
| Stale streams | `stale = TRUE` | Increase retention |
| Small files | COPY_HISTORY file_size | Batch files to 100-250MB |
| No resource monitor | Account check | Create immediately |
| Transient for critical data | Table type audit | Use permanent tables |
| Wrong account format | Connection error | Use `orgname-accountname` |

## Resources

- [Warehouse Considerations](https://docs.snowflake.com/en/user-guide/warehouses-considerations)
- [Access Control Best Practices](https://docs.snowflake.com/en/user-guide/security-access-control-considerations)
- [Data Loading Best Practices](https://docs.snowflake.com/en/user-guide/data-load-considerations-prepare)
