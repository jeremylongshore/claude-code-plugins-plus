---
name: supabase-multi-env-setup
description: |
  Supabase multi-environment setup for dev/staging/prod configuration.
  Use when setting up Supabase across multiple environments.
  Trigger with phrases like "supabase environments", "supabase staging",
  "supabase multi-env", "supabase dev setup".
allowed-tools: Read, Write, Edit, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Multi-Environment Setup

## Overview
Configure Supabase across development, staging, and production environments.

## Prerequisites
- supabase-install-auth completed
- Access to Supabase dashboard for all environments
- Environment variable management system (dotenv, Vault, etc.)
- Separate API keys per environment

## Instructions

### Step 1: Environment Configuration Structure

```
config/
├── supabase.development.json
├── supabase.staging.json
├── supabase.production.json
└── supabase.base.json       # Shared settings
```

### Step 2: Environment-Specific Config

```typescript
// config/supabase.ts
import { merge } from 'lodash';

interface SupabaseConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  baseUrl: string;
  timeout: number;
  retries: number;
  debug: boolean;
}

const baseConfig = require('./supabase.base.json');

export function getSupabaseConfig(): SupabaseConfig {
  const env = process.env.NODE_ENV || 'development';
  const envConfig = require(`./supabase.${env}.json`);

  return merge({}, baseConfig, envConfig, {
    apiKey: process.env.SUPABASE_API_KEY!,
  });
}
```

### Step 3: Environment Variables

```bash
# .env.development
SUPABASE_API_KEY=sk_dev_***
SUPABASE_ENV=development
SUPABASE_DEBUG=true

# .env.staging
SUPABASE_API_KEY=sk_staging_***
SUPABASE_ENV=staging
SUPABASE_DEBUG=true

# .env.production
SUPABASE_API_KEY=sk_live_***
SUPABASE_ENV=production
SUPABASE_DEBUG=false
```

### Step 4: Environment Detection

```typescript
function getSupabaseEnvironment(): 'development' | 'staging' | 'production' {
  // Check explicit env var first
  const explicit = process.env.SUPABASE_ENV;
  if (explicit) return explicit as any;

  // Fall back to NODE_ENV
  switch (process.env.NODE_ENV) {
    case 'production': return 'production';
    case 'staging': return 'staging';
    default: return 'development';
  }
}
```

## Output
- Isolated Supabase configurations per environment
- Environment-specific API keys and settings
- Debug logging enabled for non-production
- Consistent configuration loading across codebase

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Wrong API key for env | Mismatched key/environment | Verify API key prefix matches environment |
| Config file not found | Missing environment config | Create config file for environment |
| Environment detection fail | NODE_ENV not set | Set NODE_ENV or SUPABASE_ENV explicitly |
| Cross-env data access | Using prod key in staging | Audit API key usage, use key validation |

## Examples

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: supabase-config
data:
  SUPABASE_ENV: "production"
  SUPABASE_BASE_URL: "https://api.supabase.com"
---
apiVersion: v1
kind: Secret
metadata:
  name: supabase-secrets
stringData:
  SUPABASE_API_KEY: "sk_live_***"
```

### GitHub Actions per Environment

```yaml
jobs:
  deploy-staging:
    environment: staging
    env:
      SUPABASE_API_KEY: ${{ secrets.SUPABASE_API_KEY_STAGING }}

  deploy-production:
    environment: production
    needs: deploy-staging
    env:
      SUPABASE_API_KEY: ${{ secrets.SUPABASE_API_KEY_PROD }}
```

## Resources
- [Supabase Environments Guide](https://supabase.com/docs/environments)
- [API Key Management](https://supabase.com/docs/api-keys)
- [Configuration Best Practices](https://supabase.com/docs/configuration)

## Next Steps
For observability across environments, see `supabase-observability`.