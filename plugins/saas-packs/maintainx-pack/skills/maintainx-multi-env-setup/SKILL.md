---
name: maintainx-multi-env-setup
description: |
  Configure multiple MaintainX environments (dev, staging, production).
  Use when setting up environment-specific configurations,
  managing multiple MaintainX accounts, or implementing environment promotion.
  Trigger with phrases like "maintainx environments", "maintainx staging",
  "maintainx dev prod", "maintainx multi-environment", "maintainx config".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Multi-Environment Setup

## Overview
Configure and manage multiple MaintainX environments for development, staging, and production with proper secret management and client isolation.

## Prerequisites
- Separate MaintainX accounts or organizations for each environment
- Secret management solution (environment variables, GCP Secret Manager, or AWS SSM)
- Node.js 18+

## Instructions

### Step 1: Environment Configuration

```typescript
// src/config/environments.ts

interface MaintainXEnvConfig {
  apiKey: string;
  orgId?: string;
  baseUrl: string;
  label: string;
  rateLimit: { requestsPerSecond: number };
}

type Environment = 'development' | 'staging' | 'production';

function getConfig(env: Environment): MaintainXEnvConfig {
  const configs: Record<Environment, () => MaintainXEnvConfig> = {
    development: () => ({
      apiKey: process.env.MAINTAINX_API_KEY_DEV!,
      orgId: process.env.MAINTAINX_ORG_ID_DEV,
      baseUrl: 'https://api.getmaintainx.com/v1',
      label: 'Development',
      rateLimit: { requestsPerSecond: 5 },
    }),
    staging: () => ({
      apiKey: process.env.MAINTAINX_API_KEY_STAGING!,
      orgId: process.env.MAINTAINX_ORG_ID_STAGING,
      baseUrl: 'https://api.getmaintainx.com/v1',
      label: 'Staging',
      rateLimit: { requestsPerSecond: 10 },
    }),
    production: () => ({
      apiKey: process.env.MAINTAINX_API_KEY_PROD!,
      orgId: process.env.MAINTAINX_ORG_ID_PROD,
      baseUrl: 'https://api.getmaintainx.com/v1',
      label: 'Production',
      rateLimit: { requestsPerSecond: 20 },
    }),
  };

  const config = configs[env]();
  if (!config.apiKey) {
    throw new Error(`Missing API key for ${env} environment`);
  }
  return config;
}

export const currentEnv = (process.env.MAINTAINX_ENV || 'development') as Environment;
export const config = getConfig(currentEnv);
```

### Step 2: Client Factory

```typescript
// src/client-factory.ts
import { MaintainXClient } from './client';

const clients = new Map<string, MaintainXClient>();

export function getClient(env?: Environment): MaintainXClient {
  const targetEnv = env || currentEnv;
  if (!clients.has(targetEnv)) {
    const cfg = getConfig(targetEnv);
    clients.set(targetEnv, new MaintainXClient(cfg.apiKey, cfg.orgId));
  }
  return clients.get(targetEnv)!;
}

// Usage
const devClient = getClient('development');
const prodClient = getClient('production');
```

### Step 3: Environment Files

```bash
# .env.development
MAINTAINX_ENV=development
MAINTAINX_API_KEY_DEV=dev-key-here
MAINTAINX_ORG_ID_DEV=org-dev-123

# .env.staging
MAINTAINX_ENV=staging
MAINTAINX_API_KEY_STAGING=staging-key-here
MAINTAINX_ORG_ID_STAGING=org-staging-456

# .env.production
MAINTAINX_ENV=production
MAINTAINX_API_KEY_PROD=prod-key-here
MAINTAINX_ORG_ID_PROD=org-prod-789
```

```bash
# .gitignore — never commit real keys
.env
.env.development
.env.staging
.env.production
```

### Step 4: GCP Secret Manager Integration

```typescript
// src/config/secrets.ts
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

const secretClient = new SecretManagerServiceClient();

async function getSecret(name: string): Promise<string> {
  const [version] = await secretClient.accessSecretVersion({
    name: `projects/your-project/secrets/${name}/versions/latest`,
  });
  return version.payload!.data!.toString();
}

async function loadProductionConfig(): Promise<MaintainXEnvConfig> {
  return {
    apiKey: await getSecret('maintainx-api-key-prod'),
    orgId: await getSecret('maintainx-org-id-prod'),
    baseUrl: 'https://api.getmaintainx.com/v1',
    label: 'Production',
    rateLimit: { requestsPerSecond: 20 },
  };
}
```

### Step 5: Validation Script

```typescript
// scripts/validate-environments.ts
import 'dotenv/config';

const envs: Environment[] = ['development', 'staging', 'production'];

async function validateAll() {
  for (const env of envs) {
    try {
      const cfg = getConfig(env);
      const client = new MaintainXClient(cfg.apiKey, cfg.orgId);
      const { data } = await client.getUsers({ limit: 1 });
      console.log(`${cfg.label}: OK (${data.users.length} user(s) found)`);
    } catch (err: any) {
      console.error(`${env}: FAILED - ${err.message}`);
    }
  }
}

validateAll();
```

```bash
# Run validation
npx tsx scripts/validate-environments.ts
# Development: OK (1 user(s) found)
# Staging: OK (1 user(s) found)
# Production: OK (1 user(s) found)
```

## Output
- Environment-specific configuration with type-safe config loader
- Client factory producing isolated clients per environment
- `.env.*` files with `.gitignore` protection
- GCP Secret Manager integration for production secrets
- Validation script to verify all environment credentials

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing API key | Environment variable not set | Check `.env.*` file for target environment |
| Wrong environment data | Using prod key in dev | Verify `MAINTAINX_ENV` is set correctly |
| Secret Manager 403 | Missing IAM permissions | Grant `secretmanager.secretAccessor` role |
| Config mismatch after deploy | Old secrets cached | Clear client cache, reload secrets |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [12-Factor App: Config](https://12factor.net/config)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)

## Next Steps
For observability setup, see `maintainx-observability`.

## Examples

**GitHub Actions with per-environment secrets**:

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - run: npm run validate-env
        env:
          MAINTAINX_ENV: ${{ vars.MAINTAINX_ENV }}
          MAINTAINX_API_KEY_PROD: ${{ secrets.MAINTAINX_API_KEY }}
```
