---
name: shopify-multi-env-setup
description: |
  Configure Shopify apps across development, staging, and production environments
  with separate stores, API credentials, and app instances.
  Use when setting up isolated dev/staging/prod environments for a Shopify app,
  managing multiple development stores, or configuring per-environment credentials.
  Trigger with phrases like "shopify environments", "shopify staging",
  "shopify dev vs prod", "shopify multi-store", "shopify environment setup".
allowed-tools: Read, Write, Edit, Bash(shopify:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Multi-Environment Setup

## Overview

Configure Shopify apps with isolated development, staging, and production environments. Each environment uses a separate Shopify app instance, development store, and credentials.

## Prerequisites

- Shopify Partner account
- Multiple development stores (free to create in Partner Dashboard)
- Secret management solution for production (Vault, AWS Secrets Manager, etc.)

## Instructions

### Step 1: Create Separate App Instances

Create one app per environment in your Partner Dashboard:

| Environment | App Name | Store | Purpose |
|-------------|----------|-------|---------|
| Development | My App (Dev) | dev-store.myshopify.com | Local development |
| Staging | My App (Staging) | staging-store.myshopify.com | Pre-prod testing |
| Production | My App | live-store.myshopify.com | Live traffic |

Each app gets its own `API_KEY`, `API_SECRET`, and `ACCESS_TOKEN`.

### Step 2: Environment Configuration Files

Create `.env.*` files for each environment and corresponding Shopify CLI TOML configs. Production secrets should never be stored on disk -- use a secret manager.

See [Environment Config Files](references/environment-config-files.md) for the complete `.env` and `.toml` configuration templates.

### Step 3: Environment-Aware Configuration

TypeScript config module that loads environment-specific settings (debug mode, session storage type) with `LATEST_API_VERSION` from `@shopify/shopify-api`.

See [Environment-Aware Config](references/environment-aware-config.md) for the complete implementation.

### Step 4: Environment Guards

Safety functions that prevent dangerous operations from running in the wrong environment (e.g., blocking test data seeding in production, requiring production for billing activation).

See [Environment Guards](references/environment-guards.md) for the complete implementation.

## Output

- Isolated environments with separate app instances
- Environment-specific configuration loading
- Shopify CLI configured for multi-env workflow
- Safety guards preventing cross-environment mistakes

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong store in dev | Using prod .env | Verify `SHOPIFY_STORE` in your .env file |
| OAuth fails on staging | Wrong redirect URL | Update redirect_urls in staging app config |
| Webhooks not received | URL mismatch | Each environment needs its own webhook URLs |
| Production guard triggered | Wrong NODE_ENV | Set NODE_ENV correctly in deployment platform |

## Examples

### Development Store Quick Setup

```bash
# Create a development store from Partner Dashboard
# Partners > Stores > Add store > Development store

# Install your dev app on the dev store
shopify app dev --store=dev-store.myshopify.com

# Populate test data
shopify populate products --count=25
shopify populate orders --count=10
shopify populate customers --count=20
```

## Resources

- [Shopify Development Stores](https://shopify.dev/docs/apps/tools/development-stores)
- [Shopify CLI Config](https://shopify.dev/docs/apps/build/cli-for-apps/app-configuration)
- [12-Factor App Config](https://12factor.net/config)
