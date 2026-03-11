---
name: databricks-ci-integration
description: |
  Configure Databricks CI/CD integration with GitHub Actions and Asset Bundles.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Databricks deployments into your build process.
  Trigger with phrases like "databricks CI", "databricks GitHub Actions",
  "databricks automated tests", "CI databricks", "databricks pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks CI Integration

## Overview
Automate Databricks deployments with Asset Bundles and GitHub Actions. Covers bundle validation, unit testing notebooks, deploying to staging/production, and integration testing against Databricks workspaces.

## Prerequisites
- Databricks workspace with service principal
- Databricks CLI v0.200+ installed
- GitHub secrets for authentication
- Asset Bundle (`databricks.yml`) configured

## Instructions

### Step 1: GitHub Actions for Bundle Validation
```yaml
# .github/workflows/databricks-ci.yml
name: Databricks CI

on:
  pull_request:
    paths:
      - 'src/**'
      - 'resources/**'
      - 'databricks.yml'
      - 'tests/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Databricks CLI
        run: |
          curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

      - name: Validate bundle
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: databricks bundle validate

      - name: Run Python unit tests
        run: |
          pip install pytest pyspark delta-spark
          pytest tests/unit/ -v --tb=short

  deploy-staging:
    needs: validate
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Databricks CLI
        run: curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

      - name: Deploy to staging
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: databricks bundle deploy --target staging
```

### Step 2: Unit Tests for Notebooks
```python
# tests/unit/test_transformations.py
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[*]").getOrCreate()

def test_clean_events(spark):
    """Test silver layer cleaning logic."""
    from src.transformation.silver_clean_events import clean_events

    schema = StructType([
        StructField("event_id", StringType()),
        StructField("user_id", StringType()),
        StructField("event_type", StringType()),
        StructField("timestamp", StringType()),
    ])

    raw_data = [
        ("1", "user-1", "click", "2024-01-01T00:00:00Z"),  # 2024 year
        ("1", "user-1", "click", "2024-01-01T00:00:00Z"),  # Duplicate
        ("2", None, "click", "2024-01-02T00:00:00Z"),       # Null user
    ]

    df = spark.createDataFrame(raw_data, schema)
    result = clean_events(df)

    assert result.count() == 1  # Deduped and nulls removed
    assert result.first()["user_id"] == "user-1"

def test_aggregate_metrics(spark):
    """Test gold layer aggregation."""
    from src.aggregation.gold_daily_metrics import aggregate_daily

    # Create test data...
    result = aggregate_daily(spark, "2024-01-01")
    assert result.count() > 0
```

### Step 3: Deploy to Production on Merge
```yaml
# .github/workflows/databricks-deploy.yml
name: Databricks Deploy

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'resources/**'
      - 'databricks.yml'

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Install Databricks CLI
        run: curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

      - name: Validate bundle
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST_PROD }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN_PROD }}
        run: databricks bundle validate --target prod

      - name: Deploy to production
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST_PROD }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN_PROD }}
        run: |
          databricks bundle deploy --target prod
          databricks bundle run daily_etl --target prod --no-wait
```

### Step 4: Integration Tests
```yaml
  integration-tests:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Databricks CLI
        run: curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

      - name: Run integration test job
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          # Run the test notebook on staging
          databricks bundle run integration_tests --target staging

      - name: Verify output tables
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          databricks sql execute \
            --statement "SELECT COUNT(*) FROM staging_catalog.silver.clean_events WHERE date = current_date()"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Bundle validation fails | Invalid YAML | Run `databricks bundle validate` locally first |
| Auth error in CI | Token expired | Use service principal with OIDC |
| Test cluster timeout | Cluster not started | Increase timeout or use existing cluster |
| Deploy conflict | Concurrent deployments | Use GitHub environments with concurrency limit |

## Examples

### Quick Local Validation
```bash
# Validate and see what would be deployed
databricks bundle validate --target staging
databricks bundle deploy --target staging --dry-run
```

## Resources
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/)
- [Databricks GitHub Actions](https://github.com/databricks/setup-cli)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale