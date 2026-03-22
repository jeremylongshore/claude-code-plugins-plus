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
tags: [saas, databricks, workflow, data-pipeline, etl]

---
# Databricks Core Workflow A: Delta Lake ETL

## Overview
Build production Delta Lake ETL pipelines using the medallion architecture (Bronze > Silver > Gold). Uses Auto Loader (`cloudFiles`) for incremental ingestion, `MERGE INTO` for upserts, and Delta Live Tables for declarative pipelines.

## Prerequisites
- Completed `databricks-install-auth` setup
- Unity Catalog enabled with catalogs/schemas created
- Access to cloud storage for raw data (S3, ADLS, GCS)

## Architecture
```
Raw Sources (S3/ADLS/GCS)
    │  Auto Loader (cloudFiles)
    ▼
Bronze (raw + metadata)
    │  Cleanse, deduplicate, type-cast
    ▼
Silver (conformed)
    │  Aggregate, join, feature engineer
    ▼
Gold (analytics-ready)
```

## Instructions

### Step 1: Bronze Layer — Raw Ingestion with Auto Loader
Auto Loader (`cloudFiles` format) incrementally processes new files as they arrive. It handles schema inference, evolution, and scales to millions of files.

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, input_file_name, lit

spark = SparkSession.builder.getOrCreate()

# Streaming ingestion with Auto Loader
bronze_stream = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", "/checkpoints/bronze/orders/schema")
    .option("cloudFiles.inferColumnTypes", "true")
    .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
    .load("s3://data-lake/raw/orders/")
)

# Add ingestion metadata
bronze_with_meta = (
    bronze_stream
    .withColumn("_ingested_at", current_timestamp())
    .withColumn("_source_file", input_file_name())
    .withColumn("_source_system", lit("orders-api"))
)

# Write to bronze Delta table
(bronze_with_meta.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/bronze/orders/data")
    .option("mergeSchema", "true")
    .toTable("prod_catalog.bronze.raw_orders"))
```

### Step 2: Silver Layer — Cleansing and Deduplication
Read from Bronze, apply business logic, and MERGE INTO Silver with upsert semantics.

```python
from pyspark.sql.functions import col, trim, lower, to_timestamp, sha2, concat_ws
from delta.tables import DeltaTable

# Read new records from bronze (batch mode for scheduled jobs)
bronze_df = spark.table("prod_catalog.bronze.raw_orders")

# Apply transformations
silver_df = (
    bronze_df
    .withColumn("order_id", col("order_id").cast("string"))
    .withColumn("customer_email", lower(trim(col("customer_email"))))
    .withColumn("order_date", to_timestamp(col("order_date"), "yyyy-MM-dd'T'HH:mm:ss"))
    .withColumn("amount", col("amount").cast("decimal(12,2)"))
    .withColumn("email_hash", sha2(col("customer_email"), 256))
    .filter(col("order_id").isNotNull())
    .dropDuplicates(["order_id"])
)

# Upsert into silver with MERGE
if spark.catalog.tableExists("prod_catalog.silver.orders"):
    target = DeltaTable.forName(spark, "prod_catalog.silver.orders")
    (target.alias("t")
        .merge(silver_df.alias("s"), "t.order_id = s.order_id")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute())
else:
    silver_df.write.format("delta").saveAsTable("prod_catalog.silver.orders")
```

### Step 3: Gold Layer — Business Aggregations
Aggregate Silver data into analytics-ready tables. Use partition-level overwrites for efficient updates.

```python
from pyspark.sql.functions import sum as _sum, count, avg, date_trunc

# Daily order metrics
gold_metrics = (
    spark.table("prod_catalog.silver.orders")
    .withColumn("order_day", date_trunc("day", col("order_date")))
    .groupBy("order_day", "region")
    .agg(
        count("order_id").alias("total_orders"),
        _sum("amount").alias("total_revenue"),
        avg("amount").alias("avg_order_value"),
    )
)

# Overwrite only changed partitions
(gold_metrics.write
    .format("delta")
    .mode("overwrite")
    .option("replaceWhere", f"order_day >= '{target_date}'")
    .saveAsTable("prod_catalog.gold.daily_order_metrics"))
```

### Step 4: Delta Table Maintenance
```sql
-- Compact small files (bin-packing)
OPTIMIZE prod_catalog.silver.orders;

-- Z-order for query performance on frequently filtered columns
OPTIMIZE prod_catalog.silver.orders ZORDER BY (order_date, region);

-- Or use Liquid Clustering (DBR 13.3+) — replaces partitioning + Z-order
ALTER TABLE prod_catalog.silver.orders CLUSTER BY (order_date, region);
OPTIMIZE prod_catalog.silver.orders;

-- Clean up old file versions (default: 7 days)
VACUUM prod_catalog.silver.orders RETAIN 168 HOURS;

-- Compute statistics for query optimizer
ANALYZE TABLE prod_catalog.silver.orders COMPUTE STATISTICS;
```

### Step 5: Delta Live Tables (Declarative Pipeline)
DLT manages orchestration, data quality, lineage, and error handling automatically.

```python
import dlt
from pyspark.sql.functions import col, current_timestamp

@dlt.table(
    comment="Raw orders from Auto Loader",
    table_properties={"quality": "bronze"},
)
def bronze_orders():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .load("s3://data-lake/raw/orders/")
        .withColumn("_ingested_at", current_timestamp())
    )

@dlt.table(comment="Cleansed orders")
@dlt.expect_or_drop("valid_order_id", "order_id IS NOT NULL")
@dlt.expect_or_drop("valid_amount", "amount > 0")
def silver_orders():
    return (
        dlt.read_stream("bronze_orders")
        .withColumn("amount", col("amount").cast("decimal(12,2)"))
        .dropDuplicates(["order_id"])
    )

@dlt.table(comment="Daily revenue metrics")
def gold_daily_revenue():
    return (
        dlt.read("silver_orders")
        .groupBy("region", "order_date")
        .agg({"amount": "sum", "order_id": "count"})
    )
```

### Step 6: Schedule the Pipeline
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import (
    CreateJob, Task, NotebookTask, JobCluster, CronSchedule,
)
from databricks.sdk.service.compute import ClusterSpec, AutoScale

w = WorkspaceClient()

job = w.jobs.create(
    name="daily-orders-etl",
    tasks=[
        Task(task_key="bronze", job_cluster_key="etl",
             notebook_task=NotebookTask(notebook_path="/Repos/team/pipelines/bronze")),
        Task(task_key="silver", job_cluster_key="etl",
             notebook_task=NotebookTask(notebook_path="/Repos/team/pipelines/silver"),
             depends_on=[{"task_key": "bronze"}]),
        Task(task_key="gold", job_cluster_key="etl",
             notebook_task=NotebookTask(notebook_path="/Repos/team/pipelines/gold"),
             depends_on=[{"task_key": "silver"}]),
    ],
    job_clusters=[JobCluster(
        job_cluster_key="etl",
        new_cluster=ClusterSpec(
            spark_version="14.3.x-scala2.12",
            node_type_id="i3.xlarge",
            autoscale=AutoScale(min_workers=1, max_workers=4),
        ),
    )],
    schedule=CronSchedule(quartz_cron_expression="0 0 6 * * ?", timezone_id="UTC"),
    max_concurrent_runs=1,
)
print(f"Created job: {job.job_id}")
```

## Output
- Bronze layer with raw data, Auto Loader schema evolution, and ingestion metadata
- Silver layer with cleansed, deduplicated, type-cast data via MERGE upserts
- Gold layer with business-ready aggregations
- Table maintenance schedule (OPTIMIZE, VACUUM, ANALYZE)
- Optional DLT pipeline with built-in data quality expectations

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `AnalysisException: mergeSchema` | Source schema changed | Auto Loader handles this; for batch add `.option("mergeSchema", "true")` |
| `ConcurrentAppendException` | Multiple jobs writing same table | Use MERGE with retry logic or serialize writes via `max_concurrent_runs=1` |
| `Null primary key` | Bad source data | Add `@dlt.expect_or_drop` or `.filter(col("pk").isNotNull())` |
| `java.lang.OutOfMemoryError` | Driver collecting large results | Never call `.collect()` on large data; use `.write` to keep distributed |
| `VACUUM below retention` | Retention < 7 days | Set `delta.deletedFileRetentionDuration = '168 hours'` minimum |

## Examples

### Quick Pipeline Validation
```sql
-- Verify row counts flow through medallion layers
SELECT 'bronze' AS layer, COUNT(*) AS rows FROM prod_catalog.bronze.raw_orders
UNION ALL SELECT 'silver', COUNT(*) FROM prod_catalog.silver.orders
UNION ALL SELECT 'gold', COUNT(*) FROM prod_catalog.gold.daily_order_metrics;
```

## Resources
- [Auto Loader](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/)
- [Delta Lake MERGE INTO](https://docs.databricks.com/aws/en/delta/merge)
- [OPTIMIZE](https://docs.databricks.com/aws/en/sql/language-manual/delta-optimize)
- [Delta Live Tables](https://docs.databricks.com/aws/en/delta-live-tables/)

## Next Steps
For ML workflows, see `databricks-core-workflow-b`.
