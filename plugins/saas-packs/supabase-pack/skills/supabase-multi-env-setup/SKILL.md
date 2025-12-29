---
name: supabase-multi-env-setup
description: |
  Supabase multi-environment configuration for dev/staging/prod.
  Trigger phrases: "supabase environments", "supabase staging",
  "supabase dev prod", "supabase environment setup".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Multi-Environment Setup

## Overview
Configure Supabase across development, staging, and production environments.

## Environment Strategy

| Environment | Purpose | API Keys | Data |
|-------------|---------|----------|------|
| Development | Local dev | Test keys | Sandbox |
| Staging | Pre-prod validation | Staging keys | Test data |
| Production | Live traffic | Production keys | Real data |

## Configuration Structure

```
config/
├── supabase/
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
  "apiKey": "${SUPABASE_API_KEY}",
  "baseUrl": "https://api-sandbox.supabase.com",
  "debug": true,
  "cache": {
    "enabled": false
  }
}
```

### staging.json
```json
{
  "apiKey": "${SUPABASE_API_KEY_STAGING}",
  "baseUrl": "https://api-staging.supabase.com",
  "debug": false
}
```

### production.json
```json
{
  "apiKey": "${SUPABASE_API_KEY_PROD}",
  "baseUrl": "https://api.supabase.com",
  "debug": false,
  "retries": 5
}
```

## Environment Detection

```typescript
// src/supabase/config.ts
import baseConfig from '../../config/supabase/base.json';

type Environment = 'development' | 'staging' | 'production';

function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || 'development';
  const validEnvs: Environment[] = ['development', 'staging', 'production'];
  return validEnvs.includes(env as Environment)
    ? (env as Environment)
    : 'development';
}

export function getSupabaseConfig() {
  const env = detectEnvironment();
  const envConfig = require(`../../config/supabase/${env}.json`);

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
SUPABASE_API_KEY=sk_test_dev_***
```

### CI/CD (GitHub Actions)
```yaml
env:
  SUPABASE_API_KEY: ${{ secrets.SUPABASE_API_KEY_${{ matrix.environment }} }}
```

### Production (Vault/Secrets Manager)
```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id supabase/production/api-key

# GCP Secret Manager
gcloud secrets versions access latest --secret=supabase-api-key

# HashiCorp Vault
vault kv get -field=api_key secret/supabase/production
```

## Environment Isolation

```typescript
// Prevent production operations in non-prod
function guardProductionOperation(operation: string): void {
  const config = getSupabaseConfig();

  if (config.environment !== 'production') {
    console.warn(`[supabase] ${operation} blocked in ${config.environment}`);
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

## Next Steps
For observability setup, see `supabase-observability`.