---
name: snowflake-migration-deep-dive
description: |
  Execute migration to Snowflake from Redshift, BigQuery, or on-prem databases
  with data transfer, schema conversion, and validation strategies.
  Use when migrating to Snowflake from another platform, planning data transfers,
  or re-platforming existing data warehouses to Snowflake.
  Trigger with phrases like "migrate to snowflake", "snowflake migration",
  "redshift to snowflake", "bigquery to snowflake", "snowflake replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Migration Deep Dive

## Overview

Comprehensive guide for migrating to Snowflake from Redshift, BigQuery, on-prem databases, or other data warehouses.

## Migration Types

| Source | Complexity | Duration | Key Challenge |
|--------|-----------|----------|---------------|
| Amazon Redshift | Medium | 2-6 weeks | SQL dialect differences |
| Google BigQuery | Medium | 2-6 weeks | Nested/repeated fields |
| On-prem (Oracle/SQL Server) | High | 1-3 months | Data transfer bandwidth |
| Another Snowflake account | Low | Days | Replication or data sharing |

## Instructions

### Step 1: Schema Conversion

```sql
-- Common SQL differences from Redshift/BigQuery

-- Redshift DISTKEY/SORTKEY → Snowflake clustering (optional, for large tables)
-- Redshift: CREATE TABLE orders (id INT) DISTSTYLE KEY DISTKEY(customer_id) SORTKEY(order_date);
-- Snowflake:
CREATE TABLE orders (
  id INTEGER AUTOINCREMENT,
  customer_id INTEGER,
  order_date TIMESTAMP_NTZ
);
ALTER TABLE orders CLUSTER BY (order_date);  -- Only for tables > 1TB

-- Redshift IDENTITY → Snowflake AUTOINCREMENT
-- Redshift: id INT IDENTITY(1,1)
-- Snowflake: id INTEGER AUTOINCREMENT START 1 INCREMENT 1

-- BigQuery STRUCT/ARRAY → Snowflake VARIANT/ARRAY
-- BigQuery: address STRUCT<street STRING, city STRING>
-- Snowflake:
CREATE TABLE customers (
  id INTEGER,
  address VARIANT  -- Store as JSON: {"street": "...", "city": "..."}
);
-- Access: SELECT address:street::VARCHAR FROM customers

-- BigQuery REPEATED fields → Snowflake ARRAY
-- BigQuery: tags ARRAY<STRING>
-- Snowflake: tags ARRAY

-- Data types mapping
-- Redshift VARCHAR(MAX) → Snowflake VARCHAR (16MB max)
-- Redshift TIMESTAMPTZ → Snowflake TIMESTAMP_TZ
-- BigQuery INT64 → Snowflake NUMBER(38,0)
-- BigQuery FLOAT64 → Snowflake FLOAT
-- BigQuery BYTES → Snowflake BINARY
-- Oracle CLOB → Snowflake VARCHAR
-- SQL Server DATETIME2 → Snowflake TIMESTAMP_NTZ
```

### Step 2: Data Transfer Methods

```bash
# Method 1: Through cloud storage (recommended for large datasets)

# From Redshift → S3 → Snowflake
# Step A: Unload from Redshift to S3
psql -h redshift-cluster.xxx.region.redshift.amazonaws.com -d mydb -c "
  UNLOAD ('SELECT * FROM orders')
  TO 's3://migration-bucket/redshift/orders/'
  IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftUnload'
  FORMAT PARQUET;
"

# Step B: Load from S3 to Snowflake
snowsql -c prod -q "
  CREATE STAGE migration_stage
    STORAGE_INTEGRATION = s3_integration
    URL = 's3://migration-bucket/redshift/';

  COPY INTO orders
    FROM @migration_stage/orders/
    FILE_FORMAT = (TYPE = 'PARQUET')
    MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;
"
```

```python
# Method 2: Direct transfer via Python (for smaller tables)
import snowflake.connector
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas

# Read from source (Redshift example)
import psycopg2
source_conn = psycopg2.connect(
    host='redshift-cluster.xxx.redshift.amazonaws.com',
    dbname='source_db', user='admin', password='***', port=5439
)
df = pd.read_sql('SELECT * FROM orders', source_conn)
print(f"Read {len(df)} rows from Redshift")

# Write to Snowflake
sf_conn = snowflake.connector.connect(
    account=os.environ['SNOWFLAKE_ACCOUNT'],
    user=os.environ['SNOWFLAKE_USER'],
    password=os.environ['SNOWFLAKE_PASSWORD'],
    warehouse='ETL_WH',
    database='PROD_DW',
    schema='SILVER',
)
success, nchunks, nrows, _ = write_pandas(sf_conn, df, 'ORDERS')
print(f"Loaded {nrows} rows to Snowflake in {nchunks} chunks")
```

