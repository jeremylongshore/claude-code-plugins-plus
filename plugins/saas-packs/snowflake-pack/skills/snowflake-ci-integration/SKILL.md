---
name: snowflake-ci-integration
description: |
  Configure Snowflake CI/CD with GitHub Actions, SchemaChange, and Terraform.
  Use when setting up automated schema migrations, CI pipelines for Snowflake,
  or integrating SchemaChange/Terraform into your deployment workflow.
  Trigger with phrases like "snowflake CI", "snowflake GitHub Actions",
  "snowflake SchemaChange", "snowflake terraform", "snowflake CI/CD".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, data-warehouse, analytics, snowflake]
compatible-with: claude-code
---

# Snowflake CI Integration

## Overview

Set up CI/CD for Snowflake using SchemaChange for migrations, GitHub Actions for automation, and Terraform for infrastructure.

## Prerequisites

- GitHub repository with Actions enabled
- Snowflake service account with key pair auth
- SchemaChange or Terraform installed

## Instructions

### Step 1: SchemaChange for Database Migrations

```bash
# Install SchemaChange
pip install schemachange

# Directory structure
migrations/
├── V1.0.0__initial_schema.sql          # Versioned (run once, in order)
├── V1.1.0__add_orders_table.sql
├── V1.2.0__add_customer_segments.sql
├── R__views.sql                         # Repeatable (re-run on every change)
├── R__stored_procedures.sql
└── A__cleanup_temp_tables.sql           # Always run
```

```sql
-- V1.0.0__initial_schema.sql
CREATE DATABASE IF NOT EXISTS {{database}};
CREATE SCHEMA IF NOT EXISTS {{database}}.{{schema}};

CREATE TABLE IF NOT EXISTS {{database}}.{{schema}}.users (
    id INTEGER AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- V1.1.0__add_orders_table.sql
CREATE TABLE IF NOT EXISTS {{database}}.{{schema}}.orders (
    order_id INTEGER AUTOINCREMENT,
    user_id INTEGER REFERENCES {{database}}.{{schema}}.users(id),
    amount DECIMAL(12,2),
    order_date TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

```bash
# Run migrations locally
schemachange deploy \
  --root-folder migrations \
  --snowflake-account $SNOWFLAKE_ACCOUNT \
  --snowflake-user $SNOWFLAKE_USER \
  --snowflake-private-key-path ./rsa_key.p8 \
  --snowflake-warehouse DEV_WH_XS \
  --snowflake-database DEV_DB \
  --snowflake-schema PUBLIC \
  --change-history-table SCHEMACHANGE.CHANGE_HISTORY \
  --create-change-history-table \
  --vars '{"database": "DEV_DB", "schema": "PUBLIC"}'
```

### Step 2: GitHub Actions Workflow

```yaml
# .github/workflows/snowflake-deploy.yml
name: Snowflake Deploy

on:
  push:
    branches: [main]
    paths: ['migrations/**']
  pull_request:
    branches: [main]
    paths: ['migrations/**']

env:
  SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
  SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}

jobs:
  validate:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install schemachange
      - name: Dry-run migrations against staging
        env:
          SNOWFLAKE_PRIVATE_KEY: ${{ secrets.SNOWFLAKE_PRIVATE_KEY }}
        run: |
          echo "$SNOWFLAKE_PRIVATE_KEY" > /tmp/rsa_key.p8
          schemachange deploy \
            --root-folder migrations \
            --snowflake-account $SNOWFLAKE_ACCOUNT \
            --snowflake-user $SNOWFLAKE_USER \
            --snowflake-private-key-path /tmp/rsa_key.p8 \
            --snowflake-warehouse CI_WH_XS \
            --snowflake-database STAGING_DB \
            --dry-run \
            --vars '{"database": "STAGING_DB", "schema": "PUBLIC"}'

  deploy:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install schemachange
      - name: Deploy to production
        env:
          SNOWFLAKE_PRIVATE_KEY: ${{ secrets.SNOWFLAKE_PRIVATE_KEY_PROD }}
        run: |
          echo "$SNOWFLAKE_PRIVATE_KEY" > /tmp/rsa_key.p8
          schemachange deploy \
            --root-folder migrations \
            --snowflake-account $SNOWFLAKE_ACCOUNT \
            --snowflake-user $SNOWFLAKE_USER \
            --snowflake-private-key-path /tmp/rsa_key.p8 \
            --snowflake-warehouse PROD_ETL_WH \
            --snowflake-database PROD_DB \
            --change-history-table SCHEMACHANGE.CHANGE_HISTORY \
            --create-change-history-table \
            --vars '{"database": "PROD_DB", "schema": "PUBLIC"}'
```

### Step 3: Configure GitHub Secrets

```bash
# Store credentials
gh secret set SNOWFLAKE_ACCOUNT --body "myorg-myaccount"
gh secret set SNOWFLAKE_USER --body "svc_github_ci"
gh secret set SNOWFLAKE_PRIVATE_KEY < rsa_key.p8
gh secret set SNOWFLAKE_PRIVATE_KEY_PROD < rsa_key_prod.p8
```

### Step 4: Terraform for Infrastructure

```hcl
# snowflake.tf
terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.90"
    }
  }
}

provider "snowflake" {
  account  = var.snowflake_account
  user     = var.snowflake_user
  private_key = file(var.private_key_path)
  role     = "SYSADMIN"
}

resource "snowflake_database" "analytics" {
  name                        = "ANALYTICS_DB"
  data_retention_time_in_days = 14
}

resource "snowflake_warehouse" "etl" {
  name           = "ETL_WH"
  warehouse_size = "LARGE"
  auto_suspend   = 120
  auto_resume    = true
}

resource "snowflake_role" "analyst" {
  name = "ANALYST_ROLE"
}

resource "snowflake_grant_privileges_to_role" "analyst_usage" {
  role_name  = snowflake_role.analyst.name
  privileges = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.etl.name
  }
}
```

### Step 5: Integration Tests in CI

```yaml
# Add to GitHub Actions workflow
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Run Snowflake integration tests
        env:
          SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
          SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
          SNOWFLAKE_PRIVATE_KEY: ${{ secrets.SNOWFLAKE_PRIVATE_KEY }}
        run: |
          echo "$SNOWFLAKE_PRIVATE_KEY" > /tmp/rsa_key.p8
          SNOWFLAKE_PRIVATE_KEY_PATH=/tmp/rsa_key.p8 npm test
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `Duplicate script` | SchemaChange already ran it | Versioned scripts run once; check CHANGE_HISTORY |
| `Permission denied` | CI user lacks privileges | Grant required roles to CI service account |
| `Terraform drift` | Manual changes in Snowflake | Run `terraform plan` to detect, `terraform import` to sync |
| `Secret not found` | Missing GitHub secret | `gh secret set SNOWFLAKE_*` |

## Resources

- [SchemaChange](https://github.com/Snowflake-Labs/schemachange)
- [Snowflake Terraform Provider](https://registry.terraform.io/providers/Snowflake-Labs/snowflake/latest)
- [GitHub Actions](https://docs.github.com/en/actions)

## Next Steps

For deployment patterns, see `snowflake-deploy-integration`.
