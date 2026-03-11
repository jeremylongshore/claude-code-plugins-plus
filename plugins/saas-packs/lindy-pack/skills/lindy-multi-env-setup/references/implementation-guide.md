# Lindy Multi Env Setup - Implementation Guide

# Lindy AI Multi-Environment Setup

## Overview
Configure Lindy AI across development, staging, and production environments with isolated API keys, environment-specific settings, and proper secret management. Each environment gets its own credentials and configuration to prevent cross-environment data leakage.

## Prerequisites
- Separate Lindy AI API keys per environment
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
  lindy/
    base.ts           # Shared defaults
    development.ts    # Dev overrides
    staging.ts        # Staging overrides
    production.ts     # Prod overrides
    index.ts          # Environment resolver
```

### Step 2: Base Configuration
```typescript
// config/lindy/base.ts
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
// config/lindy/development.ts
import { baseConfig } from "./base";

export const developmentConfig = {
  ...baseConfig,
  apiKey: process.env.LINDY_API_KEY_DEV,
  debug: true,
  cache: { enabled: false, ttlSeconds: 60 },
};

// config/lindy/staging.ts
import { baseConfig } from "./base";

export const stagingConfig = {
  ...baseConfig,
  apiKey: process.env.LINDY_API_KEY_STAGING,
  debug: false,
};

// config/lindy/production.ts
import { baseConfig } from "./base";

export const productionConfig = {
  ...baseConfig,
  apiKey: process.env.LINDY_API_KEY_PROD,
  debug: false,
  timeout: 60000,
  maxRetries: 5,
  cache: { enabled: true, ttlSeconds: 600 },
};
```

### Step 4: Environment Resolver
```typescript
// config/lindy/index.ts
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

export function getLindyAIConfig() {
  const env = detectEnvironment();
  const config = configs[env];

  if (!config.apiKey) {
    throw new Error(`LINDY_API_KEY not set for environment: ${env}`);
  }

  return { ...config, environment: env };
}
```

### Step 5: Secret Management
```bash
# Local development (.env.local - git-ignored)
LINDY_API_KEY_DEV=your-dev-key

# GitHub Actions
# Settings > Environments > staging/production > Secrets
# Add LINDY_API_KEY_STAGING and LINDY_API_KEY_PROD

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name lindy/production/api-key \
  --secret-string "your-prod-key"

# GCP Secret Manager
echo -n "your-prod-key" | gcloud secrets create lindy-api-key-prod --data-file=-
```

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      LINDY_API_KEY_STAGING: ${{ secrets.LINDY_API_KEY_STAGING }}

  deploy-production:
    environment: production
    env:
      LINDY_API_KEY_PROD: ${{ secrets.LINDY_API_KEY_PROD }}
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
const config = getLindyAIConfig();
console.log(`Running in ${config.environment}`);
console.log(`Cache enabled: ${config.cache.enabled}`);
```

### Startup Validation
```typescript
import { z } from "zod";

const configSchema = z.object({
  apiKey: z.string().min(1, "LINDY_API_KEY is required"),
  environment: z.enum(["development", "staging", "production"]),
  timeout: z.number().positive(),
});

const config = configSchema.parse(getLindyAIConfig());
```

## Resources
- [Lindy AI Documentation](https://docs.lindy.ai)
- [Lindy API Reference](https://docs.lindy.ai/api)

## Next Steps
For deployment, see `lindy-deploy-integration`.
