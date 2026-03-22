---
name: exa-multi-env-setup
description: |
  Configure Exa across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Exa configurations.
  Trigger with phrases like "exa environments", "exa staging",
  "exa dev prod", "exa environment setup", "exa config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, exa]
---

# Exa Multi-Environment Setup

## Overview
Configure Exa across development, staging, and production environments.

## Prerequisites
- Separate Exa accounts or API keys per environment
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
├── exa/
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
  "apiKey": "${EXA_API_KEY}",
  "baseUrl": "https://api-sandbox.exa.com",
  "debug": true,
  "cache": {
    "enabled": false
  }
}
```

### staging.json
```json
{
  "apiKey": "${EXA_API_KEY_STAGING}",
  "baseUrl": "https://api-staging.exa.com",
  "debug": false
}
```

### production.json
```json
{
  "apiKey": "${EXA_API_KEY_PROD}",
  "baseUrl": "https://api.exa.com",
  "debug": false,
  "retries": 5
}
```

## Environment Detection

```typescript
// src/exa/config.ts
import baseConfig from '../../config/exa/base.json';

type Environment = 'development' | 'staging' | 'production';

function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || 'development';
  const validEnvs: Environment[] = ['development', 'staging', 'production'];
  return validEnvs.includes(env as Environment)
    ? (env as Environment)
    : 'development';
}

export function getExaConfig() {
  const env = detectEnvironment();
  const envConfig = require(`../../config/exa/${env}.json`);

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
EXA_API_KEY=sk_test_dev_***
```

### CI/CD (GitHub Actions)
```yaml
env:
  EXA_API_KEY: ${{ secrets.EXA_API_KEY_${{ matrix.environment }} }}
```

### Production (Vault/Secrets Manager)
```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id exa/production/api-key

# GCP Secret Manager
gcloud secrets versions access latest --secret=exa-api-key

# HashiCorp Vault
vault kv get -field=api_key secret/exa/production
```

## Environment Isolation

```typescript
// Prevent production operations in non-prod
function guardProductionOperation(operation: string): void {
  const config = getExaConfig();

  if (config.environment !== 'production') {
    console.warn(`[exa] ${operation} blocked in ${config.environment}`);
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
const env = getExaConfig();
console.log(`Running in ${env.environment} with ${env.baseUrl}`);
```

## Resources
- [Exa Environments Guide](https://docs.exa.com/environments)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps
For observability setup, see `exa-observability`.