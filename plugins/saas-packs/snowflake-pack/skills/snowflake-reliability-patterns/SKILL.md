---
name: snowflake-reliability-patterns
description: |
  Implement Snowflake reliability patterns: replication, failover, Time Travel recovery,
  and application-level resilience for Snowflake integrations.
  Use when building fault-tolerant pipelines, configuring disaster recovery,
  or adding resilience to production Snowflake services.
  Trigger with phrases like "snowflake reliability", "snowflake failover",
  "snowflake replication", "snowflake disaster recovery", "snowflake Time Travel".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Reliability Patterns

## Overview

Production-grade reliability patterns for Snowflake: database replication, account failover, Time Travel recovery, and application-level circuit breakers.

## Instructions

### Step 1: Time Travel for Point-in-Time Recovery

```sql
-- Query historical data (up to 90 days on Enterprise Edition)
SELECT * FROM orders
AT (TIMESTAMP => '2026-03-21 14:00:00'::TIMESTAMP_NTZ);

-- Restore a table to a previous state
CREATE OR REPLACE TABLE orders
  CLONE orders AT (TIMESTAMP => '2026-03-21 14:00:00'::TIMESTAMP_NTZ);

-- Restore a dropped table
UNDROP TABLE orders;
UNDROP SCHEMA my_schema;
UNDROP DATABASE my_database;

-- Query by offset (5 minutes ago)
SELECT * FROM orders AT (OFFSET => -300);

-- Query by statement ID (before a specific query ran)
SELECT * FROM orders BEFORE (STATEMENT => '<query_id_of_bad_update>');

-- Set retention period per table
ALTER TABLE critical_data SET DATA_RETENTION_TIME_IN_DAYS = 90;
ALTER TABLE temp_staging SET DATA_RETENTION_TIME_IN_DAYS = 0;  -- No Time Travel
```

### Step 2: Database Replication Across Regions

```sql
-- Enable replication on source account (primary)
ALTER DATABASE PROD_DW ENABLE REPLICATION TO ACCOUNTS
  myorg.us_east_account,
  myorg.eu_west_account;

-- On target account: create replica database
CREATE DATABASE PROD_DW_REPLICA
  AS REPLICA OF myorg.us_west_account.PROD_DW;

-- Refresh replica (manual or scheduled)
ALTER DATABASE PROD_DW_REPLICA REFRESH;

-- Check replication status
SELECT * FROM TABLE(INFORMATION_SCHEMA.DATABASE_REPLICATION_USAGE_HISTORY(
  DATE_RANGE_START => DATEADD(hours, -24, CURRENT_TIMESTAMP())
));

-- Check replication lag
SELECT database_name, primary_snowflake_region,
       replication_allowed, is_primary,
       DATEDIFF('minute', snowflake_region_last_refresh_time, CURRENT_TIMESTAMP()) AS lag_minutes
FROM TABLE(INFORMATION_SCHEMA.REPLICATION_DATABASES())
WHERE database_name = 'PROD_DW_REPLICA';
```

### Step 3: Account Failover Groups

```sql
-- Create failover group (replicates databases, warehouses, roles, etc.)
-- On primary account:
CREATE FAILOVER GROUP prod_failover
  OBJECT_TYPES = DATABASES, WAREHOUSES, ROLES, USERS, INTEGRATIONS
  ALLOWED_DATABASES = PROD_DW
  ALLOWED_ACCOUNTS = myorg.us_east_account
  REPLICATION_SCHEDULE = '10 MINUTE';

-- On secondary account: create as replica
CREATE FAILOVER GROUP prod_failover
  AS REPLICA OF myorg.us_west_account.prod_failover;

-- Promote secondary to primary (during outage)
ALTER FAILOVER GROUP prod_failover PRIMARY;

-- After recovery, switch back
-- On original primary:
ALTER FAILOVER GROUP prod_failover PRIMARY;
```

### Step 4: Application-Level Connection Failover

```typescript
// src/snowflake/resilient-connection.ts
import snowflake from 'snowflake-sdk';

interface FailoverConfig {
  primary: snowflake.ConnectionOptions;
  secondary: snowflake.ConnectionOptions;
  healthCheckIntervalMs: number;
}

class ResilientSnowflakeConnection {
  private activeConn: snowflake.Connection | null = null;
  private isPrimary = true;
  private config: FailoverConfig;

  constructor(config: FailoverConfig) {
    this.config = config;
  }

  async connect(): Promise<snowflake.Connection> {
    try {
      this.activeConn = await this.tryConnect(this.config.primary);
      this.isPrimary = true;
      return this.activeConn;
    } catch (primaryErr) {
      console.warn('Primary Snowflake connection failed, trying secondary');
      try {
        this.activeConn = await this.tryConnect(this.config.secondary);
        this.isPrimary = false;
        return this.activeConn;
      } catch (secondaryErr) {
        throw new Error(`Both Snowflake connections failed.
          Primary: ${primaryErr.message}
          Secondary: ${secondaryErr.message}`);
      }
    }
  }

  private tryConnect(opts: snowflake.ConnectionOptions): Promise<snowflake.Connection> {
    return new Promise((resolve, reject) => {
      const conn = snowflake.createConnection(opts);
      conn.connect((err, conn) => (err ? reject(err) : resolve(conn)));
    });
  }

  async healthCheck(): Promise<{ connected: boolean; isPrimary: boolean }> {
    try {
      await new Promise<void>((resolve, reject) => {
        this.activeConn!.execute({
          sqlText: 'SELECT 1',
          complete: (err) => (err ? reject(err) : resolve()),
        });
      });
      return { connected: true, isPrimary: this.isPrimary };
    } catch {
      return { connected: false, isPrimary: this.isPrimary };
    }
  }
}

// Usage
const resilientConn = new ResilientSnowflakeConnection({
  primary: {
    account: 'myorg-primary',
    username: process.env.SNOWFLAKE_USER!,
    password: process.env.SNOWFLAKE_PASSWORD!,
    warehouse: 'PROD_WH',
    database: 'PROD_DW',
  },
  secondary: {
    account: 'myorg-secondary',
    username: process.env.SNOWFLAKE_USER!,
    password: process.env.SNOWFLAKE_PASSWORD!,
    warehouse: 'PROD_WH',
    database: 'PROD_DW_REPLICA',
  },
  healthCheckIntervalMs: 30000,
});
```

### Step 5: Pipeline Retry and Idempotency

```sql
-- Idempotent data loading (safe to retry)
MERGE INTO silver.orders AS target
USING (
  SELECT * FROM bronze.raw_orders
  WHERE ingestion_time >= DATEADD(hours, -1, CURRENT_TIMESTAMP())
) AS source
ON target.order_id = source.order_id
WHEN NOT MATCHED THEN INSERT
  (order_id, customer_id, amount, order_date)
VALUES
  (source.order_id, source.customer_id, source.amount, source.order_date);

-- MERGE is idempotent: running it twice with the same data produces the same result
-- Prefer MERGE over INSERT for retry-safe pipelines

-- Task retry configuration
CREATE OR REPLACE TASK reliable_transform
  WAREHOUSE = ETL_WH
  SCHEDULE = '5 MINUTE'
  ALLOW_OVERLAPPING_EXECUTION = FALSE  -- Prevent concurrent runs
  SUSPEND_TASK_AFTER_NUM_FAILURES = 3  -- Auto-suspend after 3 failures
  WHEN SYSTEM$STREAM_HAS_DATA('orders_stream')
AS
  MERGE INTO dim_orders ...;

ALTER TASK reliable_transform RESUME;
```

### Step 6: Backup Strategy

```sql
-- Zero-copy clone backups (instant, no extra storage until data changes)
CREATE DATABASE PROD_DW_BACKUP_20260322
  CLONE PROD_DW;

-- Automated daily backup via task
CREATE OR REPLACE TASK daily_backup
  WAREHOUSE = ADMIN_WH
  SCHEDULE = 'USING CRON 0 3 * * * UTC'
AS
BEGIN
  LET backup_name VARCHAR := 'PROD_DW_BACKUP_' || TO_CHAR(CURRENT_DATE(), 'YYYYMMDD');
  EXECUTE IMMEDIATE 'CREATE DATABASE IF NOT EXISTS ' || :backup_name || ' CLONE PROD_DW';
  -- Clean up backups older than 7 days
  -- (done via separate cleanup task or stored procedure)
END;
```

## Recovery Time Objectives

| Scenario | Recovery Method | RTO | RPO |
|----------|---------------|-----|-----|
| Accidental table drop | UNDROP | Instant | Zero |
| Bad data update | Time Travel CLONE | Minutes | Configurable (up to 90 days) |
| Regional outage | Failover group | 10-30 min | Replication lag |
| Account compromise | Contact Snowflake support | Hours | Last backup |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Time Travel expired | Past retention period | Increase DATA_RETENTION_TIME_IN_DAYS |
| Replication lag high | Large data changes | Check replication schedule, network |
| Failover fails | Secondary not synced | Verify failover group status |
| UNDROP fails | Object recreated with same name | Rename current object first |

## Resources

- [Time Travel](https://docs.snowflake.com/en/user-guide/data-time-travel)
- [Database Replication](https://docs.snowflake.com/en/user-guide/account-replication-intro)
- [Failover Groups](https://docs.snowflake.com/en/user-guide/account-replication-failover-failback)
- [Business Continuity](https://docs.snowflake.com/en/user-guide/replication-intro)

## Next Steps

For policy enforcement, see `snowflake-policy-guardrails`.
