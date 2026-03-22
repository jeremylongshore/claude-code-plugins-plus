---
name: databricks-deploy-integration
description: |
  Deploy Databricks jobs and pipelines with Declarative Automation Bundles.
  Use when deploying jobs to different environments, managing deployments,
  or setting up deployment automation.
  Trigger with phrases like "databricks deploy", "asset bundles",
  "databricks deployment", "deploy to production", "bundle deploy".
allowed-tools: Read, Write, Edit, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, deployment]

---
# Databricks Deploy Integration

## Overview
Deploy Databricks jobs, DLT pipelines, and ML models using Declarative Automation Bundles (DABs, formerly Asset Bundles). Bundles provide infrastructure-as-code with `databricks.yml` defining resources, targets (dev/staging/prod), variables, and permissions. The CLI handles validation, deployment, and lifecycle management.

## Prerequisites
- Databricks CLI v0.200+ (`databricks --version`)
- Workspace access with service principal for automated deploys
- `databricks.yml` bundle configuration at project root

## Instructions

### Step 1: Initialize a Bundle
```bash
# Create from a template
databricks bundle init

# Available templates:
# - default-python: Python notebook project
# - default-sql: SQL project
# - mlops-stacks: Full MLOps template with feature engineering
```

### Step 2: Configure `databricks.yml`
```yaml
# databricks.yml — single source of truth for project deployment
bundle:
  name: sales-etl-pipeline

workspace:
  host: ${DATABRICKS_HOST}

variables:
  catalog:
    description: Unity Catalog name
    default: dev_catalog
  alert_email:
    description: Alert notification email
    default: dev@company.com
  warehouse_size:
    default: "2X-Small"

include:
  - resources/*.yml

targets:
  dev:
    default: true
    mode: development
    # dev mode auto-prefixes resources with [username] and enables debug
    workspace:
      root_path: /Users/${workspace.current_user.userName}/.bundle/${bundle.name}/dev
    variables:
      catalog: dev_catalog

  staging:
    workspace:
      root_path: /Shared/.bundle/${bundle.name}/staging
    variables:
      catalog: staging_catalog
      alert_email: staging-alerts@company.com

  prod:
    mode: production
    # production mode prevents accidental destruction
    workspace:
      root_path: /Shared/.bundle/${bundle.name}/prod
    variables:
      catalog: prod_catalog
      alert_email: oncall@company.com
      warehouse_size: "Medium"
```

### Step 3: Define Resources
```yaml
# resources/jobs.yml
resources:
  jobs:
    daily_etl:
      name: "daily-etl-${bundle.target}"
      max_concurrent_runs: 1
      timeout_seconds: 14400

      schedule:
        quartz_cron_expression: "0 0 6 * * ?"
        timezone_id: "UTC"

      email_notifications:
        on_failure: ["${var.alert_email}"]

      tasks:
        - task_key: extract
          notebook_task:
            notebook_path: ./src/extract.py
            base_parameters:
              catalog: "${var.catalog}"
          job_cluster_key: etl

        - task_key: transform
          depends_on: [{task_key: extract}]
          notebook_task:
            notebook_path: ./src/transform.py
          job_cluster_key: etl

        - task_key: load
          depends_on: [{task_key: transform}]
          notebook_task:
            notebook_path: ./src/load.py
          job_cluster_key: etl

      job_clusters:
        - job_cluster_key: etl
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            node_type_id: "i3.xlarge"
            autoscale:
              min_workers: 1
              max_workers: 4
            aws_attributes:
              availability: SPOT_WITH_FALLBACK
              first_on_demand: 1
```

```yaml
# resources/pipelines.yml (DLT)
resources:
  pipelines:
    dlt_pipeline:
      name: "dlt-pipeline-${bundle.target}"
      target: "${var.catalog}.silver"
      catalog: "${var.catalog}"
      libraries:
        - notebook:
            path: ./src/dlt_pipeline.py
      continuous: false
      development: ${bundle.target == "dev"}
```

### Step 4: Deploy Lifecycle Commands
```bash
# Validate — checks YAML syntax, variable resolution, permissions
databricks bundle validate -t staging

# Deploy — creates/updates jobs, uploads notebooks, syncs config
databricks bundle deploy -t staging

# Summary — show what's deployed
databricks bundle summary -t staging

# Run — trigger a specific job/pipeline
databricks bundle run daily_etl -t staging

# Run and wait for completion
databricks bundle run daily_etl -t staging --restart-all-workflows

# Sync — live-reload files during development
databricks bundle sync -t dev --watch

# Destroy — remove all deployed resources (dev only!)
databricks bundle destroy -t dev --auto-approve
```

### Step 5: Promote Staging to Production
```bash
# 1. Validate staging is clean
databricks bundle validate -t staging

# 2. Deploy and test on staging
databricks bundle deploy -t staging
RUN=$(databricks bundle run daily_etl -t staging --output json | jq -r '.run_id')
databricks runs get --run-id $RUN | jq '.state.result_state'

# 3. After staging passes, deploy to production
databricks bundle validate -t prod
databricks bundle deploy -t prod

# 4. Verify production deployment
databricks bundle summary -t prod
databricks jobs list --output json | \
  jq '.[] | select(.settings.name | contains("daily-etl-prod"))'
```

### Step 6: Permissions in Bundles
```yaml
# resources/jobs.yml — add permissions block
resources:
  jobs:
    daily_etl:
      name: "daily-etl-${bundle.target}"
      permissions:
        - group_name: data-engineers
          level: CAN_MANAGE
        - group_name: data-analysts
          level: CAN_VIEW
        - service_principal_name: cicd-service-principal
          level: CAN_MANAGE_RUN
```

## Output
- `databricks.yml` with multi-target deployment (dev/staging/prod)
- Job and pipeline resources defined as code
- Environment-specific variables (catalog, alerts, sizing)
- Promotion workflow from staging to production
- Permissions managed declaratively in bundle config

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `bundle validate` fails | Invalid YAML or unresolved variable | Check variable definitions and target config |
| `PERMISSION_DENIED` on deploy | Service principal lacks workspace access | Add SP to workspace in Account Console |
| `RESOURCE_CONFLICT` | Resource name collision across targets | Bundle auto-prefixes in `development` mode |
| `Cluster quota exceeded` | Too many active clusters | Use instance pools or terminate idle clusters |
| `Cannot destroy production` | `mode: production` prevents accidental destroy | This is intentional — remove mode or use `--force` |

## Examples

### Override Variables per Target
```bash
# Override a variable at deploy time
databricks bundle deploy -t prod --var="warehouse_size=Large"
```

### Clean Slate Redeploy (Dev Only)
```bash
databricks bundle destroy -t dev --auto-approve
databricks bundle deploy -t dev
```

## Resources
- [Declarative Automation Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [Bundle Configuration Reference](https://docs.databricks.com/aws/en/dev-tools/bundles/reference)
- [Bundle Resources](https://docs.databricks.com/aws/en/dev-tools/bundles/resources)
- [Deployment Modes](https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes)

## Next Steps
For multi-environment setup, see `databricks-multi-env-setup`.
