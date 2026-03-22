---
name: snowflake-reference-architecture
description: |
  Implement Snowflake reference architecture with medallion pattern and Snowflake-native design.
  Use when designing a new Snowflake data platform, setting up bronze/silver/gold layers,
  or establishing architecture standards for a Snowflake deployment.
  Trigger with phrases like "snowflake architecture", "snowflake medallion",
  "snowflake best practices layout", "snowflake data platform design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Reference Architecture

## Overview

Production-ready Snowflake architecture using the medallion pattern (bronze/silver/gold), role-based access, and workload-isolated warehouses.

## Architecture Overview

```
                    ┌──────────────────────┐
                    │   Data Sources        │
                    │ (S3, APIs, DBs, SaaS) │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   BRONZE (Raw)        │
                    │   Snowpipe / COPY     │
                    │   VARIANT columns     │
                    └──────────┬───────────┘
                               │ Streams + Tasks
                    ┌──────────▼───────────┐
                    │   SILVER (Cleansed)   │
                    │   Typed columns       │
                    │   Deduped, validated   │
                    └──────────┬───────────┘
                               │ Dynamic Tables
                    ┌──────────▼───────────┐
                    │   GOLD (Business)     │
                    │   Aggregated          │
                    │   Analytics-ready     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Consumers           │
                    │   BI tools, APIs,     │
                    │   Data Sharing        │
                    └──────────────────────┘
```

## Database Layout

```sql
-- One database per environment, schemas per layer
CREATE DATABASE PROD_DW;

-- Bronze: Raw ingested data (append-only, VARIANT columns)
CREATE SCHEMA PROD_DW.BRONZE;

-- Silver: Cleansed, typed, deduplicated
CREATE SCHEMA PROD_DW.SILVER;

-- Gold: Business-level aggregations and dimensions
CREATE SCHEMA PROD_DW.GOLD;

-- Staging: Temporary tables for ETL processing
CREATE SCHEMA PROD_DW.STAGING;

-- Utility: Stored procedures, UDFs, file formats
CREATE SCHEMA PROD_DW.UTILITY;
```

## Instructions

### Step 1: Bronze Layer (Raw Ingestion)

```sql
-- Store raw data as VARIANT for schema-on-read
CREATE TABLE PROD_DW.BRONZE.RAW_EVENTS (
    ingestion_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    source_file VARCHAR(500),
    raw_data VARIANT
);

-- File format for JSON ingestion
CREATE FILE FORMAT PROD_DW.UTILITY.JSON_INGEST
  TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE;

-- Stage for S3 source
CREATE STAGE PROD_DW.UTILITY.S3_EVENTS_STAGE
  STORAGE_INTEGRATION = s3_integration
  URL = 's3://data-lake/events/'
  FILE_FORMAT = PROD_DW.UTILITY.JSON_INGEST;

-- Snowpipe for continuous ingestion
CREATE PIPE PROD_DW.BRONZE.EVENTS_PIPE
  AUTO_INGEST = TRUE
AS
  COPY INTO PROD_DW.BRONZE.RAW_EVENTS (source_file, raw_data)
  FROM (SELECT METADATA$FILENAME, $1 FROM @PROD_DW.UTILITY.S3_EVENTS_STAGE);
```

### Step 2: Silver Layer (Cleansing)

```sql
-- Stream on bronze table
CREATE STREAM PROD_DW.BRONZE.EVENTS_STREAM
  ON TABLE PROD_DW.BRONZE.RAW_EVENTS APPEND_ONLY = TRUE;

-- Silver table with typed columns
CREATE TABLE PROD_DW.SILVER.EVENTS (
    event_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    user_id INTEGER,
    event_data VARIANT,
    event_timestamp TIMESTAMP_NTZ NOT NULL,
    processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_events PRIMARY KEY (event_id)
);

-- Task to transform bronze → silver
CREATE TASK PROD_DW.SILVER.TRANSFORM_EVENTS
  WAREHOUSE = ETL_WH
  SCHEDULE = '5 MINUTE'
  WHEN SYSTEM$STREAM_HAS_DATA('PROD_DW.BRONZE.EVENTS_STREAM')
AS
  INSERT INTO PROD_DW.SILVER.EVENTS (event_id, event_type, user_id, event_data, event_timestamp)
  SELECT
    raw_data:id::VARCHAR AS event_id,
    raw_data:type::VARCHAR AS event_type,
    raw_data:user_id::INTEGER AS user_id,
    raw_data:data AS event_data,
    raw_data:timestamp::TIMESTAMP_NTZ AS event_timestamp
  FROM PROD_DW.BRONZE.EVENTS_STREAM
  WHERE raw_data:id IS NOT NULL
    AND raw_data:type IS NOT NULL
    AND raw_data:timestamp IS NOT NULL;

ALTER TASK PROD_DW.SILVER.TRANSFORM_EVENTS RESUME;
```

