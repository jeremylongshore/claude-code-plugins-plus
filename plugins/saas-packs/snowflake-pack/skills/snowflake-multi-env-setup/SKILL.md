---
name: snowflake-multi-env-setup
description: |
  Configure Snowflake across dev, staging, and production with account-level isolation,
  zero-copy clones, and environment-specific RBAC.
  Trigger with phrases like "snowflake environments", "snowflake staging",
  "snowflake dev prod", "snowflake clone", "snowflake environment setup".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Multi-Environment Setup

## Overview

Configure dev/staging/production environments using Snowflake's zero-copy cloning, separate databases, and environment-specific roles and warehouses.

## Environment Strategy

| Environment | Approach | Data | Warehouse | Cost |
|-------------|----------|------|-----------|------|
| Development | Cloned DB, XSMALL WH | Zero-copy clone (refreshed weekly) | DEV_WH_XS | Minimal |
| Staging | Cloned DB, same-size WH | Zero-copy clone (refreshed daily) | STAGING_WH | Moderate |
| Production | Source of truth | Real data | PROD_WH (multi-cluster) | Full |

## Instructions

### Step 1: Create Environment Databases with Zero-Copy Cloning

```sql
-- Zero-copy clone creates instant copy with no additional storage cost
-- Storage cost only accrues when cloned data diverges from source

-- Clone production to staging (point-in-time)
CREATE DATABASE STAGING_DW CLONE PROD_DW;

-- Clone to dev
CREATE DATABASE DEV_DW CLONE PROD_DW;

-- Clone from a specific point in time (Time Travel)
CREATE DATABASE STAGING_DW CLONE PROD_DW
  AT (TIMESTAMP => '2026-03-21 06:00:00'::TIMESTAMP_NTZ);

-- Refresh clone (drop and re-clone)
-- Schedule this as a task:
CREATE OR REPLACE TASK refresh_staging_clone
  WAREHOUSE = ADMIN_WH
  SCHEDULE = 'USING CRON 0 4 * * * America/New_York'  -- 4 AM ET daily
AS
  BEGIN
    DROP DATABASE IF EXISTS STAGING_DW;
    CREATE DATABASE STAGING_DW CLONE PROD_DW;
    -- Re-grant permissions after clone
    GRANT USAGE ON DATABASE STAGING_DW TO ROLE STAGING_ROLE;
    GRANT USAGE ON ALL SCHEMAS IN DATABASE STAGING_DW TO ROLE STAGING_ROLE;
    GRANT SELECT ON ALL TABLES IN DATABASE STAGING_DW TO ROLE STAGING_ROLE;
  END;

ALTER TASK refresh_staging_clone RESUME;
```

### Step 2: Environment-Specific Warehouses

```sql
-- Development: minimal size, aggressive auto-suspend
CREATE WAREHOUSE DEV_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  RESOURCE_MONITOR = dev_monitor;

-- Staging: mirrors production size for realistic testing
CREATE WAREHOUSE STAGING_WH
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 120
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  RESOURCE_MONITOR = staging_monitor;

-- Production: multi-cluster for concurrency
CREATE WAREHOUSE PROD_WH
  WAREHOUSE_SIZE = 'MEDIUM'
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 4
  SCALING_POLICY = 'STANDARD'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  RESOURCE_MONITOR = prod_monitor;

-- Resource monitors per environment
CREATE RESOURCE MONITOR dev_monitor
  WITH CREDIT_QUOTA = 50 FREQUENCY = MONTHLY START_TIMESTAMP = IMMEDIATELY
  TRIGGERS ON 100 PERCENT DO SUSPEND;

CREATE RESOURCE MONITOR staging_monitor
  WITH CREDIT_QUOTA = 200 FREQUENCY = MONTHLY START_TIMESTAMP = IMMEDIATELY
  TRIGGERS ON 90 PERCENT DO NOTIFY ON 100 PERCENT DO SUSPEND;

CREATE RESOURCE MONITOR prod_monitor
  WITH CREDIT_QUOTA = 2000 FREQUENCY = MONTHLY START_TIMESTAMP = IMMEDIATELY
  TRIGGERS ON 75 PERCENT DO NOTIFY ON 90 PERCENT DO NOTIFY ON 100 PERCENT DO SUSPEND;
```

