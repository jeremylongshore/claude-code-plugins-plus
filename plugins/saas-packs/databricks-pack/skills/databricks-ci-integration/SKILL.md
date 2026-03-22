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
tags: [saas, databricks, deployment, testing, ci-cd]

---
# Databricks CI Integration

## Overview
Automate Databricks deployments with Declarative Automation Bundles (DABs) and GitHub Actions. Covers bundle validation, unit testing PySpark transforms locally, deploying to staging on PR, production on merge, and integration testing against live workspaces. Uses `databricks/setup-cli` action and OAuth M2M for secure CI auth.

## Prerequisites
- Databricks workspace with service principal (OAuth M2M)
- Asset Bundle (`databricks.yml`) configured
- GitHub repo with Actions enabled
- GitHub environment secrets: `DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`

## Instructions

### Step 1: GitHub Actions — Validate and Test on PR
```yaml
# .github/workflows/databricks-ci.yml
name: Databricks CI

on:
  pull_request:
    paths: ['src/**', 'resources/**', 'databricks.yml', 'tests/**']

jobs:
  validate-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install pytest pyspark delta-spark databricks-sdk
          pip install -e .  # If using pyproject.toml

      - name: Run unit tests (local Spark, no cluster needed)
        run: pytest tests/unit/ -v --tb=short

      - name: Install Databricks CLI
        uses: databricks/setup-cli@main

      - name: Validate bundle
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET }}
        run: databricks bundle validate -t staging

  deploy-staging:
    needs: validate-and-test
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main

      - name: Deploy to staging
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET }}
        run: databricks bundle deploy -t staging

      - name: Run integration tests on staging
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET }}
        run: |
          databricks bundle run integration_tests -t staging
          # Verify output tables
          databricks sql execute \
            --warehouse-id "$WAREHOUSE_ID" \
            --statement "SELECT COUNT(*) AS rows FROM staging_catalog.silver.orders WHERE date >= current_date() - 1"
```

### Step 2: Unit Tests for PySpark Transforms
```python
# tests/unit/test_transformations.py
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[*]").appName("tests").getOrCreate()

def test_silver_dedup(spark):
    """Test deduplication logic in silver layer."""
    from src.pipelines.silver import dedup_orders

    data = [
        ("order-1", "user-a", 10.0),
        ("order-1", "user-a", 10.0),  # duplicate
        ("order-2", "user-b", 20.0),
    ]
    schema = StructType([
        StructField("order_id", StringType()),
        StructField("user_id", StringType()),
        StructField("amount", DoubleType()),
    ])
    df = spark.createDataFrame(data, schema)
    result = dedup_orders(df)

    assert result.count() == 2
    assert set(r.order_id for r in result.collect()) == {"order-1", "order-2"}

def test_gold_aggregation(spark):
    """Test daily aggregation in gold layer."""
    from src.pipelines.gold import aggregate_daily_revenue
    # ... test with sample data
```

### Step 3: Deploy to Production on Merge
```yaml
# .github/workflows/databricks-deploy.yml
name: Databricks Deploy

on:
  push:
    branches: [main]
    paths: ['src/**', 'resources/**', 'databricks.yml']

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production  # Requires approval if configured
    concurrency:
      group: databricks-prod-deploy
      cancel-in-progress: false
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main

      - name: Validate production bundle
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST_PROD }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID_PROD }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET_PROD }}
        run: databricks bundle validate -t prod

      - name: Deploy to production
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST_PROD }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID_PROD }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET_PROD }}
        run: |
          databricks bundle deploy -t prod
          echo "## Deployment Summary" >> $GITHUB_STEP_SUMMARY
          databricks bundle summary -t prod >> $GITHUB_STEP_SUMMARY

      - name: Trigger smoke test
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST_PROD }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID_PROD }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET_PROD }}
        run: databricks bundle run prod_etl_pipeline -t prod --no-wait
```

### Step 4: OIDC Authentication (Keyless CI)
Eliminate long-lived secrets by using GitHub OIDC federation with Databricks.

```yaml
# In GitHub Actions — no client_secret needed
jobs:
  deploy:
    permissions:
      id-token: write  # Required for OIDC
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main

      - name: Deploy with OIDC
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
          # No DATABRICKS_CLIENT_SECRET — uses GitHub OIDC token
          ARM_USE_OIDC: true
        run: databricks bundle deploy -t prod
```

## Output
- CI workflow validating bundles and running unit tests on every PR
- Staging deployment with integration tests before merge
- Production deployment on merge to main with approval gate
- Concurrency control preventing parallel deployments

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Bundle validation fails | Invalid YAML or missing variables | Run `databricks bundle validate` locally first |
| Auth error in CI | Client secret expired | Regenerate OAuth secret or switch to OIDC |
| Integration test timeout | Cluster cold start | Use instance pools or increase timeout |
| Deploy conflict | Concurrent CI runs | Use `concurrency` group in GitHub Actions |
| PySpark import error | Missing `pyspark` in CI | Add to `pip install` step |

## Examples

### Local Validation Before Push
```bash
# Validate and dry-run before committing
databricks bundle validate -t staging
databricks bundle deploy -t staging --dry-run
pytest tests/unit/ -v
```

### Branch-Based Development Targets
```yaml
# databricks.yml — auto-name resources per developer
targets:
  dev:
    default: true
    mode: development
    # In dev mode, resources auto-prefixed with [dev username]
    workspace:
      root_path: /Users/${workspace.current_user.userName}/.bundle/${bundle.name}/dev
```

## Resources
- [CI/CD with Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/ci-cd-bundles)
- [databricks/setup-cli Action](https://github.com/databricks/setup-cli)
- [OAuth M2M](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m)
- [Bundle Configuration](https://docs.databricks.com/aws/en/dev-tools/bundles/settings)

## Next Steps
For Asset Bundle deployment details, see `databricks-deploy-integration`.
