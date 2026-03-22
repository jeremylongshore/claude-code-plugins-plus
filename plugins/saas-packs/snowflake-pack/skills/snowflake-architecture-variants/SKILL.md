---
name: snowflake-architecture-variants
description: |
  Choose and implement Snowflake architecture blueprints: data lakehouse, data mesh,
  data sharing, and Snowpark-native patterns for different scales.
  Use when designing Snowflake data platforms, choosing between architectures,
  or implementing data sharing and Snowpark patterns.
  Trigger with phrases like "snowflake architecture", "snowflake lakehouse",
  "snowflake data mesh", "snowflake data sharing", "snowflake Snowpark".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake Architecture Variants

## Overview

Three validated architecture blueprints for Snowflake deployments: traditional data warehouse, lakehouse with Iceberg, and data mesh with data sharing.

## Variant A: Traditional Data Warehouse

**Best for:** Single team, centralized analytics, < 50 users

```
┌──────────────────────────┐
│   Snowflake Account      │
│                          │
│  ┌────────┐  ┌────────┐  │
│  │ Bronze │→ │ Silver │→ Gold │
│  └────────┘  └────────┘       │
│                               │
│  ┌─────────────────────┐      │
│  │ Single ETL Warehouse │      │
│  └─────────────────────┘      │
│                               │
│  ┌──────────┐ ┌──────────┐   │
│  │ BI Tools │ │ Analysts │   │
│  └──────────┘ └──────────┘   │
└──────────────────────────────┘
```

```sql
-- Simple single-account setup
CREATE DATABASE DW;
CREATE SCHEMA DW.RAW;
CREATE SCHEMA DW.CURATED;
CREATE SCHEMA DW.ANALYTICS;

CREATE WAREHOUSE ETL_WH WAREHOUSE_SIZE = 'MEDIUM' AUTO_SUSPEND = 120;
CREATE WAREHOUSE QUERY_WH WAREHOUSE_SIZE = 'SMALL' AUTO_SUSPEND = 60;
```

## Variant B: Lakehouse with Iceberg Tables

**Best for:** Hybrid cloud/on-prem, existing data lake, open table format requirement

```
┌──────────────────────┐     ┌─────────────────────┐
│   External Storage   │     │  Snowflake Account   │
│   (S3/GCS/Azure)     │     │                      │
│                      │     │  ┌────────────────┐   │
│  ┌─────────────┐     │←───→│  │ Iceberg Tables │   │
│  │ Parquet/    │     │     │  │ (managed)      │   │
│  │ Iceberg     │     │     │  └────────────────┘   │
│  │ files       │     │     │                      │
│  └─────────────┘     │     │  ┌────────────────┐   │
│                      │     │  │ Native Tables  │   │
│  ┌─────────────┐     │     │  │ (hot data)     │   │
│  │ Spark/Flink │     │     │  └────────────────┘   │
│  │ (external)  │     │     │                      │
│  └─────────────┘     │     │  ┌────────────────┐   │
└──────────────────────┘     │  │ Dynamic Tables │   │
                             │  │ (transforms)   │   │
                             │  └────────────────┘   │
                             └──────────────────────┘
```

```sql
-- Iceberg table backed by external storage
CREATE ICEBERG TABLE events_iceberg (
  event_id STRING,
  event_type STRING,
  event_data VARIANT,
  event_timestamp TIMESTAMP_NTZ
)
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'my_s3_volume'
  BASE_LOCATION = 'iceberg/events/';

-- External volume for S3
CREATE EXTERNAL VOLUME my_s3_volume
  STORAGE_LOCATIONS = (
    (NAME = 'primary'
     STORAGE_BASE_URL = 's3://my-data-lake/'
     STORAGE_PROVIDER = 'S3'
     STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789:role/snowflake-iceberg')
  );

-- Dynamic Iceberg table for transforms (writes back to your storage)
CREATE DYNAMIC ICEBERG TABLE curated_events
  TARGET_LAG = '30 minutes'
  WAREHOUSE = ETL_WH
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'my_s3_volume'
  BASE_LOCATION = 'iceberg/curated_events/'
AS
  SELECT event_id, event_type, event_data,
         event_timestamp, CURRENT_TIMESTAMP() AS processed_at
  FROM events_iceberg
  WHERE event_type IS NOT NULL;
```

## Variant C: Data Mesh with Data Sharing

**Best for:** Multi-team, multi-account, decentralized ownership

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Finance Account │   │  Marketing Acct  │   │  Engineering    │
│                  │   │                  │   │  Account        │
│  ┌────────────┐  │   │  ┌────────────┐  │   │  ┌────────────┐ │
│  │ Finance DB │  │   │  │ Marketing  │  │   │  │ Product DB │ │
│  │ (owner)    │──┼──→│  │ DB (owner) │──┼──→│  │ (owner)    │ │
│  └────────────┘  │   │  └────────────┘  │   │  └────────────┘ │
│                  │   │                  │   │                 │
│  ┌────────────┐  │   │  ┌────────────┐  │   │  ┌────────────┐ │
│  │ Shared:    │  │   │  │ Shared:    │  │   │  │ Shared:    │ │
│  │ Product,   │←─┼───┼──│ Finance    │←─┼───┼──│ Marketing, │ │
│  │ Marketing  │  │   │  │ Product    │  │   │  │ Finance    │ │
│  └────────────┘  │   │  └────────────┘  │   │  └────────────┘ │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

