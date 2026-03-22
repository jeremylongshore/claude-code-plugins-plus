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
tags: [saas, databricks, migration]

---
# Databricks Upgrade & Migration

## Overview
Upgrade Databricks Runtime versions and migrate from Hive Metastore to Unity Catalog. Covers version compatibility, deprecated config removal, table migration via SYNC/CTAS, API endpoint updates, and Delta protocol upgrades.

## Prerequisites
- Admin access to workspace
- Test environment (dev/staging) for validation before prod
- Inventory of current workloads and dependencies

## Instructions

### Step 1: Runtime Version Upgrade

#### Version Compatibility Matrix
| Current DBR | Target DBR | Key Changes | Effort |
|-------------|------------|-------------|--------|
| 12.x LTS | 13.3 LTS | Spark 3.4, Python 3.10 default | Low |
| 13.3 LTS | 14.3 LTS | Spark 3.5, improved AQE, Liquid Clustering GA | Medium |
| 14.x | 15.x LTS | Unity Catalog mandatory, legacy DBFS deprecated | High |

#### Automated Upgrade Script
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

def plan_cluster_upgrade(
    cluster_id: str,
    target_version: str = "14.3.x-scala2.12",
    dry_run: bool = True,
) -> dict:
    """Plan and optionally execute a DBR version upgrade."""
    cluster = w.clusters.get(cluster_id)
    plan = {
        "cluster_id": cluster_id,
        "cluster_name": cluster.cluster_name,
        "current_version": cluster.spark_version,
        "target_version": target_version,
        "removals": [],
        "warnings": [],
    }

    # Check for deprecated Spark configs
    deprecated = {
        "spark.databricks.delta.preview.enabled": "GA in 13.x+",
        "spark.sql.legacy.createHiveTableByDefault": "Removed in 14.x+",
        "spark.databricks.passthrough.enabled": "Removed in 15.x+",
        "spark.sql.legacy.allowNonEmptyLocationInCTAS": "Removed in 14.x+",
    }

    for key, reason in deprecated.items():
        if cluster.spark_conf and key in cluster.spark_conf:
            plan["removals"].append({"config": key, "reason": reason})

    # Check Python version compatibility
    if "13." in target_version or "14." in target_version:
        plan["warnings"].append("Python default changes to 3.10 — verify library compatibility")

    if not dry_run:
        clean_conf = {
            k: v for k, v in (cluster.spark_conf or {}).items()
            if k not in deprecated
        }
        w.clusters.edit(
            cluster_id=cluster_id,
            spark_version=target_version,
            cluster_name=cluster.cluster_name,
            spark_conf=clean_conf,
            node_type_id=cluster.node_type_id,
            num_workers=cluster.num_workers,
        )
        plan["status"] = "APPLIED"
    else:
        plan["status"] = "DRY_RUN"

    return plan

# Dry run first
for cluster in w.clusters.list():
    plan = plan_cluster_upgrade(cluster.cluster_id, dry_run=True)
    if plan["removals"] or plan["warnings"]:
        print(f"\n{plan['cluster_name']}:")
        for r in plan["removals"]:
            print(f"  REMOVE: {r['config']} ({r['reason']})")
        for w_ in plan["warnings"]:
            print(f"  WARN: {w_}")
```

### Step 2: Unity Catalog Migration (Hive Metastore)

#### Inventory Current Tables
```sql
-- List all Hive Metastore tables to migrate
SHOW DATABASES IN hive_metastore;
SHOW TABLES IN hive_metastore.my_database;

-- Get table sizes for migration planning
SELECT table_name, table_type,
       data_length / 1024 / 1024 AS size_mb
FROM hive_metastore.information_schema.tables
WHERE table_schema = 'my_database'
ORDER BY data_length DESC;
```

#### Migrate Tables
```sql
-- Create Unity Catalog destination
CREATE CATALOG IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS analytics.migrated;

-- Option A: SYNC (in-place — keeps data where it is, adds UC metadata)
-- Best for external tables already on cloud storage
SYNC SCHEMA analytics.migrated FROM hive_metastore.my_database;

-- Option B: CTAS (copies data — creates managed Delta tables)
-- Best for small-medium tables or format conversion
CREATE TABLE analytics.migrated.customers AS
SELECT * FROM hive_metastore.my_database.customers;

-- Option C: DEEP CLONE (best for Delta-to-Delta, preserves history)
CREATE TABLE analytics.migrated.orders
DEEP CLONE hive_metastore.my_database.orders;

-- Migrate views
CREATE VIEW analytics.migrated.customer_summary AS
SELECT * FROM analytics.migrated.customers
WHERE active = true;

