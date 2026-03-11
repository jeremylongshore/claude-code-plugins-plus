---
name: replit-multi-env-setup
description: |
  Configure Replit across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Replit configurations.
  Trigger with phrases like "replit environments", "replit staging",
  "replit dev prod", "replit environment setup", "replit config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Multi-Environment Setup

## Overview
Configure Replit across development, staging, and production environments with isolated API keys, environment-specific settings, and proper secret management. Each environment gets its own credentials and configuration to prevent cross-environment data leakage.

## Prerequisites
- Separate Replit API keys per environment
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
  replit/
    base.ts           # Shared defaults
    development.ts    # Dev overrides
    staging.ts        # Staging overrides
    production.ts     # Prod overrides
    index.ts          # Environment resolver
```

### Step 2: Base Configuration
```typescript
// config/replit/base.ts
export const baseConfig = {
  timeout: 30000,  # 30000: 30 seconds in ms
  maxRetries: 3,
  cache: {
    enabled: true,
    ttlSeconds: 300,  # 300: timeout: 5 minutes
  },
};
```

### Step 3: Environment-Specific Configs
```typescript
// config/replit/development.ts
import { baseConfig } from "./base";

export const developmentConfig = {
  ...baseConfig,
  apiKey: process.env.REPLIT_TOKEN_DEV,
  debug: true,
  cache: { enabled: false, ttlSeconds: 60 },
};

// config/replit/staging.ts
import { baseConfig } from "./base";

export const stagingConfig = {
  ...baseConfig,
  apiKey: process.env.REPLIT_TOKEN_STAGING,
  debug: false,
};

// config/replit/production.ts
import { baseConfig } from "./base";

export const productionConfig = {
  ...baseConfig,
  apiKey: process.env.REPLIT_TOKEN_PROD,
  debug: false,
  timeout: 60000,  # 60000: 1 minute in ms
  maxRetries: 5,
  cache: { enabled: true, ttlSeconds: 600 },  # 600: timeout: 10 minutes
};
```

### Step 4: Environment Resolver
```typescript
// config/replit/index.ts
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

export function getReplitConfig() {
  const env = detectEnvironment();
  const config = configs[env];

  if (!config.apiKey) {
    throw new Error(`REPLIT_TOKEN not set for environment: ${env}`);
  }

  return { ...config, environment: env };
}
```

### Step 5: Secret Management
```bash
# Local development (.env.local - git-ignored)
REPLIT_TOKEN_DEV=your-dev-key

# GitHub Actions
# Settings > Environments > staging/production > Secrets
# Add REPLIT_TOKEN_STAGING and REPLIT_TOKEN_PROD

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name replit/production/api-key \
  --secret-string "your-prod-key"

# GCP Secret Manager
echo -n "your-prod-key" | gcloud secrets create replit-api-key-prod --data-file=-
```

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      REPLIT_TOKEN_STAGING: ${{ secrets.REPLIT_TOKEN_STAGING }}

  deploy-production:
    environment: production
    env:
      REPLIT_TOKEN_PROD: ${{ secrets.REPLIT_TOKEN_PROD }}
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
const config = getReplitConfig();
console.log(`Running in ${config.environment}`);
console.log(`Cache enabled: ${config.cache.enabled}`);
```

### Startup Validation
```typescript
import { z } from "zod";

const configSchema = z.object({
  apiKey: z.string().min(1, "REPLIT_TOKEN is required"),
  environment: z.enum(["development", "staging", "production"]),
  timeout: z.number().positive(),
});

const config = configSchema.parse(getReplitConfig());
```

## Resources
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Replit Secrets](https://docs.replit.com/programming-ide/storing-sensitive-information)

## Next Steps
For deployment, see `replit-deploy-integration`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale