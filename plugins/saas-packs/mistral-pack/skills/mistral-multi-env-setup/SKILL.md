---
name: mistral-multi-env-setup
description: |
  Configure Mistral AI across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Mistral AI configurations.
  Trigger with phrases like "mistral environments", "mistral staging",
  "mistral dev prod", "mistral environment setup", "mistral config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Multi-Environment Setup

## Overview
Configure Mistral AI across development, staging, and production environments.

## Prerequisites
- Separate Mistral AI API keys per environment
- Secret management solution (Vault, AWS Secrets Manager, GCP Secret Manager)
- CI/CD pipeline with environment variables
- Environment detection in application

## Environment Strategy

| Environment | Purpose | API Keys | Model Selection |
|-------------|---------|----------|-----------------|
| Development | Local dev | Test keys | mistral-small-latest |
| Staging | Pre-prod testing | Staging keys | Same as prod |
| Production | Live traffic | Production keys | Optimized selection |

## Instructions

### Step 1: Configuration Structure

```
config/
├── mistral/
│   ├── base.ts           # Shared configuration
│   ├── development.ts    # Dev overrides
│   ├── staging.ts        # Staging overrides
│   └── production.ts     # Prod overrides
```

### Step 2: Base Configuration

```typescript
// config/mistral/base.ts
export const baseConfig = {
  defaultModel: 'mistral-small-latest',
  timeout: 30000,  # 30000: 30 seconds in ms
  maxRetries: 3,
  cache: {
    enabled: true,
    ttlSeconds: 300,  # 300: timeout: 5 minutes
  },
  rateLimits: {
    requestsPerMinute: 60,
    tokensPerMinute: 500000,  # 500000 = configured value
  },
};
```

### Step 3: Environment-Specific Configs

```typescript
// config/mistral/development.ts
import { baseConfig } from './base';

export const developmentConfig = {
  ...baseConfig,
  apiKey: process.env.MISTRAL_API_KEY_DEV,
  debug: true,
  cache: {
    enabled: false, // Disable cache in dev for testing
    ttlSeconds: 60,
  },
  rateLimits: {
    requestsPerMinute: 10,
    tokensPerMinute: 100000,  # 100000 = configured value
  },
};
```

```typescript
// config/mistral/staging.ts
import { baseConfig } from './base';

export const stagingConfig = {
  ...baseConfig,
  apiKey: process.env.MISTRAL_API_KEY_STAGING,
  debug: false,
  cache: {
    enabled: true,
    ttlSeconds: 300,  # 300: timeout: 5 minutes
  },
};
```

```typescript
// config/mistral/production.ts
import { baseConfig } from './base';

export const productionConfig = {
  ...baseConfig,
  apiKey: process.env.MISTRAL_API_KEY_PROD,
  debug: false,
  timeout: 60000,  # 60000: 1 minute in ms
  maxRetries: 5,
  cache: {
    enabled: true,
    ttlSeconds: 600,  # 600: timeout: 10 minutes
  },
};
```

### Step 4: Environment Detection

```typescript
// config/mistral/index.ts
import { developmentConfig } from './development';
import { stagingConfig } from './staging';
import { productionConfig } from './production';

type Environment = 'development' | 'staging' | 'production';

const configs = {
  development: developmentConfig,
  staging: stagingConfig,
  production: productionConfig,
};

export function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || 'development';

  if (env === 'production') return 'production';
  if (env === 'staging' || process.env.VERCEL_ENV === 'preview') return 'staging';
  return 'development';
}

export function getMistralConfig() {
  const env = detectEnvironment();
  const config = configs[env];

  if (!config.apiKey) {
    throw new Error(`MISTRAL_API_KEY not set for environment: ${env}`);
  }

  return {
    ...config,
    environment: env,
  };
}
```

### Step 5: Secret Management

**Local Development (.env.local)**
```bash
# .env.local (git-ignored)
MISTRAL_API_KEY_DEV=your-dev-api-key
```

**GitHub Actions (secrets)**
```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      MISTRAL_API_KEY_STAGING: ${{ secrets.MISTRAL_API_KEY_STAGING }}

  deploy-production:
    environment: production
    env:
      MISTRAL_API_KEY_PROD: ${{ secrets.MISTRAL_API_KEY_PROD }}
```

**AWS Secrets Manager**
```bash
# Store secrets
aws secretsmanager create-secret \
  --name mistral/production/api-key \
  --secret-string "your-api-key"

# Retrieve in code
aws secretsmanager get-secret-value \
  --secret-id mistral/production/api-key
```

```typescript
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

const sm = new SecretsManager({ region: 'us-east-1' });

async function getMistralApiKey(env: string): Promise<string> {
  const { SecretString } = await sm.getSecretValue({
    SecretId: `mistral/${env}/api-key`,
  });
  return SecretString!;
}
```

**GCP Secret Manager**
```bash
# Store secret
echo -n "your-api-key" | gcloud secrets create mistral-api-key-prod --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding mistral-api-key-prod \
  --member="serviceAccount:your-sa@project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

```typescript
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

const client = new SecretManagerServiceClient();

async function getMistralApiKey(env: string): Promise<string> {
  const [version] = await client.accessSecretVersion({
    name: `projects/my-project/secrets/mistral-api-key-${env}/versions/latest`,
  });
  return version.payload?.data?.toString()!;
}
```

### Step 6: Environment Isolation

```typescript
// Prevent accidental cross-environment operations
function validateEnvironment(operation: string, requiredEnv: Environment): void {
  const currentEnv = detectEnvironment();

  if (currentEnv !== requiredEnv) {
    throw new Error(
      `Operation "${operation}" requires ${requiredEnv} but running in ${currentEnv}`
    );
  }
}

// Protect production-only operations
function requireProduction(operation: string): void {
  validateEnvironment(operation, 'production');
}

// Usage
async function deployModel() {
  requireProduction('deployModel');
  // Production-only code
}
```

### Step 7: Feature Flags by Environment

```typescript
interface FeatureFlags {
  useNewModel: boolean;
  enableFunctionCalling: boolean;
  maxConcurrentRequests: number;
}

const featureFlags: Record<Environment, FeatureFlags> = {
  development: {
    useNewModel: true,
    enableFunctionCalling: true,
    maxConcurrentRequests: 2,
  },
  staging: {
    useNewModel: true,
    enableFunctionCalling: true,
    maxConcurrentRequests: 5,
  },
  production: {
    useNewModel: false, // Gradual rollout
    enableFunctionCalling: true,
    maxConcurrentRequests: 10,
  },
};

export function getFeatureFlags(): FeatureFlags {
  const env = detectEnvironment();
  return featureFlags[env];
}
```

## Output
- Multi-environment config structure
- Environment detection logic
- Secure secret management
- Production safeguards enabled

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Missing NODE_ENV | Set environment variable |
| Secret not found | Wrong secret path | Verify secret manager config |
| Config validation | Invalid settings | Use Zod schema validation |
| Cross-env leak | Missing guards | Add environment checks |

## Examples

### Quick Environment Check
```typescript
const config = getMistralConfig();
console.log(`Running in ${config.environment}`);
console.log(`Model: ${config.defaultModel}`);
console.log(`Cache enabled: ${config.cache.enabled}`);
```

### Vercel Environment Detection
```typescript
function getVercelEnvironment(): Environment {
  const vercelEnv = process.env.VERCEL_ENV;

  if (vercelEnv === 'production') return 'production';
  if (vercelEnv === 'preview') return 'staging';
  return 'development';
}
```

## Resources
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps
For observability setup, see `mistral-observability`.