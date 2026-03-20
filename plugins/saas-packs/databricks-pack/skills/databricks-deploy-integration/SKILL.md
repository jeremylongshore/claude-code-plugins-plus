---
name: databricks-deploy-integration
description: |
  Deploy Databricks jobs and pipelines with Asset Bundles.
  Use when deploying jobs to different environments, managing deployments,
  or setting up deployment automation.
  Trigger with phrases like "databricks deploy", "asset bundles",
  "databricks deployment", "deploy to production", "bundle deploy".
allowed-tools: Read, Write, Edit, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Deploy Integration

## Overview
Deploy Databricks jobs and pipelines using Databricks Asset Bundles (DABs). Asset Bundles provide infrastructure-as-code for deploying jobs, notebooks, DLT pipelines, and ML models across workspaces with proper environment isolation and CI/CD integration.

## Prerequisites
- Databricks CLI v0.200+ installed (`databricks` command)
- Workspace access with appropriate permissions
- Service principal for automated deployments
- `databricks.yml` bundle configuration

## Instructions

### Step 1: Initialize Asset Bundle
```bash
# Create new bundle from template
databricks bundle init

# Or manually create databricks.yml
```

```yaml
# databricks.yml
bundle:
  name: etl-pipeline

workspace:
  host: https://myworkspace.cloud.databricks.com

resources:
  jobs:
    daily_etl:
      name: daily-etl-${bundle.environment}
      schedule:
        quartz_cron_expression: "0 0 6 * * ?"
        timezone_id: "America/New_York"
      tasks:
        - task_key: extract
          notebook_task:
            notebook_path: ./src/extract.py
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            node_type_id: "i3.xlarge"
            num_workers: 2
        - task_key: transform
          depends_on:
            - task_key: extract
          notebook_task:
            notebook_path: ./src/transform.py

environments:
  development:
    default: true
    workspace:
      host: https://dev.cloud.databricks.com
  staging:
    workspace:
      host: https://staging.cloud.databricks.com
  production:
    workspace:
      host: https://prod.cloud.databricks.com
```

### Step 2: Deploy to Environment
```bash
# Validate bundle configuration
databricks bundle validate -e production

# Deploy resources (create/update jobs, notebooks)
databricks bundle deploy -e staging

# Run a specific job
databricks bundle run daily_etl -e staging

# Destroy resources in an environment
databricks bundle destroy -e development
```

### Step 3: CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy Databricks Bundle
on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - run: databricks bundle validate -e staging
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
      - run: databricks bundle deploy -e staging
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - run: databricks bundle deploy -e production
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_PROD_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_PROD_TOKEN }}
```

### Step 4: Verify Deployment
```bash
# List deployed jobs
databricks jobs list --output json | jq '.[] | select(.settings.name | contains("etl"))'

# Check recent runs
databricks runs list --job-id $JOB_ID --limit 5

# Get run output
databricks runs get-output --run-id $RUN_ID
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Bundle validation fails | Invalid YAML | Run `databricks bundle validate` locally |
| Permission denied | Missing workspace access | Check service principal permissions |
| Cluster start fails | Quota exceeded | Request quota increase or use smaller nodes |
| Job timeout | Long-running task | Set `timeout_seconds` in job config |

## Examples

### Parameterize Bundles per Environment
```yaml
# databricks.yml — use variables for environment-specific values
variables:
  warehouse_size:
    default: "2X-Small"
  alert_email:
    default: "dev@company.com"

environments:
  production:
    variables:
      warehouse_size: "Medium"
      alert_email: "oncall@company.com"
```

### Promote a Bundle from Staging to Production
```bash
# Validate staging is clean
databricks bundle validate -e staging

# Deploy to staging, run smoke test
databricks bundle deploy -e staging
databricks bundle run daily_etl -e staging

# After staging passes, deploy to production
databricks bundle deploy -e production

# Verify production deployment
databricks bundle validate -e production
databricks jobs list --output json | jq '.[] | select(.settings.name | contains("daily-etl-production"))'
```

### Destroy and Redeploy (Dev Only)
```bash
# Tear down dev resources for clean slate
databricks bundle destroy -e development --auto-approve

# Redeploy from scratch
databricks bundle deploy -e development
```

## Output
- `databricks.yml` Asset Bundle with multi-environment targets
- CI/CD pipeline deploying staging on merge, production on release
- Job resources created/updated in target workspace
- Verification commands confirming successful deployment

## Resources
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles)
- [Bundle Configuration Reference](https://docs.databricks.com/dev-tools/bundles/settings.html)
- [CI/CD with Bundles](https://docs.databricks.com/dev-tools/bundles/ci-cd.html)

## Next Steps
For multi-environment setup, see `databricks-multi-env-setup`.