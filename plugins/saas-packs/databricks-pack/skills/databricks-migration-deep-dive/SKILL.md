---
name: databricks-migration-deep-dive
description: |
  Execute comprehensive platform migrations to Databricks from legacy systems.
  Use when migrating from on-premises Hadoop, other cloud platforms,
  or legacy data warehouses to Databricks.
  Trigger with phrases like "migrate to databricks", "hadoop migration",
  "snowflake to databricks", "legacy migration", "data warehouse migration".
allowed-tools: Read, Write, Edit, Bash(databricks:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, migration]

---
# Databricks Migration Deep Dive

## Overview
Comprehensive migration strategies for moving to Databricks from Hadoop, Snowflake, Redshift, Synapse, or legacy data warehouses. Covers discovery and assessment, schema conversion, data migration with batching and validation, ETL/pipeline conversion, and cutover planning with rollback procedures.

## Prerequisites
- Access to source and target systems
- Databricks workspace with Unity Catalog enabled
- Understanding of current data architecture and dependencies
- Stakeholder alignment on migration timeline

## Migration Patterns

| Source | Pattern | Complexity | Timeline |
|--------|---------|------------|----------|
| Hive Metastore (same workspace) | SYNC / CTAS / DEEP CLONE | Low | Days |
| On-prem Hadoop/HDFS | Lift-and-shift to cloud storage + UC | High | 6-12 months |
| Snowflake | Parallel run + cutover | Medium | 3-6 months |
| AWS Redshift | Unload to S3 + Auto Loader | Medium | 3-6 months |
| Legacy DW (Oracle/Teradata) | Full rebuild with JDBC extraction | High | 12-18 months |

## Instructions

### Step 1: Discovery and Assessment
Inventory all source tables with metadata for migration planning.

```python
from pyspark.sql import SparkSession
from dataclasses import dataclass

spark = SparkSession.builder.getOrCreate()

@dataclass
class TableInventory:
    database: str
    table: str
    table_type: str
    format: str
    row_count: int
    size_mb: float
    columns: int
    partitions: list[str]

def assess_hive_metastore() -> list[TableInventory]:
    """Inventory all Hive Metastore tables for migration planning."""
    inventory = []
    databases = [r.databaseName for r in spark.sql("SHOW DATABASES").collect()]

    for db in databases:
        tables = spark.sql(f"SHOW TABLES IN hive_metastore.{db}").collect()
        for t in tables:
            table_name = f"hive_metastore.{db}.{t.tableName}"
            try:
                detail = spark.sql(f"DESCRIBE DETAIL {table_name}").first()
                schema = spark.table(table_name).schema

                inventory.append(TableInventory(
                    database=db,
                    table=t.tableName,
                    table_type=detail.format or "unknown",
                    format=detail.format or "unknown",
                    row_count=spark.table(table_name).count(),
                    size_mb=detail.sizeInBytes / 1048576 if detail.sizeInBytes else 0,
                    columns=len(schema),
                    partitions=detail.partitionColumns or [],
                ))
            except Exception as e:
                print(f"  Skipping {table_name}: {e}")

    return inventory

# Generate migration plan
tables = assess_hive_metastore()
tables.sort(key=lambda t: t.size_mb, reverse=True)

print(f"\nTotal tables: {len(tables)}")
print(f"Total size: {sum(t.size_mb for t in tables):.0f} MB")
print(f"\nTop 10 by size:")
for t in tables[:10]:
    print(f"  {t.database}.{t.table}: {t.size_mb:.0f}MB, {t.row_count:,} rows, {t.format}")
```

