---
name: databricks-multi-env-setup
description: |
  Configure Databricks across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Databricks configurations.
  Trigger with phrases like "databricks environments", "databricks staging",
  "databricks dev prod", "databricks environment setup", "databricks config by env".
allowed-tools: Read, Write, Edit, Bash(databricks:*), Bash(terraform:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, deployment]

---
# Databricks Multi-Environment Setup

## Overview
Configure Databricks across dev, staging, and production with isolated workspaces (or catalog-level isolation), per-environment secrets, Asset Bundle targets, and Terraform for workspace provisioning. Each environment gets its own credentials, Unity Catalog namespace, and compute policies.

## Prerequisites
- Databricks account with multiple workspaces (or Premium for catalog-level isolation)
- Service principals per environment
- Secret management (Databricks Secret Scopes, AWS Secrets Manager, or GCP Secret Manager)
- CI/CD pipeline (GitHub Actions, Azure DevOps, etc.)

## Environment Strategy

| Environment | Workspace | Catalog | Auth | Compute |
|-------------|-----------|---------|------|---------|
| Development | Shared or dedicated | `dev_catalog` | Personal PAT | Single-node, 15min auto-stop |
| Staging | Dedicated | `staging_catalog` | Service principal | Production-like, spot instances |
| Production | Dedicated | `prod_catalog` | Service principal (OAuth M2M) | Instance pools, auto-scale |

## Instructions

### Step 1: CLI Profiles per Environment
```ini
# ~/.databrickscfg
[dev]
host = https://adb-dev-workspace.7.azuredatabricks.net
token = dapi_dev_token

[staging]
host = https://adb-staging-workspace.7.azuredatabricks.net
client_id = staging-sp-client-id
client_secret = staging-sp-secret

[production]
host = https://adb-prod-workspace.7.azuredatabricks.net
client_id = prod-sp-client-id
client_secret = prod-sp-secret
```

```bash
# Use a specific environment
databricks workspace list / --profile staging
databricks clusters list --profile production
```

### Step 2: Asset Bundle Targets
```yaml
# databricks.yml — single project, multiple targets
bundle:
  name: data-platform

variables:
  catalog:
    description: Unity Catalog for this environment
    default: dev_catalog
  alert_email:
    default: dev@company.com
  cluster_size:
    default: "2X-Small"

targets:
  dev:
    default: true
    mode: development
    workspace:
      host: https://adb-dev-workspace.7.azuredatabricks.net
      root_path: /Users/${workspace.current_user.userName}/.bundle/${bundle.name}/dev
    variables:
      catalog: dev_catalog

  staging:
    workspace:
      host: https://adb-staging-workspace.7.azuredatabricks.net
      root_path: /Shared/.bundle/${bundle.name}/staging
    variables:
      catalog: staging_catalog
      alert_email: staging-alerts@company.com

  prod:
    mode: production
    workspace:
      host: https://adb-prod-workspace.7.azuredatabricks.net
      root_path: /Shared/.bundle/${bundle.name}/prod
    variables:
      catalog: prod_catalog
      alert_email: oncall@company.com
      cluster_size: "Medium"
```

### Step 3: Per-Environment Secret Scopes
```bash
# Create environment-specific secret scopes in each workspace
for env in dev staging prod; do
    databricks secrets create-scope "${env}-secrets" --profile $env
    databricks secrets put-secret "${env}-secrets" db-password --profile $env
    databricks secrets put-secret "${env}-secrets" api-key --profile $env
done
```

```python
# Access secrets in notebooks — scope name matches environment
import os

env = os.getenv("ENVIRONMENT", "dev")
db_password = dbutils.secrets.get(scope=f"{env}-secrets", key="db-password")
api_key = dbutils.secrets.get(scope=f"{env}-secrets", key="api-key")
```

### Step 4: Environment-Aware Python Config
```python
# config/databricks_config.py
from dataclasses import dataclass
import os

@dataclass
class DatabricksEnvConfig:
    host: str
    catalog: str
    secret_scope: str
    debug: bool
    max_retries: int
    timeout_seconds: int

CONFIGS = {
    "dev": DatabricksEnvConfig(
        host=os.getenv("DATABRICKS_HOST_DEV", ""),
        catalog="dev_catalog",
        secret_scope="dev-secrets",
        debug=True,
        max_retries=3,
        timeout_seconds=30,
    ),
    "staging": DatabricksEnvConfig(
        host=os.getenv("DATABRICKS_HOST_STAGING", ""),
        catalog="staging_catalog",
        secret_scope="staging-secrets",
        debug=False,
        max_retries=3,
        timeout_seconds=60,
    ),
    "prod": DatabricksEnvConfig(
        host=os.getenv("DATABRICKS_HOST_PROD", ""),
        catalog="prod_catalog",
        secret_scope="prod-secrets",
        debug=False,
        max_retries=5,
        timeout_seconds=120,
    ),
}

def get_config() -> DatabricksEnvConfig:
    env = os.getenv("ENVIRONMENT", "dev")
    config = CONFIGS.get(env)
    if not config:
        raise ValueError(f"Unknown environment: {env}")
    if not config.host:
        raise ValueError(f"DATABRICKS_HOST_{env.upper()} not set")
    return config
```

### Step 5: CI/CD with Environment Secrets
```yaml
# .github/workflows/deploy.yml
name: Deploy Pipeline

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
      - run: databricks bundle deploy -t staging
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET }}

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - run: databricks bundle deploy -t prod
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST_PROD }}
          DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID_PROD }}
          DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET_PROD }}
```

### Step 6: Terraform for Workspace Provisioning (Optional)
```hcl
# terraform/main.tf
resource "databricks_workspace" "staging" {
  provider                = databricks.accounts
  workspace_name          = "data-platform-staging"
  aws_region             = "us-east-1"
  pricing_tier           = "PREMIUM"
  deployment_name        = "data-platform-staging"
  managed_services_customer_managed_key_id = var.cmk_id
}

resource "databricks_catalog" "staging" {
  provider = databricks.staging
  name     = "staging_catalog"
  comment  = "Staging environment catalog"
}

resource "databricks_schema" "staging_bronze" {
  provider   = databricks.staging
  catalog_name = databricks_catalog.staging.name
  name       = "bronze"
}
```

## Output
- CLI profiles configured per environment (`~/.databrickscfg`)
- Asset Bundle with dev/staging/prod targets and variable overrides
- Per-environment secret scopes with isolated credentials
- Python config class for environment-aware code
- CI/CD pipeline with GitHub environment secrets and approval gates

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment targeted | Missing `--profile` or `-t` flag | Default profile should always be dev |
| Cross-env data leak | Shared catalog | Use separate catalogs per environment |
| Secret not found | Wrong scope name | Verify scope exists: `databricks secrets list-scopes --profile $env` |
| CI auth failure | Expired service principal secret | Regenerate OAuth secret or use OIDC |

## Examples

### Quick Environment Verification
```bash
for profile in dev staging production; do
    echo "=== $profile ==="
    databricks current-user me --profile $profile 2>/dev/null && echo "OK" || echo "FAILED"
done
```

### Startup Validation
```python
config = get_config()
print(f"Environment: {os.getenv('ENVIRONMENT', 'dev')}")
print(f"Catalog: {config.catalog}")
print(f"Debug: {config.debug}")
```

## Resources
- [Declarative Automation Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [CLI Authentication](https://docs.databricks.com/aws/en/dev-tools/cli/authentication)
- [Terraform Provider](https://docs.databricks.com/aws/en/dev-tools/terraform/)

## Next Steps
For deployment, see `databricks-deploy-integration`.
