---
name: databricks-reference-architecture
description: |
  Implement Databricks reference architecture with best-practice project layout.
  Use when designing new Databricks projects, reviewing architecture,
  or establishing standards for Databricks applications.
  Trigger with phrases like "databricks architecture", "databricks best practices",
  "databricks project structure", "how to organize databricks", "databricks layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, databricks-reference]

---
# Databricks Reference Architecture

## Overview
Production-ready lakehouse architecture with Unity Catalog, Delta Lake, and the medallion pattern. Covers workspace organization, three-level namespace governance, compute strategy, CI/CD with Asset Bundles, and project structure for team collaboration.

## Prerequisites
- Databricks workspace with Unity Catalog enabled
- Understanding of medallion architecture (bronze/silver/gold)
- Databricks CLI configured
- Terraform or Asset Bundles for infrastructure

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNITY CATALOG                                  │
│                                                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  │  Bronze    │  │  Silver    │  │   Gold     │  │ ML Models │  │
│  │  Catalog   │─▶│  Catalog   │─▶│  Catalog   │  │ (MLflow)  │  │
│  │  (raw)     │  │  (clean)   │  │  (curated) │  │           │  │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │
│       ▲                                    │                      │
│  ┌────────────┐                   ┌────────────────┐             │
│  │ Auto Loader│                   │ Model Serving  │             │
│  │ Ingestion  │                   │ Endpoints      │             │
│  └────────────┘                   └────────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│  Compute: Job Clusters │ SQL Warehouses │ Instance Pools        │
├─────────────────────────────────────────────────────────────────┤
│  Security: Row Filters │ Column Masks │ Secret Scopes │ SCIM   │
├─────────────────────────────────────────────────────────────────┤
│  CI/CD: Asset Bundles │ GitHub Actions │ dev/staging/prod       │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
databricks-platform/
├── src/
│   ├── ingestion/
│   │   ├── bronze_raw_events.py       # Auto Loader streaming
│   │   ├── bronze_api_data.py         # REST API batch ingestion
│   │   └── bronze_file_uploads.py     # Manual file uploads
│   ├── transformation/
│   │   ├── silver_clean_events.py     # Cleansing + dedup
│   │   ├── silver_schema_enforce.py   # Schema validation
│   │   └── silver_scd2.py            # Slowly changing dimensions
│   ├── aggregation/
│   │   ├── gold_daily_metrics.py      # Business KPIs
│   │   ├── gold_user_features.py      # ML feature engineering
│   │   └── gold_reporting.py          # BI-ready views
│   └── ml/
│       ├── training/
│       │   └── train_churn_model.py
│       └── inference/
│           └── batch_scoring.py
├── tests/
│   ├── conftest.py                    # Spark fixtures
│   ├── unit/                          # Local Spark tests
│   └── integration/                   # Databricks Connect tests
├── resources/
│   ├── etl_jobs.yml                   # ETL job definitions
│   ├── ml_jobs.yml                    # ML pipeline definitions
│   └── maintenance.yml                # OPTIMIZE/VACUUM schedules
├── databricks.yml                     # Asset Bundle root config
├── pyproject.toml
└── requirements.txt
```

## Instructions

### Step 1: Unity Catalog Hierarchy
```sql
-- One catalog per environment (or shared with schema isolation)
CREATE CATALOG IF NOT EXISTS dev_catalog;
CREATE CATALOG IF NOT EXISTS prod_catalog;

-- Medallion schemas per catalog
CREATE SCHEMA IF NOT EXISTS prod_catalog.bronze;
CREATE SCHEMA IF NOT EXISTS prod_catalog.silver;
CREATE SCHEMA IF NOT EXISTS prod_catalog.gold;
CREATE SCHEMA IF NOT EXISTS prod_catalog.ml_features;
CREATE SCHEMA IF NOT EXISTS prod_catalog.ml_models;

-- Permissions: engineers write bronze/silver, analysts read gold
GRANT USAGE ON CATALOG prod_catalog TO `data-engineers`;
GRANT CREATE, MODIFY, SELECT ON SCHEMA prod_catalog.bronze TO `data-engineers`;
GRANT CREATE, MODIFY, SELECT ON SCHEMA prod_catalog.silver TO `data-engineers`;
GRANT SELECT ON SCHEMA prod_catalog.gold TO `data-engineers`;

GRANT USAGE ON CATALOG prod_catalog TO `data-analysts`;
GRANT SELECT ON SCHEMA prod_catalog.gold TO `data-analysts`;
```

### Step 2: Asset Bundle Configuration
```yaml
# databricks.yml
bundle:
  name: data-platform

workspace:
  host: ${DATABRICKS_HOST}