### Step 2: Schema Migration
```python
# Schema conversion for common type mismatches
TYPE_MAP = {
    # Hadoop/Hive types → Delta Lake/Spark types
    "CHAR": "STRING",
    "VARCHAR": "STRING",
    "TINYINT": "INT",
    "SMALLINT": "INT",
    "BINARY": "BINARY",
    # Snowflake types
    "NUMBER": "DECIMAL",
    "VARIANT": "STRING",  # Store as JSON string, parse in Silver
    "TIMESTAMP_NTZ": "TIMESTAMP",
    "TIMESTAMP_TZ": "TIMESTAMP",
    # Redshift types
    "SUPER": "STRING",
    "TIMETZ": "TIMESTAMP",
}

def generate_create_table(source_table: str, target_table: str) -> str:
    """Generate CREATE TABLE DDL with type conversions."""
    schema = spark.table(source_table).schema
    cols = []
    for field in schema:
        dtype = TYPE_MAP.get(str(field.dataType).upper(), str(field.dataType))
        cols.append(f"  {field.name} {dtype}")

    return f"""CREATE TABLE IF NOT EXISTS {target_table} (
{',\n'.join(cols)}
) USING DELTA
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);"""
```

### Step 3: Data Migration with Validation
```python
def migrate_table(
    source_table: str,
    target_table: str,
    method: str = "ctas",
    batch_size_mb: int = 500,
) -> dict:
    """Migrate a table with validation."""
    result = {"source": source_table, "target": target_table, "method": method}

    if method == "sync":
        # In-place metadata migration (fastest, no data copy)
        spark.sql(f"SYNC TABLE {target_table} FROM {source_table}")

    elif method == "deep_clone":
        # Delta-to-Delta with history preservation
        spark.sql(f"CREATE TABLE {target_table} DEEP CLONE {source_table}")

    elif method == "ctas":
        # Full data copy (works with any source format)
        source_size_mb = spark.sql(
            f"DESCRIBE DETAIL {source_table}"
        ).first().sizeInBytes / 1048576

        if source_size_mb > batch_size_mb:
            # Batch large tables by partition or row number
            spark.sql(f"""
                CREATE TABLE {target_table}
                USING DELTA
                AS SELECT * FROM {source_table}
            """)
        else:
            spark.sql(f"CREATE TABLE {target_table} AS SELECT * FROM {source_table}")

    elif method == "jdbc":
        # External database migration
        df = (spark.read
            .format("jdbc")
            .option("url", f"jdbc:postgresql://host:5432/db")
            .option("dbtable", source_table)
            .option("fetchsize", "10000")
            .load())
        df.write.format("delta").saveAsTable(target_table)

    # Validate
    src_count = spark.table(source_table).count()
    tgt_count = spark.table(target_table).count()
    result["source_rows"] = src_count
    result["target_rows"] = tgt_count
    result["match"] = src_count == tgt_count
    result["status"] = "OK" if result["match"] else "MISMATCH"

    return result

# Migrate with validation
result = migrate_table(
    "hive_metastore.legacy.customers",
    "analytics.migrated.customers",
    method="ctas",
)
print(f"{result['source']} -> {result['target']}: "
      f"{result['source_rows']:,} rows [{result['status']}]")
```

### Step 4: Snowflake / Redshift Migration
```python
# Snowflake: Use Lakehouse Federation or Unload + Auto Loader
# Option A: Lakehouse Federation (query in place, no copy)
spark.sql("""
    CREATE FOREIGN CATALOG snowflake_catalog
    USING CONNECTION snowflake_conn
    OPTIONS (database 'PROD_DB')
""")
# Query directly: SELECT * FROM snowflake_catalog.schema.table

# Option B: Unload to S3 + ingest
# In Snowflake:
# COPY INTO @my_s3_stage/export/customers/
# FROM PROD_DB.PUBLIC.CUSTOMERS
# FILE_FORMAT = (TYPE = PARQUET);

# In Databricks:
df = spark.read.parquet("s3://migration-bucket/export/customers/")
df.write.format("delta").saveAsTable("analytics.migrated.customers")
```

```python
# Redshift: Unload to S3 + Auto Loader
# In Redshift:
# UNLOAD ('SELECT * FROM prod.customers')
# TO 's3://migration-bucket/redshift/customers/'
# FORMAT PARQUET;

# In Databricks:
(spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", "/checkpoints/migration/schema")
    .load("s3://migration-bucket/redshift/customers/")
    .writeStream
    .format("delta")
    .option("checkpointLocation", "/checkpoints/migration/data")
    .toTable("analytics.migrated.customers"))
```

