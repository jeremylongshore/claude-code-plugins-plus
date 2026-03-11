---
name: databricks-core-workflow-a
description: |
  Execute Databricks primary workflow: Delta Lake ETL pipelines.
  Use when building data ingestion pipelines, implementing medallion architecture,
  or creating Delta Lake transformations.
  Trigger with phrases like "databricks ETL", "delta lake pipeline",
  "medallion architecture", "databricks data pipeline", "bronze silver gold".
allowed-tools: Read, Write, Edit, Bash(databricks:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Databricks Core Workflow A: Delta Lake ETL

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Build production Delta Lake ETL pipelines using medallion architecture (Bronze -> Silver -> Gold).

## Prerequisites
- Completed `databricks-install-auth` setup
- Understanding of Delta Lake concepts
- Unity Catalog configured (recommended)

## Medallion Architecture
```
Raw Sources -> Bronze (Raw/Landing) -> Silver (Cleaned/Business Logic) -> Gold (Aggregated/Analytics Ready)
```

## Instructions

### Step 1: Bronze Layer - Raw Ingestion
Ingest raw data with metadata columns (`_ingested_at`, `_source_file`). Use `mergeSchema` for schema evolution. Use Auto Loader (`cloudFiles`) for streaming ingestion with schema inference.

### Step 2: Silver Layer - Data Cleansing
Read from Bronze using Change Data Feed. Apply transformations: trim/lowercase strings, parse timestamps, hash PII, filter nulls, generate surrogate keys. Merge into Silver with upsert pattern.

### Step 3: Gold Layer - Business Aggregations
Aggregate Silver data by business dimensions and time grain. Use partition-level overwrites for efficient updates.

### Step 4: Delta Live Tables (Optional)
Declarative pipeline with `@dlt.table` decorators and data quality expectations (`@dlt.expect_or_drop`).

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete Bronze/Silver/Gold pipeline code, Auto Loader config, DLT pipeline, and orchestration example.

## Output
- Bronze layer with raw data and ingestion metadata
- Silver layer with cleansed, deduplicated data
- Gold layer with business aggregations
- Delta Lake tables with ACID transactions

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Schema mismatch | Source schema changed | Use `mergeSchema` option |
| Duplicate records | Missing deduplication | Add merge logic with primary keys |
| Null values | Data quality issues | Add expectations/filters in Silver |
| Memory errors | Large aggregations | Increase cluster size or partition data |

## Examples

### Quick Pipeline Run
```python
# Full medallion pipeline
bronze.ingest_to_bronze(spark, "/mnt/landing/orders/", "catalog.bronze.orders")
silver.transform_to_silver(spark, "catalog.bronze.orders", "catalog.silver.orders", primary_keys=["order_id"])
gold.aggregate_to_gold(spark, "catalog.silver.orders", "catalog.gold.metrics", group_by_columns=["region"])
```

## Resources
- [Delta Lake Guide](https://docs.databricks.com/delta/index.html)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [Delta Live Tables](https://docs.databricks.com/delta-live-tables/index.html)
- [Auto Loader](https://docs.databricks.com/ingestion/auto-loader/index.html)

## Next Steps
For ML workflows, see `databricks-core-workflow-b`.