### Step 3: Environment-Specific Roles

```sql
-- Dev role: full access to dev DB only
CREATE ROLE DEV_ROLE;
GRANT USAGE ON WAREHOUSE DEV_WH TO ROLE DEV_ROLE;
GRANT ALL ON DATABASE DEV_DW TO ROLE DEV_ROLE;
GRANT ALL ON ALL SCHEMAS IN DATABASE DEV_DW TO ROLE DEV_ROLE;

-- Staging role: read/write staging, read-only prod
CREATE ROLE STAGING_ROLE;
GRANT USAGE ON WAREHOUSE STAGING_WH TO ROLE STAGING_ROLE;
GRANT ALL ON DATABASE STAGING_DW TO ROLE STAGING_ROLE;
GRANT USAGE ON DATABASE PROD_DW TO ROLE STAGING_ROLE;
GRANT SELECT ON ALL TABLES IN DATABASE PROD_DW TO ROLE STAGING_ROLE;

-- Production role: minimal, service-account driven
CREATE ROLE PROD_ETL_ROLE;
GRANT USAGE ON WAREHOUSE PROD_WH TO ROLE PROD_ETL_ROLE;
GRANT ALL ON DATABASE PROD_DW TO ROLE PROD_ETL_ROLE;

-- Hierarchy
GRANT ROLE DEV_ROLE TO ROLE SYSADMIN;
GRANT ROLE STAGING_ROLE TO ROLE SYSADMIN;
GRANT ROLE PROD_ETL_ROLE TO ROLE SYSADMIN;
```

### Step 4: Application Configuration

```typescript
// src/snowflake/env-config.ts
type Environment = 'development' | 'staging' | 'production';

interface SnowflakeEnvConfig {
  account: string;
  warehouse: string;
  database: string;
  role: string;
}

const ENV_CONFIGS: Record<Environment, SnowflakeEnvConfig> = {
  development: {
    account: process.env.SNOWFLAKE_ACCOUNT!,
    warehouse: 'DEV_WH',
    database: 'DEV_DW',
    role: 'DEV_ROLE',
  },
  staging: {
    account: process.env.SNOWFLAKE_ACCOUNT!,
    warehouse: 'STAGING_WH',
    database: 'STAGING_DW',
    role: 'STAGING_ROLE',
  },
  production: {
    account: process.env.SNOWFLAKE_ACCOUNT!,
    warehouse: 'PROD_WH',
    database: 'PROD_DW',
    role: 'PROD_ETL_ROLE',
  },
};

export function getEnvConfig(): SnowflakeEnvConfig {
  const env = (process.env.NODE_ENV || 'development') as Environment;
  const config = ENV_CONFIGS[env];
  if (!config) throw new Error(`Unknown environment: ${env}`);
  return config;
}
```

### Step 5: Data Masking for Non-Production

```sql
-- Mask PII in dev/staging clones
CREATE OR REPLACE MASKING POLICY pii_mask AS (val STRING)
  RETURNS STRING ->
  CASE
    WHEN CURRENT_DATABASE() = 'PROD_DW' THEN val
    ELSE SHA2(val)  -- Hash PII in non-prod
  END;

-- Apply to sensitive columns
ALTER TABLE DEV_DW.SILVER.USERS MODIFY COLUMN email
  SET MASKING POLICY pii_mask;
ALTER TABLE STAGING_DW.SILVER.USERS MODIFY COLUMN email
  SET MASKING POLICY pii_mask;
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Clone takes too long | Very large DB | Clone is instant; check for metadata operations |
| Wrong database context | Environment mismatch | Verify `NODE_ENV` and connection config |
| Dev credits exhausted | Resource monitor hit | Increase quota or wait for monthly reset |
| Clone permissions lost | Grants not re-applied after refresh | Add grants to refresh task |

## Resources

- [Zero-Copy Cloning](https://docs.snowflake.com/en/sql-reference/sql/create-clone)
- [Time Travel](https://docs.snowflake.com/en/user-guide/data-time-travel)
- [Masking Policies](https://docs.snowflake.com/en/user-guide/tag-based-masking-policies)

## Next Steps

For observability setup, see `snowflake-observability`.