```sql
-- PROVIDER: Create a share from Finance account
CREATE SHARE finance_share;
GRANT USAGE ON DATABASE FINANCE_DW TO SHARE finance_share;
GRANT USAGE ON SCHEMA FINANCE_DW.GOLD TO SHARE finance_share;

-- Only share secure views (hides underlying SQL)
CREATE SECURE VIEW FINANCE_DW.GOLD.REVENUE_SUMMARY AS
  SELECT region, product_line,
         SUM(revenue) AS total_revenue,
         COUNT(DISTINCT customer_id) AS customer_count
  FROM FINANCE_DW.SILVER.TRANSACTIONS
  GROUP BY region, product_line;

GRANT SELECT ON VIEW FINANCE_DW.GOLD.REVENUE_SUMMARY TO SHARE finance_share;

-- Add consumer accounts
ALTER SHARE finance_share ADD ACCOUNTS = myorg.marketing_account, myorg.engineering_account;

-- CONSUMER: Create database from share
CREATE DATABASE FINANCE_SHARED FROM SHARE myorg.finance_account.finance_share;
-- Zero-copy, real-time, no data movement

-- Query shared data as if it's local
SELECT * FROM FINANCE_SHARED.GOLD.REVENUE_SUMMARY
WHERE region = 'North America';
```

## Variant D: Snowpark-Native Application

**Best for:** ML/AI workloads, Python-heavy teams, stored procedure logic

```python
# Snowpark Python — run Python natively inside Snowflake
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, sum as sf_sum, avg

# Create session
session = Session.builder.configs({
    "account": os.environ['SNOWFLAKE_ACCOUNT'],
    "user": os.environ['SNOWFLAKE_USER'],
    "password": os.environ['SNOWFLAKE_PASSWORD'],
    "warehouse": "ML_WH",
    "database": "PROD_DW",
    "schema": "GOLD",
}).create()

# DataFrame API (lazy evaluation, pushdown to Snowflake)
orders_df = session.table("orders")
revenue = (
    orders_df
    .filter(col("order_date") >= "2026-01-01")
    .group_by("customer_id")
    .agg(
        sf_sum("amount").alias("total_spend"),
        avg("amount").alias("avg_order"),
    )
    .filter(col("total_spend") > 1000)
    .sort(col("total_spend").desc())
)
revenue.show()  # Executes in Snowflake, not locally

# Register as stored procedure (runs inside Snowflake)
@session.sproc(name="train_model", replace=True, is_permanent=True,
               stage_location="@ML_STAGE", packages=["scikit-learn"])
def train_model(session: Session, table_name: str) -> str:
    df = session.table(table_name).to_pandas()
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier()
    model.fit(df[['feature1', 'feature2']], df['label'])
    return f"Trained on {len(df)} rows, score: {model.score(...)}"

# Register UDF
@session.udf(name="predict_churn", replace=True, is_permanent=True,
             stage_location="@ML_STAGE")
def predict_churn(tenure: int, monthly_charge: float) -> float:
    # Model loaded from stage at runtime
    return model.predict_proba([[tenure, monthly_charge]])[0][1]
```

## Decision Matrix

| Factor | Traditional DW | Lakehouse | Data Mesh | Snowpark |
|--------|---------------|-----------|-----------|----------|
| Team Size | 1-10 | 5-30 | 10+ (multi-team) | 3-20 |
| Data Volume | Any | Large (10TB+) | Any | Any |
| External Tools | BI only | Spark, Flink, Presto | BI per domain | Python/ML |
| Governance | Centralized | Centralized | Federated | Centralized |
| Complexity | Low | Medium | High | Medium |
| Cost Model | Compute + storage | Reduced storage | Per-domain | Compute-heavy |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Share access denied | Consumer not added | `ALTER SHARE x ADD ACCOUNTS = y` |
| Iceberg sync delay | External catalog lag | Check external volume config |
| Snowpark OOM | Large DataFrame | Use `session.table()` not `to_pandas()` for large data |
| Cross-account query slow | Network latency | Deploy in same region |

## Resources

- [Data Sharing](https://docs.snowflake.com/en/user-guide/data-sharing-intro)
- [Iceberg Tables](https://docs.snowflake.com/en/user-guide/tables-iceberg)
- [Snowpark Python](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
- [Secure Views](https://docs.snowflake.com/en/user-guide/views-secure)

## Next Steps

For common anti-patterns, see `snowflake-known-pitfalls`.
