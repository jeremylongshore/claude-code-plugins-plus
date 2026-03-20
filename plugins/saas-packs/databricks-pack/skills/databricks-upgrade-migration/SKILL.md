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

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

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

For Unity Catalog migration script, API endpoint migration, Delta protocol upgrade, and complete migration runbook, see [Migration Scripts](references/migration-scripts.md).

## Output
- DBR version upgraded with compatibility verified
- Hive Metastore tables migrated to Unity Catalog
- Deprecated API calls updated to v2.1 endpoints
- Delta Lake protocol upgraded for new features (deletion vectors, liquid clustering)

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Incompatible library | DBR version mismatch | Pin library to compatible version in `requirements.txt` |
| `PERMISSION_DENIED` on table | Missing Unity Catalog grants | Run `GRANT USE CATALOG`, `GRANT USE SCHEMA` for target |
| Table sync failed | Storage location inaccessible | Check cloud storage permissions and network config |
| Protocol downgrade error | Target version lower than current | Cannot downgrade — `DEEP CLONE` to a new table instead |

## Examples

### Quick Upgrade Check
```bash
set -euo pipefail
echo "Current DBR: $(databricks clusters get --cluster-id $CLUSTER_ID | jq -r .spark_version)"
echo "Current SDK: $(pip show databricks-sdk | grep Version)"
pip install --upgrade databricks-sdk
echo "Updated SDK: $(pip show databricks-sdk | grep Version)"
```

## Resources
- [Databricks Runtime Release Notes](https://docs.databricks.com/release-notes/runtime/releases.html)
- [Unity Catalog Migration](https://docs.databricks.com/data-governance/unity-catalog/migrate.html)
- [Delta Lake Protocol Versions](https://docs.databricks.com/delta/versioning.html)

## Next Steps
For CI/CD integration, see `databricks-ci-integration`.