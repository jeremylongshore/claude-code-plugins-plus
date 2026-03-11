---
name: langchain-multi-env-setup
description: |
  Configure LangChain multi-environment setup for dev/staging/prod.
  Use when managing multiple environments, configuring environment-specific settings,
  or implementing environment promotion workflows.
  Trigger with phrases like "langchain environments", "langchain staging",
  "langchain dev prod", "environment configuration", "langchain env setup".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# LangChain Multi-Environment Setup

## Overview
Configure LangChain across development, staging, and production environments with isolated API keys, environment-specific settings, and proper secret management. Each environment gets its own credentials and configuration to prevent cross-environment data leakage.

## Prerequisites
- Separate LangChain API keys per environment
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
  langchain/
    base.ts           # Shared defaults
    development.ts    # Dev overrides
    staging.ts        # Staging overrides
    production.ts     # Prod overrides
    index.ts          # Environment resolver
```

### Step 2: Base Configuration
```typescript
// config/langchain/base.ts
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
// config/langchain/development.ts
import { baseConfig } from "./base";

export const developmentConfig = {
  ...baseConfig,
  apiKey: process.env.OPENAI_API_KEY_DEV,
  debug: true,
  cache: { enabled: false, ttlSeconds: 60 },
};

// config/langchain/staging.ts
import { baseConfig } from "./base";

export const stagingConfig = {
  ...baseConfig,
  apiKey: process.env.OPENAI_API_KEY_STAGING,
  debug: false,
};

// config/langchain/production.ts
import { baseConfig } from "./base";

export const productionConfig = {
  ...baseConfig,
  apiKey: process.env.OPENAI_API_KEY_PROD,
  debug: false,
  timeout: 60000,
  maxRetries: 5,
  cache: { enabled: true, ttlSeconds: 600 },
};
```

### Step 4: Environment Resolver
```typescript
// config/langchain/index.ts
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

export function getLangChainConfig() {
  const env = detectEnvironment();
  const config = configs[env];

  if (!config.apiKey) {
    throw new Error(`OPENAI_API_KEY not set for environment: ${env}`);
  }

  return { ...config, environment: env };
}
```

### Step 5: Secret Management
```bash
# Local development (.env.local - git-ignored)
OPENAI_API_KEY_DEV=your-dev-key

# GitHub Actions
# Settings > Environments > staging/production > Secrets
# Add OPENAI_API_KEY_STAGING and OPENAI_API_KEY_PROD

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name langchain/production/api-key \
  --secret-string "your-prod-key"

# GCP Secret Manager
echo -n "your-prod-key" | gcloud secrets create langchain-api-key-prod --data-file=-
```

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      OPENAI_API_KEY_STAGING: ${{ secrets.OPENAI_API_KEY_STAGING }}

  deploy-production:
    environment: production
    env:
      OPENAI_API_KEY_PROD: ${{ secrets.OPENAI_API_KEY_PROD }}
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
const config = getLangChainConfig();
console.log(`Running in ${config.environment}`);
console.log(`Cache enabled: ${config.cache.enabled}`);
```

### Startup Validation
```typescript
import { z } from "zod";

const configSchema = z.object({
  apiKey: z.string().min(1, "OPENAI_API_KEY is required"),
  environment: z.enum(["development", "staging", "production"]),
  timeout: z.number().positive(),
});

const config = configSchema.parse(getLangChainConfig());
```

## Resources
- [LangChain Configuration](https://python.langchain.com/docs/guides/deployment)
- [LangSmith Environments](https://docs.smith.langchain.com)

## Next Steps
For deployment, see `langchain-deploy-integration`.
