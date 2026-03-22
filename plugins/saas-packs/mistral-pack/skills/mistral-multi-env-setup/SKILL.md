---
name: mistral-multi-env-setup
description: |
  Configure Mistral AI across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Mistral AI configurations.
  Trigger with phrases like "mistral environments", "mistral staging",
  "mistral dev prod", "mistral environment setup".
allowed-tools: Read, Write, Edit, Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, deployment]

---
# Mistral AI Multi-Environment Setup

## Overview
Configure Mistral AI across development, staging, and production with per-environment API keys, model selection, rate limits, and secret management via GCP Secret Manager, AWS Secrets Manager, or Vault.

## Prerequisites
- Separate Mistral API keys per environment (from [console.mistral.ai](https://console.mistral.ai/))
- Secret management solution configured
- CI/CD pipeline with environment variables

## Environment Strategy

| Environment | API Key | Default Model | Rate Limit | Cache |
|-------------|---------|---------------|------------|-------|
| Development | Dev key (low quota) | mistral-small-latest | 10 RPM | Off |
| Staging | Staging key | Same as prod | 60 RPM | On |
| Production | Prod key (full quota) | Optimized per task | Full RPM | On |

## Instructions

### Step 1: Configuration Structure

```typescript
// config/mistral/base.ts
export interface MistralEnvConfig {
  apiKey: string;
  defaultModel: string;
  timeoutMs: number;
  maxRetries: number;
  debug: boolean;
  cache: { enabled: boolean; ttlMs: number };
  rateLimits: { rpm: number; tpm: number };
}

export const baseConfig: Omit<MistralEnvConfig, 'apiKey'> = {
  defaultModel: 'mistral-small-latest',
  timeoutMs: 30_000,
  maxRetries: 3,
  debug: false,
  cache: { enabled: true, ttlMs: 300_000 },
  rateLimits: { rpm: 60, tpm: 500_000 },
};
```

### Step 2: Per-Environment Configs

```typescript
// config/mistral/environments.ts
import { baseConfig, type MistralEnvConfig } from './base.js';

const configs: Record<string, Partial<MistralEnvConfig>> = {
  development: {
    debug: true,
    cache: { enabled: false, ttlMs: 60_000 },
    rateLimits: { rpm: 10, tpm: 100_000 },
  },
  staging: {
    cache: { enabled: true, ttlMs: 300_000 },
  },
  production: {
    timeoutMs: 60_000,
    maxRetries: 5,
    cache: { enabled: true, ttlMs: 600_000 },
  },
};

export function getMistralConfig(): MistralEnvConfig {
  const env = detectEnvironment();
  const envConfig = configs[env] ?? {};

  // API key sourced from environment
  const apiKeyVar = {
    development: 'MISTRAL_API_KEY_DEV',
    staging: 'MISTRAL_API_KEY_STAGING',
    production: 'MISTRAL_API_KEY',
  }[env] ?? 'MISTRAL_API_KEY';

  const apiKey = process.env[apiKeyVar] ?? process.env.MISTRAL_API_KEY;
  if (!apiKey) throw new Error(`Mistral API key not set for ${env} (expected ${apiKeyVar})`);

  return { ...baseConfig, ...envConfig, apiKey } as MistralEnvConfig;
}
```

### Step 3: Environment Detection

```typescript
type Environment = 'development' | 'staging' | 'production';

function detectEnvironment(): Environment {
  // Explicit override
  if (process.env.APP_ENV) return process.env.APP_ENV as Environment;

  // Platform-specific detection
  if (process.env.VERCEL_ENV === 'production') return 'production';
  if (process.env.VERCEL_ENV === 'preview') return 'staging';
  if (process.env.CLOUD_RUN_JOB) return 'production';
  if (process.env.K_SERVICE) return 'production';  // Cloud Run

  // NODE_ENV fallback
  if (process.env.NODE_ENV === 'production') return 'production';
  if (process.env.NODE_ENV === 'staging') return 'staging';

  return 'development';
}
```

### Step 4: Secret Management

**GCP Secret Manager**
```typescript
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

const sm = new SecretManagerServiceClient();

async function getMistralApiKey(env: string): Promise<string> {
  const [version] = await sm.accessSecretVersion({
    name: `projects/my-project/secrets/mistral-api-key-${env}/versions/latest`,
  });
  return version.payload?.data?.toString() ?? '';
}
```

**AWS Secrets Manager**
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

**GitHub Actions**
```yaml
jobs:
  deploy-staging:
    environment: staging
    env:
      MISTRAL_API_KEY_STAGING: ${{ secrets.MISTRAL_API_KEY_STAGING }}

  deploy-production:
    environment: production
    env:
      MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY_PROD }}
```

### Step 5: Environment Isolation Guards

```typescript
function requireEnvironment(required: Environment, operation: string): void {
  const current = detectEnvironment();
  if (current !== required) {
    throw new Error(`"${operation}" requires ${required} but running in ${current}`);
  }
}

// Protect dangerous operations
async function createFineTuningJob(params: any) {
  requireEnvironment('production', 'createFineTuningJob');
  // ... fine-tuning logic
}

// Prevent production data in dev
async function processUserData(userId: string) {
  const env = detectEnvironment();
  if (env === 'development') {
    console.warn('Using test data in development');
    userId = 'test-user-001';
  }
  // ... processing logic
}
```

### Step 6: Feature Flags by Environment

```typescript
interface FeatureFlags {
  useAgentsAPI: boolean;
  enableBatchProcessing: boolean;
  enableVisionModels: boolean;
  maxConcurrentRequests: number;
}

const FLAGS: Record<Environment, FeatureFlags> = {
  development: {
    useAgentsAPI: true,
    enableBatchProcessing: true,
    enableVisionModels: true,
    maxConcurrentRequests: 2,
  },
  staging: {
    useAgentsAPI: true,
    enableBatchProcessing: true,
    enableVisionModels: true,
    maxConcurrentRequests: 5,
  },
  production: {
    useAgentsAPI: false,  // Gradual rollout
    enableBatchProcessing: true,
    enableVisionModels: true,
    maxConcurrentRequests: 10,
  },
};

export function getFlags(): FeatureFlags {
  return FLAGS[detectEnvironment()];
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Missing `APP_ENV` | Set explicitly in deployment config |
| Secret not found | Wrong secret path | Verify secret manager and IAM permissions |
| Cross-env data leak | Missing guards | Add `requireEnvironment()` checks |
| Config mismatch | Env var naming | Use consistent naming convention |

## Resources
- [GCP Secret Manager](https://cloud.google.com/secret-manager)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [12-Factor App Config](https://12factor.net/config)

## Output
- Multi-environment config with type-safe overrides
- Environment detection for Vercel, Cloud Run, and K8s
- Secret management integration (GCP, AWS, GitHub Actions)
- Environment isolation guards
- Feature flags per environment
