---
name: databricks-local-dev-loop
description: |
  Configure Databricks local development with Databricks Connect, Asset Bundles, and IDE.
  Use when setting up a local dev environment, configuring test workflows,
  or establishing a fast iteration cycle with Databricks.
  Trigger with phrases like "databricks dev setup", "databricks local",
  "databricks IDE", "develop with databricks", "databricks connect".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(databricks:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, testing, workflow]

---
# Databricks Local Dev Loop

## Overview
Set up a fast local development workflow using Databricks Connect v2, Asset Bundles, and VS Code. Databricks Connect lets you run PySpark code locally while executing on a remote Databricks cluster, giving you IDE debugging, fast iteration, and proper test isolation.

## Prerequisites
- Completed `databricks-install-auth` setup
- Python 3.10+ (must match cluster's Python version)
- A running Databricks cluster (DBR 13.3 LTS+)
- VS Code or PyCharm

## Instructions

### Step 1: Project Structure
```
my-databricks-project/
├── src/
│   ├── __init__.py
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── bronze.py          # Raw ingestion
│   │   ├── silver.py          # Cleansing transforms
│   │   └── gold.py            # Business aggregations
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── tests/
│   ├── conftest.py            # Spark fixtures
│   ├── unit/
│   │   └── test_transforms.py # Local Spark tests
│   └── integration/
│       └── test_pipeline.py   # Databricks Connect tests
├── notebooks/
│   └── exploration.py
├── resources/
│   └── daily_etl.yml          # Job resource definitions
├── databricks.yml             # Asset Bundle root config
├── pyproject.toml
└── requirements.txt
```

### Step 2: Install Development Tools
```bash
set -euo pipefail

# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Databricks Connect v2 — version MUST match cluster DBR
pip install "databricks-connect==14.3.*"

# SDK and CLI
pip install databricks-sdk

# Testing
pip install pytest pytest-cov

# Verify Connect installation
databricks-connect test
```

### Step 3: Configure Databricks Connect
Databricks Connect v2 reads from standard SDK auth (env vars, `~/.databrickscfg`, or `DATABRICKS_CLUSTER_ID`).

```bash
# Set cluster for Connect to use
export DATABRICKS_HOST="https://adb-1234567890123456.7.azuredatabricks.net"
export DATABRICKS_TOKEN="dapi..."
export DATABRICKS_CLUSTER_ID="0123-456789-abcde123"
```

```python
# src/utils/spark_session.py
from databricks.connect import DatabricksSession

def get_spark():
    """Get a DatabricksSession — runs Spark on the remote cluster."""
    return DatabricksSession.builder.getOrCreate()

# Usage: df operations execute on the remote cluster
spark = get_spark()
df = spark.sql("SELECT current_timestamp() AS now")
df.show()  # Results streamed back locally
```

### Step 4: Asset Bundle Configuration
```yaml
# databricks.yml
bundle:
  name: my-databricks-project

workspace:
  host: ${DATABRICKS_HOST}

include:
  - resources/*.yml

variables:
  catalog:
    description: Unity Catalog name
    default: dev_catalog

targets:
  dev:
    default: true
    mode: development
    workspace:
      root_path: /Users/${workspace.current_user.userName}/.bundle/${bundle.name}/dev

  staging:
    workspace:
      root_path: /Shared/.bundle/${bundle.name}/staging
    variables:
      catalog: staging_catalog

  prod:
    mode: production
    workspace:
      root_path: /Shared/.bundle/${bundle.name}/prod
    variables:
      catalog: prod_catalog
```

```yaml
# resources/daily_etl.yml
resources:
  jobs:
    daily_etl:
      name: "daily-etl-${bundle.target}"
      tasks:
        - task_key: bronze
          notebook_task:
            notebook_path: src/pipelines/bronze.py
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            node_type_id: "i3.xlarge"
            num_workers: 2
```

### Step 5: Test Setup
```python
# tests/conftest.py
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def local_spark():
    """Local SparkSession for fast unit tests (no cluster needed)."""
    return (
        SparkSession.builder
        .master("local[*]")
        .appName("unit-tests")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )

@pytest.fixture(scope="session")
def remote_spark():
    """DatabricksSession for integration tests (requires running cluster)."""
    from databricks.connect import DatabricksSession
    return DatabricksSession.builder.getOrCreate()
```

```python
# tests/unit/test_transforms.py
def test_dedup_by_primary_key(local_spark):
    from src.pipelines.silver import dedup_by_key

    data = [("a", 1), ("a", 2), ("b", 3)]
    df = local_spark.createDataFrame(data, ["id", "value"])

    result = dedup_by_key(df, key_col="id", order_col="value")
    assert result.count() == 2
    # Keeps latest value per key
    assert result.filter("id = 'a'").first()["value"] == 2
```

### Step 6: Dev Workflow Commands
```bash
# Validate bundle configuration
databricks bundle validate

# Deploy dev resources to workspace
databricks bundle deploy -t dev

# Run a job
databricks bundle run daily_etl -t dev

# Sync local files to workspace (live reload)
databricks bundle sync -t dev --watch

# Run local unit tests (fast, no cluster)
pytest tests/unit/ -v

# Run integration tests (needs cluster)
pytest tests/integration/ -v --tb=short

# Full test with coverage
pytest tests/ --cov=src --cov-report=html
```

### Step 7: VS Code Configuration
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.envFile": "${workspaceFolder}/.env",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

## Output
- Local Python environment with Databricks Connect
- Unit tests running with local Spark (no cluster required)
- Integration tests running against remote cluster
- Asset Bundle configured for dev/staging/prod deployment
- VS Code debugging with breakpoints in PySpark code

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Cluster not running` | Auto-terminated | Set `DATABRICKS_CLUSTER_ID` and start it: `databricks clusters start --cluster-id ...` |
| `Version mismatch` | `databricks-connect` version differs from cluster DBR | Install matching version: `pip install "databricks-connect==14.3.*"` for DBR 14.3 |
| `SPARK_CONNECT_GRPC` error | gRPC connection blocked | Check firewall allows outbound to workspace on port 443 |
| `ModuleNotFoundError` | Missing local package install | Run `pip install -e .` for editable install |
| `Multiple SparkSessions` | Conflicting Spark instances | Always use `getOrCreate()` pattern |

## Examples

### Interactive Development Script
```python
# src/pipelines/bronze.py
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import current_timestamp, input_file_name

def ingest_raw(spark: SparkSession, source_path: str, target_table: str) -> DataFrame:
    """Bronze ingestion with metadata columns."""
    return (
        spark.read.format("json").load(source_path)
        .withColumn("_ingested_at", current_timestamp())
        .withColumn("_source_file", input_file_name())
    )

if __name__ == "__main__":
    # Works locally via Databricks Connect
    from databricks.connect import DatabricksSession
    spark = DatabricksSession.builder.getOrCreate()
    df = ingest_raw(spark, "/mnt/raw/events/", "dev_catalog.bronze.events")
    df.show(5)
```

## Resources
- [Databricks Connect v2](https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/)
- [Declarative Automation Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [VS Code Extension](https://docs.databricks.com/aws/en/dev-tools/vscode-ext/)

## Next Steps
See `databricks-sdk-patterns` for production-ready code patterns.
