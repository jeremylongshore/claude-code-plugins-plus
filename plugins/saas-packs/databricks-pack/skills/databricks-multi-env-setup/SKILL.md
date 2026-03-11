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
---

# Databricks Multi-Environment Setup

## Overview
Configure Databricks across development, staging, and production environments with isolated API keys, environment-specific settings, and proper secret management. Each environment gets its own credentials and configuration to prevent cross-environment data leakage.

## Prerequisites
- Separate Databricks API keys per environment
- Secret management solution (environment variables, Vault, or cloud secrets)
- CI/CD pipeline with environment-aware deployment
- Application with environment detection logic

## Environment Strategy

| Environment | Purpose | API Key Source | Settings |
|-------------|---------|---------------|----------|
| Development | Local development | `.env.local` | Debug enabled, relaxed limits |
| Staging | Pre-production testing | CI/CD secrets | Production-like settings |
| Production | Live traffic | Secret manager | Optimized, hardened |

## Instructions

### Step 1: Configuration Structure
```
config/
  databricks/
    base.ts           # Shared defaults
    development.ts    # Dev overrides
    staging.ts        # Staging overrides
    production.ts     # Prod overrides
    index.ts          # Environment resolver
```

### Step 2: Base Configuration
```typescript
// config/databricks/base.ts
export const baseConfig = {
  timeout: 30000,
  maxRetries: 3,
  cache: {
    enabled: true,
    ttlSeconds: 300,
  },
};
```

### Step 3: Environment-Specific Configs
```typescript
// config/databricks/development.ts
import { baseConfig } from "./base";

export const developmentConfig = {
  ...baseConfig,
  apiKey: process.env.DATABRICKS_TOKEN_DEV,
  debug: true,
  cache: { enabled: false, ttlSeconds: 60 },
};

// config/databricks/staging.ts
import { baseConfig } from "./base";

export const stagingConfig = {
  ...baseConfig,
  apiKey: process.env.DATABRICKS_TOKEN_STAGING,
  debug: false,
};

// config/databricks/production.ts
import { baseConfig } from "./base";

export const productionConfig = {
  ...baseConfig,
  apiKey: process.env.DATABRICKS_TOKEN_PROD,
  debug: false,
  timeout: 60000,
  maxRetries: 5,
  cache: { enabled: true, ttlSeconds: 600 },
};
```

### Step 4: Environment Resolver
```typescript
// config/databricks/index.ts
import { developmentConfig } from "./development";
import { stagingConfig } from "./staging";
import { productionConfig } from "./production";

type Environment = "development" | "staging" | "production";

const configs = {
  development: developmentConfig,
  staging: stagingConfig,
  production: productionConfig,
};

export function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || "development";
  if (env === "production") return "production";
  if (env === "staging" || process.env.VERCEL_ENV === "preview") return "staging";
  return "development";
}

export function getDatabricksConfig() {
  const env = detectEnvironment();
  const config = configs[env];

  if (!config.apiKey) {
    throw new Error(`DATABRICKS_TOKEN not set for environment: ${env}`);
  }

  return { ...config, environment: env };
}
```

### Step 5: Secret Management
```bash
# Local development (.env.local - git-ignored)
DATABRICKS_TOKEN_DEV=your-dev-key

# GitHub Actions
# Settings > Environments > staging/production > Secrets
# Add DATABRICKS_TOKEN_STAGING and DATABRICKS_TOKEN_PROD

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name databricks/production/api-key \
  --secret-string "your-prod-key"

# GCP Secret Manager
echo -n "your-prod-key" | gcloud secrets create databricks-api-key-prod --data-file=-
```

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      DATABRICKS_TOKEN_STAGING: ${{ secrets.DATABRICKS_TOKEN_STAGING }}

  deploy-production:
    environment: production
    env:
      DATABRICKS_TOKEN_PROD: ${{ secrets.DATABRICKS_TOKEN_PROD }}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Missing NODE_ENV | Set environment variable in deployment |
| Secret not found | Wrong secret path | Verify secret manager configuration |
| Cross-env data leak | Shared API key | Use separate keys per environment |
| Config validation fail | Missing field | Add startup validation with Zod schema |

## Examples

### Quick Environment Check
```typescript
const config = getDatabricksConfig();
console.log(`Running in ${config.environment}`);
console.log(`Cache enabled: ${config.cache.enabled}`);
```

### Startup Validation
```typescript
import { z } from "zod";

const configSchema = z.object({
  apiKey: z.string().min(1, "DATABRICKS_TOKEN is required"),
  environment: z.enum(["development", "staging", "production"]),
  timeout: z.number().positive(),
});

const config = configSchema.parse(getDatabricksConfig());
```

## Resources
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles)
- [Databricks Environments](https://docs.databricks.com/dev-tools/bundles/settings.html)

## Next Steps
For deployment, see `databricks-deploy-integration`.
