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
---
# Databricks Reference Architecture

## Overview
Production-ready lakehouse architecture with Unity Catalog, Delta Lake, and medallion pattern. Covers workspace organization, data governance, and CI/CD integration for enterprise data platforms.

## Prerequisites
- Databricks workspace with Unity Catalog enabled
- Understanding of medallion architecture (bronze/silver/gold)
- Databricks CLI configured
- Terraform or Asset Bundles for infrastructure

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Unity Catalog                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Bronze   │  │ Silver   │  │ Gold     │                   │
│  │ Catalog  │─▶│ Catalog  │─▶│ Catalog  │                   │
│  │ (raw)    │  │ (clean)  │  │ (curated)│                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
│       ▲                            │                         │
│       │                            ▼                         │
│  ┌──────────┐              ┌──────────────┐                  │
│  │ Ingestion│              │ ML Models    │                  │
│  │ Jobs     │              │ (MLflow)     │                  │
│  └──────────┘              └──────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│  Compute: Job Clusters │ SQL Warehouses │ Interactive       │
├─────────────────────────────────────────────────────────────┤
│  Governance: Row-Level Security │ Column Masking │ Lineage  │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
databricks-project/
├── src/
│   ├── ingestion/
│   │   ├── bronze_raw_events.py
│   │   ├── bronze_api_data.py
│   │   └── bronze_file_uploads.py
│   ├── transformation/
│   │   ├── silver_clean_events.py
│   │   ├── silver_deduplicate.py
│   │   └── silver_schema_enforce.py
│   ├── aggregation/
│   │   ├── gold_daily_metrics.py
│   │   ├── gold_user_features.py
│   │   └── gold_ml_features.py
│   └── ml/
│       ├── training/
│       └── inference/
├── tests/
│   ├── unit/
│   └── integration/
├── databricks.yml           # Asset Bundle config
├── resources/
│   ├── jobs.yml
│   ├── pipelines.yml
│   └── clusters.yml
└── conf/
    ├── dev.yml
    ├── staging.yml
    └── prod.yml
```

## Instructions

### Step 1: Configure Unity Catalog Hierarchy
```sql
-- Create catalog per environment
CREATE CATALOG IF NOT EXISTS dev_catalog;
CREATE CATALOG IF NOT EXISTS prod_catalog;

-- Create schemas per medallion layer
CREATE SCHEMA IF NOT EXISTS prod_catalog.bronze;
CREATE SCHEMA IF NOT EXISTS prod_catalog.silver;
CREATE SCHEMA IF NOT EXISTS prod_catalog.gold;
CREATE SCHEMA IF NOT EXISTS prod_catalog.ml_features;

-- Grant permissions
GRANT USE CATALOG ON CATALOG prod_catalog TO `data-engineers`;
GRANT USE SCHEMA ON SCHEMA prod_catalog.bronze TO `data-engineers`;
GRANT SELECT ON SCHEMA prod_catalog.gold TO `analysts`;
```

### Step 2: Define Asset Bundle Configuration
```yaml
# databricks.yml
bundle:
  name: data-platform

workspace:
  host: https://your-workspace.databricks.com

resources:
  jobs:
    daily_etl:
      name: "Daily ETL Pipeline"
      schedule:
        quartz_cron_expression: "0 0 6 * * ?"
        timezone_id: "UTC"
      tasks:
        - task_key: bronze_ingest
          notebook_task:
            notebook_path: src/ingestion/bronze_raw_events.py
          job_cluster_key: etl_cluster
        - task_key: silver_transform
          depends_on:
            - task_key: bronze_ingest
          notebook_task:
            notebook_path: src/transformation/silver_clean_events.py
          job_cluster_key: etl_cluster

  job_clusters:
    - job_cluster_key: etl_cluster
      new_cluster:
        spark_version: "14.3.x-scala2.12"
        node_type_id: "i3.xlarge"
        num_workers: 2
        autoscale:
          min_workers: 1
          max_workers: 4

targets:
  dev:
    default: true
    workspace:
      host: https://dev-workspace.databricks.com
  prod:
    workspace:
      host: https://prod-workspace.databricks.com
```

### Step 3: Implement Medallion Pipeline Pattern
```python
# src/ingestion/bronze_raw_events.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, input_file_name

spark = SparkSession.builder.getOrCreate()

# Bronze: raw ingestion with metadata
raw_df = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", "/checkpoints/bronze/schema")
    .load("/data/raw/events/")
)

bronze_df = raw_df.withColumn(
    "_ingested_at", current_timestamp()
).withColumn(
    "_source_file", input_file_name()
)

(bronze_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/bronze/events")
    .toTable("prod_catalog.bronze.raw_events"))
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Schema evolution failure | New columns in source | Enable `mergeSchema` option |
| Job cluster timeout | Long-running tasks | Use autoscaling, increase timeout |
| Permission denied | Missing catalog grants | Check Unity Catalog ACLs |
| Delta version conflict | Concurrent writes | Use `MERGE` instead of `INSERT` |

## Examples

### Quick Medallion Validation
```python
# Validate data flows through medallion layers
for layer in ["bronze", "silver", "gold"]:
    count = spark.table(f"prod_catalog.{layer}.events").count()
    print(f"{layer}: {count:,} rows")
```

## Resources
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Unity Catalog Best Practices](https://docs.databricks.com/data-governance/unity-catalog/)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale