# Databricks Core Workflow A - Implementation Details

## Bronze Layer - Raw Ingestion

```python
# src/pipelines/bronze.py
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import current_timestamp, input_file_name, lit

def ingest_to_bronze(spark, source_path, target_table, source_format="json", schema=None):
    reader = spark.read.format(source_format)
    if schema:
        reader = reader.schema(schema)
    df = reader.load(source_path)
    df_with_metadata = (
        df.withColumn("_ingested_at", current_timestamp())
        .withColumn("_source_file", input_file_name())
        .withColumn("_source_format", lit(source_format))
    )
    df_with_metadata.write.format("delta").mode("append") \
        .option("mergeSchema", "true").saveAsTable(target_table)
    return df_with_metadata

# Auto Loader for streaming
def stream_to_bronze(spark, source_path, target_table, checkpoint_path, schema_location):
    (spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", schema_location)
        .option("cloudFiles.inferColumnTypes", "true")
        .load(source_path)
        .withColumn("_ingested_at", current_timestamp())
        .writeStream.format("delta")
        .option("checkpointLocation", checkpoint_path)
        .option("mergeSchema", "true")
        .trigger(availableNow=True)
        .toTable(target_table))
```

## Silver Layer - Data Cleansing

```python
# src/pipelines/silver.py
from pyspark.sql.functions import col, trim, lower, to_timestamp, sha2, concat_ws
from delta.tables import DeltaTable

def transform_to_silver(spark, bronze_table, silver_table, primary_keys, watermark_column="_ingested_at"):
    bronze_df = spark.readStream.format("delta") \
        .option("readChangeFeed", "true").table(bronze_table)

    silver_df = (bronze_df
        .withColumn("name", trim(col("name")))
        .withColumn("email", lower(trim(col("email"))))
        .withColumn("created_at", to_timestamp(col("created_at")))
        .withColumn("email_hash", sha2(col("email"), 256))
        .filter(col("email").isNotNull())
        .filter(col("created_at").isNotNull())
        .withColumn("_row_key", sha2(concat_ws("||", *[col(k) for k in primary_keys]), 256))
    )

    if DeltaTable.isDeltaTable(spark, silver_table):
        delta_table = DeltaTable.forName(spark, silver_table)
        merge_condition = " AND ".join([f"target.{k} = source.{k}" for k in primary_keys])
        (delta_table.alias("target")
            .merge(silver_df.alias("source"), merge_condition)
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute())
    else:
        silver_df.write.format("delta").mode("overwrite").saveAsTable(silver_table)
```

## Gold Layer - Business Aggregations

```python
# src/pipelines/gold.py
from pyspark.sql.functions import col, count, sum, avg, date_trunc, current_timestamp

def aggregate_to_gold(spark, silver_table, gold_table, group_by_columns, aggregations, time_grain="day"):
    silver_df = spark.table(silver_table)
    agg_exprs = [f"{expr} as {output_col}" for output_col, expr in aggregations.items()]
    gold_df = (silver_df
        .withColumn("time_period", date_trunc(time_grain, col("created_at")))
        .groupBy(*group_by_columns, "time_period")
        .agg(*[eval(e) for e in agg_exprs])
        .withColumn("_aggregated_at", current_timestamp()))
    gold_df.write.format("delta").mode("overwrite") \
        .option("replaceWhere", f"time_period >= '{get_min_date()}'") \
        .saveAsTable(gold_table)
```

## Delta Live Tables Pipeline

```python
import dlt
from pyspark.sql.functions import *

@dlt.table(name="bronze_events", table_properties={"quality": "bronze"})
def bronze_events():
    return (spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .load("/mnt/landing/events/")
        .withColumn("_ingested_at", current_timestamp()))

@dlt.table(name="silver_events", table_properties={"quality": "silver"})
@dlt.expect_or_drop("valid_email", "email IS NOT NULL")
@dlt.expect_or_drop("valid_amount", "amount > 0")
def silver_events():
    return (dlt.read_stream("bronze_events")
        .withColumn("email", lower(trim(col("email"))))
        .withColumn("event_time", to_timestamp(col("event_time"))))

@dlt.table(name="gold_daily_summary", table_properties={"quality": "gold"})
def gold_daily_summary():
    return (dlt.read("silver_events")
        .groupBy(date_trunc("day", col("event_time")).alias("date"))
        .agg(count("*").alias("total_events"),
             sum("amount").alias("total_revenue"),
             countDistinct("customer_id").alias("unique_customers")))
```

## Complete Pipeline Orchestration

```python
from src.pipelines import bronze, silver, gold

bronze.ingest_to_bronze(spark, "/mnt/landing/orders/", "catalog.bronze.orders")
silver.transform_to_silver(spark, "catalog.bronze.orders", "catalog.silver.orders", primary_keys=["order_id"])
gold.aggregate_to_gold(spark, "catalog.silver.orders", "catalog.gold.order_metrics",
    group_by_columns=["region"], time_grain="day")
```
