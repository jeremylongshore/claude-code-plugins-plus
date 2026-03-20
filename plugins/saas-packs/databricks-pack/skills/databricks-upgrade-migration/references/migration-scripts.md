# Migration Scripts

## Unity Catalog Migration

```python
def migrate_to_unity_catalog(spark, source_schema, target_catalog, target_schema, tables=None, method="sync"):
    """Migrate tables from hive_metastore to Unity Catalog."""
    results = []
    if tables is None:
        tables_df = spark.sql(f"SHOW TABLES IN {source_schema}")
        tables = [row.tableName for row in tables_df.collect()]

    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {target_catalog}.{target_schema}")

    for table in tables:
        source_table = f"{source_schema}.{table}"
        target_table = f"{target_catalog}.{target_schema}.{table}"
        try:
            if method == "sync":
                spark.sql(f"CREATE TABLE IF NOT EXISTS {target_table} USING DELTA LOCATION (SELECT location FROM (DESCRIBE DETAIL {source_table}))")
            else:
                spark.sql(f"CREATE TABLE {target_table} DEEP CLONE {source_table}")
            results.append({"table": table, "status": "SUCCESS", "method": method})
        except Exception as e:
            results.append({"table": table, "status": "FAILED", "error": str(e)})
    return results
```

## API Migration (v2.0 to v2.1)

```python
# Common v2.0 → v2.1 changes
ENDPOINT_RENAMES = {
    "/api/2.0/clusters/list": "/api/2.1/clusters/list",
    "/api/2.0/jobs/list": "/api/2.1/jobs/list",
    "/api/2.0/jobs/runs/list": "/api/2.1/jobs/runs/list",
}

def migrate_api_calls(codebase_path: str):
    """Find and update deprecated API endpoints."""
    import os, re
    for root, _, files in os.walk(codebase_path):
        for f in files:
            if f.endswith((".py", ".ts", ".js")):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                for old, new in ENDPOINT_RENAMES.items():
                    content = content.replace(old, new)
                with open(path, "w") as fh:
                    fh.write(content)
```

## Delta Protocol Upgrade

```python
def upgrade_delta_protocol(spark, catalog, schema, min_reader=2, min_writer=5):
    """Upgrade Delta Lake protocol for tables."""
    results = []
    tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect()
    for table_row in tables:
        table = f"{catalog}.{schema}.{table_row.tableName}"
        try:
            detail = spark.sql(f"DESCRIBE DETAIL {table}").first()
            if detail.minReaderVersion < min_reader or detail.minWriterVersion < min_writer:
                spark.sql(f"ALTER TABLE {table} SET TBLPROPERTIES ('delta.minReaderVersion' = '{min_reader}', 'delta.minWriterVersion' = '{min_writer}')")
                results.append({"table": table, "status": "UPGRADED", "from": f"r{detail.minReaderVersion}/w{detail.minWriterVersion}", "to": f"r{min_reader}/w{min_writer}"})
            else:
                results.append({"table": table, "status": "ALREADY_CURRENT"})
        except Exception as e:
            results.append({"table": table, "status": "FAILED", "error": str(e)})
    return results
```

## Complete Migration Runbook

```bash
#!/bin/bash
# migrate_workspace.sh

# 1. Pre-migration backup
echo "Creating backup..."
databricks workspace export-dir /production /tmp/backup --overwrite

# 2. Test migration on staging
echo "Testing on staging..."
databricks bundle deploy -t staging
databricks bundle run -t staging migration-test-job

# 3. Run migration
echo "Running migration..."
python scripts/migrate_to_unity_catalog.py

# 4. Validate migration
echo "Validating..."
databricks bundle run -t staging validation-job

# 5. Update jobs to use new tables
echo "Updating jobs..."
databricks bundle deploy -t prod

echo "Migration complete!"
```
