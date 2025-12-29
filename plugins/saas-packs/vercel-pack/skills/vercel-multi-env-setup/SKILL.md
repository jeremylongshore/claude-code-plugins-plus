---
name: vercel-multi-env-setup
description: |
  Configure Vercel across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Vercel configurations.
  Trigger with phrases like "vercel environments", "vercel staging",
  "vercel dev prod", "vercel environment setup", "vercel config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Multi-Environment Setup

## Overview
Configure Vercel across development, staging, and production environments.

## Prerequisites
- Separate Vercel accounts or API keys per environment
- Secret management solution (Vault, AWS Secrets Manager, etc.)
- CI/CD pipeline with environment variables
- Environment detection in application

## Environment Strategy

| Environment | Purpose | API Keys | Data |
|-------------|---------|----------|------|
| Development | Local dev | Test keys | Sandbox |
| Staging | Pre-prod validation | Staging keys | Test data |
| Production | Live traffic | Production keys | Real data |

## Configuration Structure

```
config/
├── vercel/
│   ├── base.json           # Shared config
│   ├── development.json    # Dev overrides
│   ├── staging.json        # Staging overrides
│   └── production.json     # Prod overrides
```

### base.json
```json
{
  "timeout": 30000,
  "retries": 3,
  "cache": {
    "enabled": true,
    "ttlSeconds": 60
  }
}
```

### development.json
```json
{
  "apiKey": "${VERCEL_API_KEY}",
  "baseUrl": "https://api-sandbox.vercel.com",
  "debug": true,
  "cache": {
    "enabled": false
  }
}
```

### staging.json
```json
{
  "apiKey": "${VERCEL_API_KEY_STAGING}",
  "baseUrl": "https://api-staging.vercel.com",
  "debug": false
}
```

### production.json
```json
{
  "apiKey": "${VERCEL_API_KEY_PROD}",
  "baseUrl": "https://api.vercel.com",
  "debug": false,
  "retries": 5
}
```

## Environment Detection

```typescript
// src/vercel/config.ts
import baseConfig from '../../config/vercel/base.json';

type Environment = 'development' | 'staging' | 'production';

function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || 'development';
  const validEnvs: Environment[] = ['development', 'staging', 'production'];
  return validEnvs.includes(env as Environment)
    ? (env as Environment)
    : 'development';
}

export function getVercelConfig() {
  const env = detectEnvironment();
  const envConfig = require(`../../config/vercel/${env}.json`);

  return {
    ...baseConfig,
    ...envConfig,
    environment: env,
  };
}
```

## Secret Management by Environment

### Local Development
```bash
# .env.local (git-ignored)
VERCEL_API_KEY=sk_test_dev_***
```

### CI/CD (GitHub Actions)
```yaml
env:
  VERCEL_API_KEY: ${{ secrets.VERCEL_API_KEY_${{ matrix.environment }} }}
```

### Production (Vault/Secrets Manager)
```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id vercel/production/api-key

# GCP Secret Manager
gcloud secrets versions access latest --secret=vercel-api-key

# HashiCorp Vault
vault kv get -field=api_key secret/vercel/production
```

## Environment Isolation

```typescript
// Prevent production operations in non-prod
function guardProductionOperation(operation: string): void {
  const config = getVercelConfig();

  if (config.environment !== 'production') {
    console.warn(`[vercel] ${operation} blocked in ${config.environment}`);
    throw new Error(`${operation} only allowed in production`);
  }
}

// Usage
async function deleteAllData() {
  guardProductionOperation('deleteAllData');
  // Dangerous operation here
}
```

## Feature Flags by Environment

```typescript
const featureFlags: Record<Environment, Record<string, boolean>> = {
  development: {
    newFeature: true,
    betaApi: true,
  },
  staging: {
    newFeature: true,
    betaApi: false,
  },
  production: {
    newFeature: false,
    betaApi: false,
  },
};
```

## Instructions

### Step 1: Create Config Structure
Set up the base and per-environment configuration files.

### Step 2: Implement Environment Detection
Add logic to detect and load environment-specific config.

### Step 3: Configure Secrets
Store API keys securely using your secret management solution.

### Step 4: Add Environment Guards
Implement safeguards for production-only operations.

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
| Config merge fails | Invalid JSON | Validate config files |
| Production guard triggered | Wrong environment | Check NODE_ENV value |

## Examples

### Quick Environment Check
```typescript
const env = getVercelConfig();
console.log(`Running in ${env.environment} with ${env.baseUrl}`);
```

## Resources
- [Vercel Environments Guide](https://vercel.com/docs/environments)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps
For observability setup, see `vercel-observability`.