include:
  - resources/*.yml

variables:
  catalog:
    default: dev_catalog
  alert_email:
    default: dev@company.com

targets:
  dev:
    default: true
    mode: development
    workspace:
      root_path: /Users/${workspace.current_user.userName}/.bundle/${bundle.name}/dev

  staging:
    variables:
      catalog: staging_catalog

  prod:
    mode: production
    variables:
      catalog: prod_catalog
      alert_email: oncall@company.com
    workspace:
      root_path: /Shared/.bundle/${bundle.name}/prod
```

### Step 3: Compute Strategy
```yaml
# resources/etl_jobs.yml
resources:
  jobs:
    daily_etl:
      name: "daily-etl-${bundle.target}"
      schedule:
        quartz_cron_expression: "0 0 6 * * ?"
        timezone_id: "UTC"
      max_concurrent_runs: 1

      tasks:
        - task_key: bronze
          notebook_task:
            notebook_path: src/ingestion/bronze_raw_events.py
          job_cluster_key: etl

        - task_key: silver
          depends_on: [{task_key: bronze}]
          notebook_task:
            notebook_path: src/transformation/silver_clean_events.py
          job_cluster_key: etl

        - task_key: gold
          depends_on: [{task_key: silver}]
          notebook_task:
            notebook_path: src/aggregation/gold_daily_metrics.py
          job_cluster_key: etl

      job_clusters:
        - job_cluster_key: etl
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            node_type_id: "i3.xlarge"
            autoscale:
              min_workers: 1
              max_workers: 4
            aws_attributes:
              availability: SPOT_WITH_FALLBACK
              first_on_demand: 1
            spark_conf:
              spark.databricks.delta.optimizeWrite.enabled: "true"
              spark.databricks.delta.autoCompact.enabled: "true"
```

### Step 4: Medallion Pipeline Pattern
```python
# src/ingestion/bronze_raw_events.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, input_file_name

spark = SparkSession.builder.getOrCreate()

# Bronze: Auto Loader for incremental file ingestion
raw = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", "/checkpoints/bronze/events/schema")
    .option("cloudFiles.inferColumnTypes", "true")
    .load("s3://data-lake/raw/events/")
    .withColumn("_ingested_at", current_timestamp())
    .withColumn("_source_file", input_file_name())
)

(raw.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/bronze/events/data")
    .toTable("prod_catalog.bronze.raw_events"))
```

### Step 5: Table Maintenance Schedule
```yaml
# resources/maintenance.yml
resources:
  jobs:
    weekly_optimize:
      name: "maintenance-optimize-${bundle.target}"
      schedule:
        quartz_cron_expression: "0 0 2 ? * SUN"
        timezone_id: "UTC"
      tasks:
        - task_key: optimize_tables
          notebook_task:
            notebook_path: src/maintenance/optimize_tables.py
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            node_type_id: "m5.xlarge"
            num_workers: 1
```

```python
# src/maintenance/optimize_tables.py
tables_to_optimize = [
    ("prod_catalog.silver.orders", ["order_date", "region"]),
    ("prod_catalog.silver.events", ["event_date"]),
    ("prod_catalog.gold.daily_metrics", []),
]

for table, z_cols in tables_to_optimize:
    if z_cols:
        spark.sql(f"OPTIMIZE {table} ZORDER BY ({', '.join(z_cols)})")
    else:
        spark.sql(f"OPTIMIZE {table}")
    spark.sql(f"VACUUM {table} RETAIN 168 HOURS")
    print(f"Maintained: {table}")
```

## Output
- Unity Catalog hierarchy with env-isolated catalogs and medallion schemas
- Asset Bundle with dev/staging/prod targets and variable overrides
- Medallion pipeline (Auto Loader > MERGE > aggregations)
- RBAC grants separating engineer write from analyst read-only
- Table maintenance schedule (weekly OPTIMIZE + VACUUM)

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Schema evolution failure | New source columns | Auto Loader handles with `schemaEvolutionMode` |
| Permission denied on schema | Missing `USAGE` on parent catalog | `GRANT USAGE ON CATALOG` first |
| Concurrent write conflict | Multiple jobs writing same table | `max_concurrent_runs: 1` in job config |
| Cluster timeout | Long-running tasks | Set `timeout_seconds` per task |

## Examples

### Validate Data Flow
```sql
SELECT 'bronze' AS layer, COUNT(*) AS rows FROM prod_catalog.bronze.raw_events
UNION ALL SELECT 'silver', COUNT(*) FROM prod_catalog.silver.events
UNION ALL SELECT 'gold', COUNT(*) FROM prod_catalog.gold.daily_metrics;
```

## Resources
- [Unity Catalog Best Practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [Declarative Automation Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [Auto Loader](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/)