### Step 5: ETL Pipeline Conversion
```python
# Convert Oozie/Airflow jobs to Databricks Asset Bundles
# Before (Oozie/spark-submit):
#   spark-submit --class com.company.ETL --master yarn app.jar
#   hive -e "INSERT OVERWRITE TABLE target SELECT * FROM staging"

# After (Asset Bundle):
# databricks.yml resources:
"""
resources:
  jobs:
    migrated_etl:
      name: migrated-etl
      tasks:
        - task_key: extract
          notebook_task:
            notebook_path: src/extract.py
        - task_key: transform
          depends_on: [{task_key: extract}]
          notebook_task:
            notebook_path: src/transform.py
"""

# Convert HiveQL to Spark SQL
# Before: INSERT OVERWRITE TABLE target SELECT ...
# After:  (Use MERGE for upserts or write.mode("overwrite").saveAsTable)
```

### Step 6: Cutover Planning
```python
cutover_steps = [
    {"step": 1, "action": "Final validation", "rollback": "No action needed"},
    {"step": 2, "action": "Disable source pipelines", "rollback": "Re-enable source"},
    {"step": 3, "action": "Final data sync", "rollback": "Data already in place"},
    {"step": 4, "action": "Switch apps to Databricks endpoints", "rollback": "Revert app config"},
    {"step": 5, "action": "Enable Databricks pipelines", "rollback": "Disable and restore source"},
    {"step": 6, "action": "Monitor for 24 hours", "rollback": "Full rollback if issues"},
]

# Validation query to run at each step
validation_query = """
SELECT 'source' AS system, COUNT(*) AS rows FROM source_table
UNION ALL
SELECT 'target', COUNT(*) FROM target_table
"""
```

## Output
- Migration assessment with table inventory (sizes, formats, dependencies)
- Schema conversion with type mapping and DDL generation
- Data migration with row-count validation per table
- ETL pipeline conversion from Oozie/Airflow to Asset Bundles
- Cutover plan with step-by-step rollback procedures

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Schema incompatibility | Unsupported types (VARIANT, SUPER) | Convert to STRING, parse in Silver layer |
| Row count mismatch | Truncation or filter during migration | Check for NULLs, encoding issues, or WHERE clauses |
| JDBC timeout | Large table extraction | Use `fetchsize`, partition reads, or incremental export |
| `SYNC` fails | External table storage inaccessible | Verify cloud storage credentials and network access |
| Pipeline dependency failure | Wrong migration order | Build dependency graph, migrate leaf tables first |

## Examples

### Quick Validation After Migration
```sql
-- Compare source and target counts
SELECT 'hive_metastore' AS source, COUNT(*) AS rows
FROM hive_metastore.legacy.customers
UNION ALL
SELECT 'unity_catalog', COUNT(*)
FROM analytics.migrated.customers;
```

### Bulk Migration Script
```python
migration_plan = [
    ("hive_metastore.legacy.customers", "analytics.migrated.customers", "ctas"),
    ("hive_metastore.legacy.orders", "analytics.migrated.orders", "deep_clone"),
    ("hive_metastore.legacy.products", "analytics.migrated.products", "sync"),
]

results = []
for src, tgt, method in migration_plan:
    print(f"Migrating {src} -> {tgt} ({method})...")
    result = migrate_table(src, tgt, method)
    results.append(result)
    print(f"  {result['status']}: {result['source_rows']:,} -> {result['target_rows']:,}")

failed = [r for r in results if r["status"] != "OK"]
print(f"\nCompleted: {len(results) - len(failed)}/{len(results)} OK")
```

## Resources
- [Unity Catalog Migration](https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started)
- [Lakehouse Federation](https://docs.databricks.com/aws/en/query-federation/)
- [Auto Loader](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/)
- [Delta Lake Migration](https://docs.databricks.com/aws/en/delta/tutorial)
