# Databricks Migration Deep Dive - Implementation Details

## Discovery and Assessment

```python
@dataclass
class SourceTableInfo:
    database: str; schema: str; table: str; row_count: int; size_gb: float
    column_count: int; partition_columns: list; dependencies: list
    access_frequency: str; data_classification: str

def assess_hadoop_cluster(spark, hive_metastore):
    tables = []
    databases = spark.sql("SHOW DATABASES").collect()
    for db_row in databases:
        db = db_row.databaseName
        if db in ['default', 'sys']: continue
        spark.sql(f"USE {db}")
        for table_row in spark.sql("SHOW TABLES").collect():
            # Extract partition info, row count, size from DESCRIBE EXTENDED
            tables.append(SourceTableInfo(...))
    return tables

def generate_migration_plan(tables):
    plan_data = []
    for table in tables:
        complexity = sum([table.size_gb > 100, len(table.partition_columns) > 2,
                          len(table.dependencies) > 5, (table.data_classification == 'pii') * 2])
        priority = (3 if table.access_frequency == 'high' else 1) + (2 if table.data_classification == 'pii' else 0)
        plan_data.append({
            'source_table': f"{table.database}.{table.table}",
            'complexity_score': complexity, 'priority_score': priority,
            'migration_wave': 1 if priority > 3 else (2 if priority > 1 else 3),
        })
    return pd.DataFrame(plan_data).sort_values(['migration_wave', 'priority_score'], ascending=[True, False])
```

## Schema Migration

```python
def convert_hive_to_delta_schema(spark, hive_table):
    type_conversions = {
        'decimal(38,0)': DecimalType(38, 10), 'char': StringType(),
        'varchar': StringType(), 'tinyint': IntegerType(),
    }
    hive_schema = spark.table(hive_table).schema
    new_fields = []
    for field in hive_schema.fields:
        new_type = field.dataType
        for pattern, replacement in type_conversions.items():
            if pattern in str(field.dataType).lower():
                new_type = replacement; break
        new_fields.append(StructField(field.name, new_type, field.nullable, field.metadata))
    return StructType(new_fields)

def migrate_table_schema(spark, source_table, target_table, catalog="migrated"):
    target_schema = convert_hive_to_delta_schema(spark, source_table)
    schema_ddl = ", ".join([f"`{f.name}` {f.dataType.simpleString()}" for f in target_schema.fields])
    spark.sql(f"""CREATE TABLE IF NOT EXISTS {catalog}.{target_table} ({schema_ddl})
        USING DELTA TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true', 'delta.autoOptimize.autoCompact' = 'true')""")
```

## Data Migration with Batching

```python
class DataMigrator:
    def migrate_table(self, source_table, target_table, batch_size=1000000, partition_columns=None):
        source_df = self.spark.table(source_table)
        if partition_columns:
            partitions = source_df.select(partition_columns).distinct().collect()
            for partition_row in partitions:
                conditions = [f"{col} = '{partition_row[col]}'" for col in partition_columns]
                batch_df = source_df.filter(" AND ".join(conditions))
                self._write_batch(batch_df, target_table, partition_columns)
        else:
            self._write_batch(source_df, target_table, partition_columns)

    def validate_migration(self, source_table, target_table):
        source_df = self.spark.table(source_table)
        target_df = self.spark.table(f"{self.target_catalog}.{target_table}")
        return {
            'count_match': source_df.count() == target_df.count(),
            'schema_match': set(source_df.columns) == set(target_df.columns),
        }
```

## ETL/Pipeline Migration

```python
def convert_spark_job_to_databricks(source_code, source_type="spark-submit"):
    replacements = {
        'SparkSession.builder.master("yarn")': 'SparkSession.builder',
        '.master("local[*]")': '',
        'hdfs://namenode:8020/': '/mnt/data/',
        's3a://': 's3://',
        '.enableHiveSupport()': '',
    }
    converted = source_code
    for old, new in replacements.items():
        converted = converted.replace(old, new)
    return converted
```

## Cutover Planning

```python
@dataclass
class CutoverStep:
    order: int; name: str; duration_minutes: int; owner: str
    rollback_procedure: str; verification: str

def generate_cutover_plan(migration_wave, tables, cutover_date):
    steps = [
        CutoverStep(1, "Pre-cutover validation", 60, "Data Engineer", "N/A", "Run validation queries"),
        CutoverStep(2, "Disable source pipelines", 15, "Platform Admin", "Re-enable pipelines", "No new data"),
        CutoverStep(3, "Final incremental sync", 120, "Data Engineer", "N/A", "Row counts match"),
        CutoverStep(4, "Enable Databricks pipelines", 30, "Data Engineer", "Disable + re-enable source", "Jobs running"),
        CutoverStep(5, "Update downstream apps", 60, "App Team", "Revert connection strings", "Apps reading Databricks"),
        CutoverStep(6, "Monitor and validate", 240, "Data Engineer", "Full rollback", "Metrics in range"),
    ]
    return steps
```

## Quick Migration Validation
```sql
SELECT 'source' as system, COUNT(*) as row_count FROM hive_metastore.db.table
UNION ALL
SELECT 'target' as system, COUNT(*) as row_count FROM migrated.db.table;
```
