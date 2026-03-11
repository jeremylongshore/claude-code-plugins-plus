---
name: databricks-local-dev-loop
description: |
  Configure Databricks local development with dbx, Databricks Connect, and IDE.
  Use when setting up a local dev environment, configuring test workflows,
  or establishing a fast iteration cycle with Databricks.
  Trigger with phrases like "databricks dev setup", "databricks local",
  "databricks IDE", "develop with databricks", "databricks connect".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(databricks:*), Bash(dbx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Databricks.

## Prerequisites
- Completed `databricks-install-auth` setup
- Python 3.8+ with pip
- VS Code or PyCharm IDE
- Access to a running cluster

## Instructions

### Step 1: Project Structure
```
my-databricks-project/
├── src/
│   ├── __init__.py
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── bronze.py       # Raw data ingestion
│   │   ├── silver.py       # Data cleansing
│   │   └── gold.py         # Business aggregations
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── test_helpers.py
│   └── integration/
│       └── test_pipelines.py
├── notebooks/              # Databricks notebooks
│   └── exploration.py
├── resources/              # Asset Bundle configs
│   └── jobs.yml
├── databricks.yml          # Asset Bundle project config
├── .env.local              # Local secrets (git-ignored)
├── .env.example            # Template for team
├── pyproject.toml
└── requirements.txt
```

### Step 2: Install Development Tools
```bash
set -euo pipefail
# Install Databricks SDK and CLI
pip install databricks-sdk databricks-cli

# Install dbx for deployment
pip install dbx

# Install Databricks Connect v2 (for local Spark)
pip install databricks-connect==14.3.*

# Install testing tools
pip install pytest pytest-cov
```

### Step 3: Configure Databricks Connect
```bash
# Configure Databricks Connect for local development
databricks-connect configure

# Or set environment variables
export DATABRICKS_HOST="https://adb-1234567890.1.azuredatabricks.net"
export DATABRICKS_TOKEN="dapi..."
export DATABRICKS_CLUSTER_ID="1234-567890-abcde123"  # 567890: port 1234 - example/test
```

### Step 4: Create databricks.yml (Asset Bundle)
```yaml
# databricks.yml
bundle:
  name: my-databricks-project

workspace:
  host: ${DATABRICKS_HOST}

variables:
  catalog:
    description: Unity Catalog name
    default: main
  schema:
    description: Schema name
    default: default

targets:
  dev:
    default: true
    mode: development
    workspace:
      root_path: /Users/${workspace.current_user.userName}/.bundle/${bundle.name}/dev

  staging:
    mode: development
    workspace:
      root_path: /Shared/.bundle/${bundle.name}/staging

  prod:
    mode: production
    workspace:
      root_path: /Shared/.bundle/${bundle.name}/prod
```

### Step 5: Local Testing Setup
```python
# tests/conftest.py
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    """Create local SparkSession for unit tests."""
    return SparkSession.builder \
        .master("local[*]") \
        .appName("unit-tests") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

@pytest.fixture(scope="session")
def dbx_spark():
    """Connect to Databricks cluster for integration tests."""
    from databricks.connect import DatabricksSession
    return DatabricksSession.builder.getOrCreate()
```

### Step 6: VS Code Configuration
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "databricks.python.envFile": "${workspaceFolder}/.env.local"
}
```

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File (Databricks Connect)",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "env": {
        "DATABRICKS_HOST": "${env:DATABRICKS_HOST}",
        "DATABRICKS_TOKEN": "${env:DATABRICKS_TOKEN}",
        "DATABRICKS_CLUSTER_ID": "${env:DATABRICKS_CLUSTER_ID}"
      }
    }
  ]
}
```

## Output
- Working local development environment
- Databricks Connect configured for remote execution
- Unit and integration test setup
- VS Code/PyCharm integration ready

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Cluster not running` | Auto-terminated | Start cluster first |
| `Version mismatch` | DBR vs Connect version | Match databricks-connect version to DBR |
| `Module not found` | Missing local install | Run `pip install -e .` |
| `Connection timeout` | Network/firewall | Check VPN and firewall rules |
| `SparkSession already exists` | Multiple sessions | Use `getOrCreate()` pattern |

## Examples

### Run Tests Locally
```bash
# Unit tests (local Spark)
pytest tests/unit/ -v

# Integration tests (Databricks Connect)
pytest tests/integration/ -v --tb=short

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Deploy with Asset Bundles
```bash
# Validate bundle
databricks bundle validate

# Deploy to dev
databricks bundle deploy -t dev

# Run job
databricks bundle run -t dev my-job
```

### Interactive Development
```python
# src/pipelines/bronze.py
from pyspark.sql import SparkSession, DataFrame

def ingest_raw_data(spark: SparkSession, source_path: str) -> DataFrame:
    """Ingest raw data from source."""
    return spark.read.format("json").load(source_path)

if __name__ == "__main__":
    # Works locally with Databricks Connect
    from databricks.connect import DatabricksSession
    spark = DatabricksSession.builder.getOrCreate()

    df = ingest_raw_data(spark, "/mnt/raw/events")
    df.show()
```

### Hot Reload with dbx
```bash
# Watch for changes and sync
dbx sync --watch

# Or use Asset Bundles
databricks bundle sync -t dev --watch
```

## Resources
- [Databricks Connect](https://docs.databricks.com/dev-tools/databricks-connect.html)
- [Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [VS Code Extension](https://docs.databricks.com/dev-tools/vscode-ext.html)
- [Testing Notebooks](https://docs.databricks.com/notebooks/testing.html)

## Next Steps
See `databricks-sdk-patterns` for production-ready code patterns.