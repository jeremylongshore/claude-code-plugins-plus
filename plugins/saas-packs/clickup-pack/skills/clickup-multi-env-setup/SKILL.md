---
name: clickup-multi-env-setup
description: |
  Configure ClickUp across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific ClickUp configurations.
  Trigger with phrases like "clickup environments", "clickup staging",
  "clickup dev prod", "clickup environment setup", "clickup config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickup]
---

# ClickUp Multi-Environment Setup

## Overview
Configure ClickUp across development, staging, and production environments.

## Prerequisites
- Separate ClickUp accounts or API keys per environment
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
├── clickup/
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
  "apiKey": "${CLICKUP_API_KEY}",
  "baseUrl": "https://api-sandbox.clickup.com",
  "debug": true,
  "cache": {
    "enabled": false
  }
}
```

### staging.json
```json
{
  "apiKey": "${CLICKUP_API_KEY_STAGING}",
  "baseUrl": "https://api-staging.clickup.com",
  "debug": false
}
```

### production.json
```json
{
  "apiKey": "${CLICKUP_API_KEY_PROD}",
  "baseUrl": "https://api.clickup.com",
  "debug": false,
  "retries": 5
}
```

## Environment Detection

```typescript
// src/clickup/config.ts
import baseConfig from '../../config/clickup/base.json';

type Environment = 'development' | 'staging' | 'production';

function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || 'development';
  const validEnvs: Environment[] = ['development', 'staging', 'production'];
  return validEnvs.includes(env as Environment)
    ? (env as Environment)
    : 'development';
}

export function getClickUpConfig() {
  const env = detectEnvironment();
  const envConfig = require(`../../config/clickup/${env}.json`);

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
CLICKUP_API_KEY=sk_test_dev_***
```

### CI/CD (GitHub Actions)
```yaml
env:
  CLICKUP_API_KEY: ${{ secrets.CLICKUP_API_KEY_${{ matrix.environment }} }}
```

### Production (Vault/Secrets Manager)
```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id clickup/production/api-key

# GCP Secret Manager
gcloud secrets versions access latest --secret=clickup-api-key

# HashiCorp Vault
vault kv get -field=api_key secret/clickup/production
```

## Environment Isolation

```typescript
// Prevent production operations in non-prod
function guardProductionOperation(operation: string): void {
  const config = getClickUpConfig();

  if (config.environment !== 'production') {
    console.warn(`[clickup] ${operation} blocked in ${config.environment}`);
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
const env = getClickUpConfig();
console.log(`Running in ${env.environment} with ${env.baseUrl}`);
```

## Resources
- [ClickUp Environments Guide](https://docs.clickup.com/environments)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps
For observability setup, see `clickup-observability`.