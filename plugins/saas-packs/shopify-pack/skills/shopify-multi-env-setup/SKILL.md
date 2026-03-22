---
name: shopify-multi-env-setup
description: |
  Configure Shopify apps across development, staging, and production environments
  with separate stores, API credentials, and app instances.
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

```bash
# .env.development (git-ignored)
SHOPIFY_API_KEY=dev_api_key
SHOPIFY_API_SECRET=dev_api_secret
SHOPIFY_STORE=dev-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_dev_token
SHOPIFY_APP_URL=https://localhost:3000
SHOPIFY_API_VERSION=2024-10
NODE_ENV=development

# .env.staging (git-ignored)
SHOPIFY_API_KEY=staging_api_key
SHOPIFY_API_SECRET=staging_api_secret
SHOPIFY_STORE=staging-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_staging_token
SHOPIFY_APP_URL=https://staging.your-app.com
SHOPIFY_API_VERSION=2024-10
NODE_ENV=staging

# .env.production (never on disk — use secret manager)
# All values stored in Vault / AWS Secrets Manager / GCP Secret Manager
```

### Step 3: Shopify CLI Configuration Per Environment

```toml
# shopify.app.dev.toml — development config
name = "My App (Dev)"
client_id = "dev_api_key"

[access_scopes]
scopes = "read_products,write_products,read_orders,write_orders"

[auth]
redirect_urls = ["https://localhost/auth/callback"]

[webhooks]
api_version = "2024-10"
```

```bash
# Switch between app configs
shopify app config use shopify.app.dev.toml
shopify app dev

shopify app config use shopify.app.toml  # production
shopify app deploy
```

### Step 4: Environment-Aware Configuration

```typescript
// src/config.ts
interface ShopifyEnvConfig {
  apiKey: string;
  apiSecret: string;
  appUrl: string;
  apiVersion: string;
  scopes: string[];
  environment: "development" | "staging" | "production";
  debug: boolean;
  sessionStorageType: "memory" | "sqlite" | "postgresql";
}

function getConfig(): ShopifyEnvConfig {
  const env = (process.env.NODE_ENV || "development") as ShopifyEnvConfig["environment"];

  const base = {
    apiKey: process.env.SHOPIFY_API_KEY!,
    apiSecret: process.env.SHOPIFY_API_SECRET!,
    appUrl: process.env.SHOPIFY_APP_URL!,
    apiVersion: process.env.SHOPIFY_API_VERSION || "2024-10",
    scopes: (process.env.SHOPIFY_SCOPES || "read_products").split(","),
    environment: env,
  };

  const envOverrides: Record<string, Partial<ShopifyEnvConfig>> = {
    development: {
      debug: true,
      sessionStorageType: "sqlite",
    },
    staging: {
      debug: false,
      sessionStorageType: "postgresql",
    },
    production: {
      debug: false,
      sessionStorageType: "postgresql",
    },
  };

  return { ...base, ...envOverrides[env] } as ShopifyEnvConfig;
}
```

### Step 5: Environment Guards

```typescript
// Prevent dangerous operations outside production
function requireProduction(operation: string): void {
  if (process.env.NODE_ENV !== "production") {
    console.log(`[DEV] ${operation} — would execute in production`);
    return;
  }
}

function blockInProduction(operation: string): void {
  if (process.env.NODE_ENV === "production") {
    throw new Error(
      `Operation "${operation}" is blocked in production. ` +
      `Use staging or development environment.`
    );
  }
}

// Example: prevent test data seeding in production
async function seedTestProducts() {
  blockInProduction("seedTestProducts");
  // ... seeding logic
}

// Example: ensure billing only runs in production
async function activateBilling(session: Session) {
  requireProduction("activateBilling");
  // ... billing logic
}
```

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

## Next Steps

For observability setup, see `shopify-observability`.