### Step 3: Gold Layer (Business Aggregations)

```sql
-- Dynamic table for real-time aggregation
CREATE DYNAMIC TABLE PROD_DW.GOLD.USER_ACTIVITY_SUMMARY
  TARGET_LAG = '30 minutes'
  WAREHOUSE = ANALYTICS_WH
AS
  SELECT
    user_id,
    COUNT(*) AS total_events,
    COUNT(DISTINCT event_type) AS unique_event_types,
    MIN(event_timestamp) AS first_seen,
    MAX(event_timestamp) AS last_seen,
    COUNT_IF(event_type = 'purchase') AS purchase_count,
    SUM(CASE WHEN event_type = 'purchase'
         THEN event_data:amount::DECIMAL(12,2) ELSE 0 END) AS total_spend
  FROM PROD_DW.SILVER.EVENTS
  GROUP BY user_id;

-- Materialized view for frequently-queried metrics
CREATE MATERIALIZED VIEW PROD_DW.GOLD.DAILY_METRICS AS
  SELECT
    DATE_TRUNC('day', event_timestamp) AS metric_date,
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT user_id) AS unique_users
  FROM PROD_DW.SILVER.EVENTS
  GROUP BY metric_date, event_type;
```

### Step 4: Warehouse Strategy

```sql
-- Workload-isolated warehouses
CREATE WAREHOUSE ETL_WH
  WAREHOUSE_SIZE = 'LARGE' AUTO_SUSPEND = 120 AUTO_RESUME = TRUE
  COMMENT = 'Bronze→Silver→Gold transformations';

CREATE WAREHOUSE ANALYTICS_WH
  WAREHOUSE_SIZE = 'MEDIUM'
  MIN_CLUSTER_COUNT = 1 MAX_CLUSTER_COUNT = 3
  SCALING_POLICY = 'STANDARD'
  AUTO_SUSPEND = 300 AUTO_RESUME = TRUE
  COMMENT = 'BI tools, ad-hoc analytics';

CREATE WAREHOUSE DASHBOARD_WH
  WAREHOUSE_SIZE = 'SMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE
  COMMENT = 'Dashboard refresh queries';

CREATE WAREHOUSE DEV_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE
  COMMENT = 'Development and testing';
```

### Step 5: Role Hierarchy

```sql
-- Custom roles following Snowflake best practices
CREATE ROLE DATA_ENGINEER;     -- Full access to bronze/silver
CREATE ROLE DATA_ANALYST;      -- Read silver/gold, write gold
CREATE ROLE BI_VIEWER;         -- Read-only gold layer
CREATE ROLE SVC_ETL;           -- Service account for pipelines

-- Hierarchy: custom roles → SYSADMIN
GRANT ROLE DATA_ENGINEER TO ROLE SYSADMIN;
GRANT ROLE DATA_ANALYST TO ROLE SYSADMIN;
GRANT ROLE BI_VIEWER TO ROLE DATA_ANALYST;
GRANT ROLE SVC_ETL TO ROLE DATA_ENGINEER;

-- Warehouse grants
GRANT USAGE ON WAREHOUSE ETL_WH TO ROLE DATA_ENGINEER;
GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE DATA_ANALYST;
GRANT USAGE ON WAREHOUSE DASHBOARD_WH TO ROLE BI_VIEWER;

-- Schema grants
GRANT ALL ON SCHEMA PROD_DW.BRONZE TO ROLE DATA_ENGINEER;
GRANT ALL ON SCHEMA PROD_DW.SILVER TO ROLE DATA_ENGINEER;
GRANT SELECT ON ALL TABLES IN SCHEMA PROD_DW.SILVER TO ROLE DATA_ANALYST;
GRANT SELECT ON ALL TABLES IN SCHEMA PROD_DW.GOLD TO ROLE DATA_ANALYST;
GRANT SELECT ON ALL TABLES IN SCHEMA PROD_DW.GOLD TO ROLE BI_VIEWER;
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Bronze data quality issues | Bad source data | Add validation in silver transform |
| Silver transform fails | Schema drift in source | Use TRY_CAST and COALESCE |
| Gold table stale | Dynamic table lag too high | Reduce TARGET_LAG or investigate |
| Warehouse contention | Shared warehouse | Separate workloads into dedicated warehouses |

## Resources

- [Snowflake Architecture](https://docs.snowflake.com/en/user-guide/intro-supported-features)
- [Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Access Control Best Practices](https://docs.snowflake.com/en/user-guide/security-access-control-considerations)

## Next Steps

For multi-environment setup, see `snowflake-multi-env-setup`.
