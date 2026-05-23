# Environment Configuration Examples

## Configuration Structure

```
config/
  retellai/
    base.ts           # Shared defaults
    development.ts    # Dev overrides
    staging.ts        # Staging overrides
    production.ts     # Prod overrides
    index.ts          # Environment resolver
```

## Base Configuration

```typescript
// config/retellai/base.ts
export const baseConfig = {
  timeout: 30000,
  maxRetries: 3,
  cache: {
    enabled: true,
    ttlSeconds: 300,
  },
};
```

## Environment-Specific Configs

```typescript
// config/retellai/development.ts
import { baseConfig } from "./base";

export const developmentConfig = {
  ...baseConfig,
  apiKey: process.env.RETELL_API_KEY_DEV,
  debug: true,
  cache: { enabled: false, ttlSeconds: 60 },
};

// config/retellai/staging.ts
import { baseConfig } from "./base";

export const stagingConfig = {
  ...baseConfig,
  apiKey: process.env.RETELL_API_KEY_STAGING,
  debug: false,
};

// config/retellai/production.ts
import { baseConfig } from "./base";

export const productionConfig = {
  ...baseConfig,
  apiKey: process.env.RETELL_API_KEY_PROD,
  debug: false,
  timeout: 60000,
  maxRetries: 5,
  cache: { enabled: true, ttlSeconds: 600 },
};
```

## Environment Resolver

```typescript
// config/retellai/index.ts
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

export function getRetellAIConfig() {
  const env = detectEnvironment();
  const config = configs[env];

  if (!config.apiKey) {
    throw new Error(`RETELL_API_KEY not set for environment: ${env}`);
  }

  return { ...config, environment: env };
}
```

## Secret Management

```bash
# Local development (.env.local - git-ignored)
RETELL_API_KEY_DEV=your-dev-key

# GitHub Actions
# Settings > Environments > staging/production > Secrets
# Add RETELL_API_KEY_STAGING and RETELL_API_KEY_PROD

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name retellai/production/api-key \
  --secret-string "your-prod-key"

# GCP Secret Manager
echo -n "your-prod-key" | gcloud secrets create retellai-api-key-prod --data-file=-
```

## CI/CD Workflow

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      RETELL_API_KEY_STAGING: ${{ secrets.RETELL_API_KEY_STAGING }}

  deploy-production:
    environment: production
    env:
      RETELL_API_KEY_PROD: ${{ secrets.RETELL_API_KEY_PROD }}
```

## Startup Validation

```typescript
import { z } from "zod";

const configSchema = z.object({
  apiKey: z.string().min(1, "RETELL_API_KEY is required"),
  environment: z.enum(["development", "staging", "production"]),
  timeout: z.number().positive(),
});

const config = configSchema.parse(getRetellAIConfig());
```
