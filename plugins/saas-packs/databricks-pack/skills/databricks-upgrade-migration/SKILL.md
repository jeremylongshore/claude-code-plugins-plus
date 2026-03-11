---
name: databricks-upgrade-migration
description: |
  Upgrade Databricks runtime versions and migrate between features.
  Use when upgrading DBR versions, migrating to Unity Catalog,
  or updating deprecated APIs and features.
  Trigger with phrases like "databricks upgrade", "DBR upgrade",
  "databricks migration", "unity catalog migration", "hive to unity".
allowed-tools: Read, Write, Edit, Bash(databricks:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Upgrade & Migration

## Overview
Upgrade Databricks Runtime versions and migrate between platform features.

## Prerequisites
- Admin access to workspace
- Test environment for validation
- Understanding of current workload dependencies

## Instructions

### Step 1: Runtime Version Upgrade

#### Version Compatibility Matrix
| Current DBR | Target DBR | Breaking Changes | Migration Effort |
|-------------|------------|------------------|------------------|
| 12.x | 13.x | Spark 3.4 changes | Low |
| 13.x | 14.x | Python 3.10 default | Medium |
| 14.x | 15.x | Unity Catalog required | High |

#### Upgrade Process
```python
# scripts/upgrade_clusters.py
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import ClusterSpec

def upgrade_cluster_dbr(
    w: WorkspaceClient,
    cluster_id: str,
    target_version: str = "14.3.x-scala2.12",
    dry_run: bool = True,
) -> dict:
    """
    Upgrade cluster to new DBR version.

    Args:
        w: WorkspaceClient
        cluster_id: Cluster to upgrade
        target_version: Target Spark version
        dry_run: If True, only validate without applying

    Returns:
        Upgrade plan or result
    """
    cluster = w.clusters.get(cluster_id)

    upgrade_plan = {
        "cluster_id": cluster_id,
        "cluster_name": cluster.cluster_name,
        "current_version": cluster.spark_version,
        "target_version": target_version,
        "changes": [],
    }

    # Check for deprecated configs
    if cluster.spark_conf:
        deprecated_configs = [
            "spark.databricks.delta.preview.enabled",
            "spark.sql.legacy.createHiveTableByDefault",
        ]
        for config in deprecated_configs:
            if config in cluster.spark_conf:
                upgrade_plan["changes"].append({
                    "type": "remove_config",
                    "config": config,
                    "reason": "Deprecated in target version",
                })

    # Check for library updates
    if cluster.cluster_libraries:
        for lib in cluster.cluster_libraries:
            # Check for incompatible versions
            pass

    if not dry_run:
        # Apply upgrade
        w.clusters.edit(
            cluster_id=cluster_id,
            spark_version=target_version,
            # Remove deprecated configs
            spark_conf={
                k: v for k, v in (cluster.spark_conf or {}).items()
                if k not in deprecated_configs
            }
        )
        upgrade_plan["status"] = "APPLIED"
    else:
        upgrade_plan["status"] = "DRY_RUN"

    return upgrade_plan
```

### Step 2: Unity Catalog Migration

#### Migration Steps
```sql
-- Step 1: Create Unity Catalog objects
CREATE CATALOG IF NOT EXISTS main;
CREATE SCHEMA IF NOT EXISTS main.migrated;

-- Step 2: Migrate tables from Hive Metastore
-- Option A: SYNC (keeps data in place)
SYNC SCHEMA main.migrated
FROM hive_metastore.old_schema;

-- Option B: CTAS (copies data)
CREATE TABLE main.migrated.customers AS
SELECT * FROM hive_metastore.old_schema.customers;

-- Step 3: Migrate views
CREATE VIEW main.migrated.customer_summary AS
SELECT * FROM hive_metastore.old_schema.customer_summary;

-- Step 4: Set up permissions
GRANT USAGE ON CATALOG main TO `data-team`;
GRANT SELECT ON SCHEMA main.migrated TO `data-team`;

-- Step 5: Verify migration
SHOW TABLES IN main.migrated;
DESCRIBE TABLE EXTENDED main.migrated.customers;
```

#### Python Migration Script
```python
# scripts/migrate_to_unity_catalog.py
from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession

def migrate_schema_to_unity(
    spark: SparkSession,
    source_schema: str,
    target_catalog: str,
    target_schema: str,
    tables: list[str] = None,
    method: str = "sync",  # "sync" or "copy"
) -> list[dict]:
    """
    Migrate Hive Metastore schema to Unity Catalog.

    Args:
        spark: SparkSession
        source_schema: Hive metastore schema (e.g., "hive_metastore.old_db")
        target_catalog: Unity Catalog catalog name
        target_schema: Target schema name
        tables: Specific tables to migrate (None = all)
        method: "sync" (in-place) or "copy" (duplicate data)

    Returns:
        List of migration results
    """
    results = []

    # Get tables to migrate
    if tables is None:
        tables_df = spark.sql(f"SHOW TABLES IN {source_schema}")
        tables = [row.tableName for row in tables_df.collect()]

    # Create target schema
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {target_catalog}.{target_schema}")

    for table in tables:
        source_table = f"{source_schema}.{table}"
        target_table = f"{target_catalog}.{target_schema}.{table}"

        try:
            if method == "sync":
                # SYNC keeps data in original location
                spark.sql(f"""
                    CREATE TABLE IF NOT EXISTS {target_table}
                    USING DELTA
                    LOCATION (SELECT location FROM
                        (DESCRIBE DETAIL {source_table}))
                """)
            else:
                # Copy creates new data
                spark.sql(f"""
                    CREATE TABLE {target_table}
                    DEEP CLONE {source_table}
                """)

            results.append({
                "table": table,
                "status": "SUCCESS",
                "method": method,
            })

        except Exception as e:
            results.append({
                "table": table,
                "status": "FAILED",
                "error": str(e),
            })

    return results
```

### Step 3: API Migration (v2.0 to v2.1)

```python
# Migrate deprecated API calls
from databricks.sdk import WorkspaceClient

def migrate_api_calls(w: WorkspaceClient):
    """Update deprecated API usage patterns."""

    # Old: clusters/create with deprecated params
    # New: Use instance pools and policies

    # Old: jobs/create with existing_cluster_id
    # New: Use job_cluster_key for better isolation

    # Old: dbfs/put for large files
    # New: Use Volumes or cloud storage

    # Old: Workspace API for notebooks
    # New: Use Repos API for version control

    pass
```

### Step 4: Delta Lake Upgrade

```python
# Upgrade Delta Lake protocol version
def upgrade_delta_tables(
    spark: SparkSession,
    catalog: str,
    schema: str,
    min_reader: int = 3,
    min_writer: int = 7,
) -> list[dict]:
    """
    Upgrade Delta Lake protocol for tables.

    Protocol version benefits:
    - Reader 2+: Column mapping
    - Reader 3+: Deletion vectors
    - Writer 5+: Change Data Feed
    - Writer 7+: Deletion vectors, liquid clustering
    """
    results = []

    tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}").collect()

    for table_row in tables:
        table = f"{catalog}.{schema}.{table_row.tableName}"

        try:
            # Check current protocol
            detail = spark.sql(f"DESCRIBE DETAIL {table}").first()
            current_reader = detail.minReaderVersion
            current_writer = detail.minWriterVersion

            if current_reader < min_reader or current_writer < min_writer:
                # Upgrade protocol
                spark.sql(f"""
                    ALTER TABLE {table}
                    SET TBLPROPERTIES (
                        'delta.minReaderVersion' = '{min_reader}',
                        'delta.minWriterVersion' = '{min_writer}'
                    )
                """)

                results.append({
                    "table": table,
                    "status": "UPGRADED",
                    "from": f"r{current_reader}/w{current_writer}",
                    "to": f"r{min_reader}/w{min_writer}",
                })
            else:
                results.append({
                    "table": table,
                    "status": "ALREADY_CURRENT",
                })

        except Exception as e:
            results.append({
                "table": table,
                "status": "FAILED",
                "error": str(e),
            })

    return results
```

## Output
- Upgraded DBR version
- Unity Catalog migration complete
- Updated API calls
- Delta Lake protocol upgraded

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Incompatible library | Version mismatch | Update library version |
| Permission error | Missing grants | Add Unity Catalog grants |
| Table sync failed | Location access | Check storage permissions |
| Protocol downgrade | Reader/writer too high | Clone to new table |

## Examples

### Complete Migration Runbook
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

## Resources
- [Databricks Runtime Release Notes](https://docs.databricks.com/release-notes/runtime/releases.html)
- [Unity Catalog Migration](https://docs.databricks.com/data-governance/unity-catalog/migrate.html)
- [Delta Lake Protocol Versions](https://docs.databricks.com/delta/versioning.html)

## Next Steps
For CI/CD integration, see `databricks-ci-integration`.