-- Verify migration
SELECT 'source' AS system, COUNT(*) AS rows
FROM hive_metastore.my_database.customers
UNION ALL
SELECT 'target', COUNT(*)
FROM analytics.migrated.customers;

-- Grant access
GRANT USAGE ON CATALOG analytics TO `data-team`;
GRANT SELECT ON SCHEMA analytics.migrated TO `data-team`;
```

### Step 3: API Endpoint Migration
```python
# Jobs API 2.0 → 2.1 changes
# Old: POST /api/2.0/jobs/create with flat task definition
# New: POST /api/2.1/jobs/create with tasks[] array (multi-task)

# Old (single task):
old_config = {
    "name": "my-job",
    "existing_cluster_id": "abc-123",
    "notebook_task": {"notebook_path": "/path"}
}

# New (multi-task):
new_config = {
    "name": "my-job",
    "tasks": [{
        "task_key": "main",
        "existing_cluster_id": "abc-123",
        "notebook_task": {"notebook_path": "/path"}
    }]
}

# The Python SDK uses the latest API version automatically
from databricks.sdk.service.jobs import Task, NotebookTask
job = w.jobs.create(
    name="my-job",
    tasks=[Task(
        task_key="main",
        existing_cluster_id="abc-123",
        notebook_task=NotebookTask(notebook_path="/path"),
    )],
)
```

### Step 4: Delta Protocol Upgrade
```sql
-- Check current protocol version
DESCRIBE DETAIL analytics.silver.orders;
-- Look at: minReaderVersion, minWriterVersion

-- Upgrade to support Deletion Vectors (reader v3, writer v7)
ALTER TABLE analytics.silver.orders
SET TBLPROPERTIES (
    'delta.minReaderVersion' = '3',
    'delta.minWriterVersion' = '7',
    'delta.enableDeletionVectors' = 'true'
);

-- Enable Liquid Clustering (replaces partitioning + Z-order)
ALTER TABLE analytics.silver.orders CLUSTER BY (order_date, region);

-- WARNING: Protocol upgrades are irreversible.
-- If you need to downgrade, DEEP CLONE to a new table instead.
```

## Output
- DBR version upgraded with deprecated configs removed
- Hive Metastore tables migrated to Unity Catalog (SYNC/CTAS/DEEP CLONE)
- API calls updated to latest SDK patterns
- Delta protocol upgraded for Deletion Vectors and Liquid Clustering

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Library incompatible with new DBR | Python/Java version change | Pin library versions in `requirements.txt`, test in staging |
| `PERMISSION_DENIED` after migration | Missing Unity Catalog grants | Run `GRANT USAGE ON CATALOG`, `GRANT SELECT ON SCHEMA` |
| `SYNC` fails | Storage location inaccessible | Check cloud storage permissions and network config |
| Protocol downgrade error | Cannot lower protocol version | `DEEP CLONE` to a new table with lower protocol |
| `Table not found` after migration | Notebooks still reference `hive_metastore` | Update all references to `catalog.schema.table` format |

## Examples

### Quick Upgrade Check
```bash
# Current state
echo "CLI: $(databricks --version)"
echo "SDK: $(pip show databricks-sdk | grep Version)"
echo "Cluster DBR: $(databricks clusters get --cluster-id $CID | jq -r .spark_version)"

# Upgrade SDK
pip install --upgrade databricks-sdk
```

### Bulk Table Migration Script
```python
# Migrate all tables in a Hive Metastore database
source_db = "hive_metastore.legacy_data"
target_schema = "analytics.migrated"

tables = spark.sql(f"SHOW TABLES IN {source_db}").collect()
for t in tables:
    table_name = t.tableName
    print(f"Migrating {table_name}...")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {target_schema}.{table_name}
        AS SELECT * FROM {source_db}.{table_name}
    """)
    # Verify
    src_count = spark.table(f"{source_db}.{table_name}").count()
    tgt_count = spark.table(f"{target_schema}.{table_name}").count()
    status = "OK" if src_count == tgt_count else "MISMATCH"
    print(f"  {table_name}: {src_count} -> {tgt_count} [{status}]")
```

## Resources
- [Runtime Release Notes](https://docs.databricks.com/aws/en/release-notes/runtime/)
- [Unity Catalog Migration](https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started)
- [Delta Protocol Versions](https://docs.databricks.com/aws/en/delta/versioning)
- [Jobs API 2.1 Updates](https://docs.databricks.com/aws/en/reference/jobs-api-2-1-updates)

## Next Steps
For CI/CD integration, see `databricks-ci-integration`.