### Step 3: Data Validation

```sql
-- Row count comparison
SELECT 'orders' AS table_name,
       (SELECT COUNT(*) FROM prod_dw.silver.orders) AS snowflake_count,
       12345678 AS source_count,  -- Replace with actual source count
       (SELECT COUNT(*) FROM prod_dw.silver.orders) - 12345678 AS diff;

-- Checksum validation (aggregate comparison)
SELECT
  COUNT(*) AS row_count,
  SUM(amount) AS total_amount,
  MIN(order_date) AS min_date,
  MAX(order_date) AS max_date,
  COUNT(DISTINCT customer_id) AS unique_customers
FROM prod_dw.silver.orders;
-- Compare these values with source system

-- Sample-based validation
SELECT *
FROM prod_dw.silver.orders
WHERE order_id IN (1001, 5000, 10000, 50000, 100000)
ORDER BY order_id;
-- Compare row-by-row with source

-- Data type validation
SELECT column_name, data_type, is_nullable,
       character_maximum_length, numeric_precision, numeric_scale
FROM INFORMATION_SCHEMA.COLUMNS
WHERE table_name = 'ORDERS'
ORDER BY ordinal_position;
```

### Step 4: Query Migration

```sql
-- Common SQL translation patterns

-- Redshift: GETDATE() → Snowflake: CURRENT_TIMESTAMP()
-- Redshift: DATEDIFF(day, a, b) → Snowflake: DATEDIFF('day', a, b)  (string date part)
-- Redshift: NVL(a, b) → Snowflake: COALESCE(a, b) or NVL(a, b)  (both work)
-- Redshift: LISTAGG(col, ',') → Snowflake: LISTAGG(col, ',')  (same)
-- Redshift: DECODE(a, 1, 'x', 2, 'y') → Snowflake: DECODE(a, 1, 'x', 2, 'y')  (same)

-- BigQuery: SAFE_DIVIDE(a, b) → Snowflake: DIV0(a, b)  or a / NULLIF(b, 0)
-- BigQuery: FORMAT_DATE('%Y-%m', date) → Snowflake: TO_CHAR(date, 'YYYY-MM')
-- BigQuery: UNNEST(array) → Snowflake: LATERAL FLATTEN(input => array)
-- BigQuery: STRUCT access a.b.c → Snowflake: a:b:c (colon path notation)

-- Example: BigQuery UNNEST → Snowflake FLATTEN
-- BigQuery:
--   SELECT id, tag FROM orders, UNNEST(tags) AS tag
-- Snowflake:
SELECT o.id, f.value::VARCHAR AS tag
FROM orders o, LATERAL FLATTEN(input => o.tags) f;
```

### Step 5: Cutover Plan

```
Week 1-2: Setup
├─ Create Snowflake account and configure
├─ Design schema (converted from source)
├─ Set up storage integration for data transfer
└─ Create roles, warehouses, resource monitors

Week 3-4: Data Migration
├─ Full historical load via cloud storage
├─ Validate row counts and checksums
├─ Convert and test critical queries
└─ Set up ongoing CDC (if parallel run needed)

Week 5-6: Parallel Run
├─ Run both systems simultaneously
├─ Compare query results between source and Snowflake
├─ Migrate BI tools to point at Snowflake
└─ Train users on Snowflake SQL differences

Week 7: Cutover
├─ Final delta sync from source
├─ Switch all connections to Snowflake
├─ Decommission source system (after validation period)
└─ Document and postmortem
```

## Rollback Plan

```sql
-- Keep source system running for rollback period (2-4 weeks)
-- If rollback needed:

-- 1. Redirect connections back to source
-- 2. Sync any new data from Snowflake back to source (if needed)
-- 3. Document what went wrong

-- Snowflake Time Travel as safety net during migration
ALTER DATABASE PROD_DW SET DATA_RETENTION_TIME_IN_DAYS = 30;
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Data type mismatch | Schema conversion error | Use TRY_CAST for safe conversion |
| Row count mismatch | Duplicate handling differs | Check dedup logic in source vs target |
| Query results differ | SQL dialect difference | Test each function translation |
| Transfer too slow | Large dataset, small warehouse | Use LARGE warehouse for COPY INTO |
| Parquet schema evolution | Column added mid-migration | Use `MATCH_BY_COLUMN_NAME` |

## Resources

- [Migration Guides](https://docs.snowflake.com/en/user-guide/data-load-overview)
- [SQL Translation (from Redshift)](https://docs.snowflake.com/en/guides/migration/redshift)
- [FLATTEN Function](https://docs.snowflake.com/en/sql-reference/functions/flatten)
- [write_pandas](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-pandas)

## Next Steps

For advanced troubleshooting, see `snowflake-advanced-troubleshooting`.
