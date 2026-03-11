# Lokalise Multi Env Setup - Implementation Guide

Detailed implementation reference for the lokalise-multi-env-setup skill.

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
  lokalise/
    base.ts           # Shared defaults
    development.ts    # Dev overrides
    staging.ts        # Staging overrides
    production.ts     # Prod overrides
    index.ts          # Environment resolver
```

### Step 2: Base Configuration
```typescript
// config/lokalise/base.ts
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
// config/lokalise/development.ts
import { baseConfig } from "./base";

export const developmentConfig = {
  ...baseConfig,
  apiKey: process.env.LOKALISE_API_TOKEN_DEV,
  debug: true,
  cache: { enabled: false, ttlSeconds: 60 },
};

// config/lokalise/staging.ts
import { baseConfig } from "./base";

export const stagingConfig = {
  ...baseConfig,
  apiKey: process.env.LOKALISE_API_TOKEN_STAGING,
  debug: false,
};

// config/lokalise/production.ts
import { baseConfig } from "./base";

export const productionConfig = {
  ...baseConfig,
  apiKey: process.env.LOKALISE_API_TOKEN_PROD,
  debug: false,
  timeout: 60000,
  maxRetries: 5,
  cache: { enabled: true, ttlSeconds: 600 },
};
```

### Step 4: Environment Resolver
```typescript
// config/lokalise/index.ts
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

export function getLokaliseConfig() {
  const env = detectEnvironment();
  const config = configs[env];

  if (!config.apiKey) {
    throw new Error(`LOKALISE_API_TOKEN not set for environment: ${env}`);
  }

  return { ...config, environment: env };
}
```

### Step 5: Secret Management
```bash
# Local development (.env.local - git-ignored)
LOKALISE_API_TOKEN_DEV=your-dev-key

# GitHub Actions
# Settings > Environments > staging/production > Secrets
# Add LOKALISE_API_TOKEN_STAGING and LOKALISE_API_TOKEN_PROD

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name lokalise/production/api-key \
  --secret-string "your-prod-key"

# GCP Secret Manager
echo -n "your-prod-key" | gcloud secrets create lokalise-api-key-prod --data-file=-
```

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      LOKALISE_API_TOKEN_STAGING: ${{ secrets.LOKALISE_API_TOKEN_STAGING }}

  deploy-production:
    environment: production
    env:
      LOKALISE_API_TOKEN_PROD: ${{ secrets.LOKALISE_API_TOKEN_PROD }}
```

