# MaintainX Multi-Environment Setup - Implementation Guide

> Full implementation details and code examples for the `maintainx-multi-env-setup` skill.

# MaintainX Multi-Environment Setup

## Overview

Configure and manage multiple MaintainX environments for development, staging, and production workflows.

## Prerequisites

- Multiple MaintainX accounts or organizations
- Secret management solution
- CI/CD pipeline configured

## Environment Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Environment Promotion Flow                        │
│                                                                      │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐                  │
│  │   DEV    │ ───▶ │ STAGING  │ ───▶ │   PROD   │                  │
│  │          │      │          │      │          │                  │
│  │ sandbox  │      │  testing │      │   live   │                  │
│  │  data    │      │   data   │      │   data   │                  │
│  └──────────┘      └──────────┘      └──────────┘                  │
│       │                 │                 │                         │
│       ▼                 ▼                 ▼                         │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐                  │
│  │  dev-    │      │  staging-│      │  prod-   │                  │
│  │  api-key │      │  api-key │      │  api-key │                  │
│  └──────────┘      └──────────┘      └──────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Environment Configuration

```typescript
// src/config/environments.ts

type Environment = 'development' | 'staging' | 'production';

interface EnvironmentConfig {
  name: Environment;
  maintainx: {
    apiKey: string;
    orgId?: string;
    baseUrl: string;
  };
  features: {
    caching: boolean;
    rateLimit: number;
    webhooksEnabled: boolean;
  };
  logging: {
    level: string;
    redactPII: boolean;
  };
}

const environments: Record<Environment, () => EnvironmentConfig> = {
  development: () => ({
    name: 'development',
    maintainx: {
      apiKey: process.env.MAINTAINX_API_KEY_DEV!,
      orgId: process.env.MAINTAINX_ORG_ID_DEV,
      baseUrl: 'https://api.getmaintainx.com/v1',
    },
    features: {
      caching: false,  // Disable caching in dev for fresh data
      rateLimit: 60,
      webhooksEnabled: false,
    },
    logging: {
      level: 'debug',
      redactPII: false,  // OK in dev
    },
  }),

  staging: () => ({
    name: 'staging',
    maintainx: {
      apiKey: process.env.MAINTAINX_API_KEY_STAGING!,
      orgId: process.env.MAINTAINX_ORG_ID_STAGING,
      baseUrl: 'https://api.getmaintainx.com/v1',
    },
    features: {
      caching: true,
      rateLimit: 120,
      webhooksEnabled: true,
    },
    logging: {
      level: 'info',
      redactPII: true,
    },
  }),

  production: () => ({
    name: 'production',
    maintainx: {
      apiKey: process.env.MAINTAINX_API_KEY_PROD!,
      orgId: process.env.MAINTAINX_ORG_ID_PROD,
      baseUrl: 'https://api.getmaintainx.com/v1',
    },
    features: {
      caching: true,
      rateLimit: 300,
      webhooksEnabled: true,
    },
    logging: {
      level: 'warn',
      redactPII: true,
    },
  }),
};

function getEnvironment(): Environment {
  const env = process.env.NODE_ENV as Environment;
  if (!['development', 'staging', 'production'].includes(env)) {
    return 'development';
  }
  return env;
}

function getConfig(): EnvironmentConfig {
  const env = getEnvironment();
  return environments[env]();
}

export { getConfig, getEnvironment, EnvironmentConfig, Environment };
```

### Step 2: Environment-Aware Client Factory

```typescript
// src/api/client-factory.ts

import { getConfig } from '../config/environments';

class MaintainXClientFactory {
  private static clients: Map<string, MaintainXClient> = new Map();

  static getClient(environment?: Environment): MaintainXClient {
    const config = environment
      ? environments[environment]()
      : getConfig();

    const cacheKey = config.name;

    if (!this.clients.has(cacheKey)) {
      const client = new MaintainXClient({
        apiKey: config.maintainx.apiKey,
        orgId: config.maintainx.orgId,
        baseUrl: config.maintainx.baseUrl,
      });

      // Apply environment-specific configurations
      if (config.features.caching) {
        // Wrap with caching
      }

      this.clients.set(cacheKey, client);
    }

    return this.clients.get(cacheKey)!;
  }

  // For cross-environment operations
  static getClientForEnvironment(env: Environment): MaintainXClient {
    return this.getClient(env);
  }

  // Clear cached clients (useful for testing)
  static clearCache(): void {
    this.clients.clear();
  }
}

export { MaintainXClientFactory };
```

### Step 3: Environment Variables Template

```bash
# .env.example

# Development
MAINTAINX_API_KEY_DEV=mx_dev_xxxxx
MAINTAINX_ORG_ID_DEV=org_dev_xxxxx

# Staging
MAINTAINX_API_KEY_STAGING=mx_staging_xxxxx
MAINTAINX_ORG_ID_STAGING=org_staging_xxxxx

# Production
MAINTAINX_API_KEY_PROD=mx_prod_xxxxx
MAINTAINX_ORG_ID_PROD=org_prod_xxxxx

# Current environment
NODE_ENV=development
```

```yaml
# docker-compose.override.yml (development)
version: '3.8'

services:
  app:
    environment:
      - NODE_ENV=development
      - MAINTAINX_API_KEY=${MAINTAINX_API_KEY_DEV}
      - MAINTAINX_ORG_ID=${MAINTAINX_ORG_ID_DEV}
```

### Step 4: Secret Management Integration

```typescript
// src/config/secrets.ts

import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

interface SecretConfig {
  apiKey: string;
  orgId?: string;
}

class SecretLoader {
  private client: SecretManagerServiceClient;
  private projectId: string;

  constructor() {
    this.client = new SecretManagerServiceClient();
    this.projectId = process.env.GCP_PROJECT_ID!;
  }

  async loadEnvironmentSecrets(env: Environment): Promise<SecretConfig> {
    const apiKeyName = `maintainx-api-key-${env}`;
    const orgIdName = `maintainx-org-id-${env}`;

    const apiKey = await this.getSecret(apiKeyName);
    const orgId = await this.getSecret(orgIdName).catch(() => undefined);

    return { apiKey, orgId };
  }

  private async getSecret(name: string): Promise<string> {
    const [version] = await this.client.accessSecretVersion({
      name: `projects/${this.projectId}/secrets/${name}/versions/latest`,
    });

    return version.payload?.data?.toString() || '';
  }
}

// Kubernetes secret mounting alternative
function loadFromMountedSecrets(env: Environment): SecretConfig {
  const basePath = '/var/secrets/maintainx';

  return {
    apiKey: fs.readFileSync(`${basePath}/${env}/api-key`, 'utf8').trim(),
    orgId: fs.existsSync(`${basePath}/${env}/org-id`)
      ? fs.readFileSync(`${basePath}/${env}/org-id`, 'utf8').trim()
      : undefined,
  };
}
```

### Step 5: Environment Promotion Tools

```typescript
// scripts/promote-config.ts

import { MaintainXClientFactory } from '../src/api/client-factory';

interface PromotionResult {
  success: boolean;
  itemsPromoted: number;
  errors: string[];
}

// Promote configuration from one environment to another
async function promoteConfiguration(
  sourceEnv: Environment,
  targetEnv: Environment
): Promise<PromotionResult> {
  const result: PromotionResult = {
    success: true,
    itemsPromoted: 0,
    errors: [],
  };

  const sourceClient = MaintainXClientFactory.getClientForEnvironment(sourceEnv);
  const targetClient = MaintainXClientFactory.getClientForEnvironment(targetEnv);

  console.log(`Promoting from ${sourceEnv} to ${targetEnv}...`);

  // Note: This is conceptual - actual promotion depends on what's configurable via API
  // Some configurations may need to be managed manually in MaintainX dashboard

  // Example: Sync work order templates (if supported)
  // Example: Sync procedure templates (if supported)

  console.log('Promotion complete');
  console.log(`Items promoted: ${result.itemsPromoted}`);
  if (result.errors.length > 0) {
    console.log('Errors:', result.errors);
  }

  return result;
}

// Validate environment configuration
async function validateEnvironment(env: Environment): Promise<boolean> {
  console.log(`Validating ${env} environment...`);

  try {
    const client = MaintainXClientFactory.getClientForEnvironment(env);

    // Test API connectivity
    await client.getUsers({ limit: 1 });
    console.log(`  [OK] API connectivity`);

    // Test work order access
    await client.getWorkOrders({ limit: 1 });
    console.log(`  [OK] Work order access`);

    // Test asset access
    await client.getAssets({ limit: 1 });
    console.log(`  [OK] Asset access`);

    return true;
  } catch (error: any) {
    console.error(`  [FAIL] ${error.message}`);
    return false;
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case 'validate':
      const env = args[1] as Environment || 'development';
      const valid = await validateEnvironment(env);
      process.exit(valid ? 0 : 1);
      break;

    case 'promote':
      const source = args[1] as Environment;
      const target = args[2] as Environment;
      if (!source || !target) {
        console.error('Usage: promote <source> <target>');
        process.exit(1);
      }
      await promoteConfiguration(source, target);
      break;

    default:
      console.log('Commands: validate <env>, promote <source> <target>');
  }
}

main().catch(console.error);
```

### Step 6: CI/CD Environment Matrix

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches:
      - develop  # Deploy to staging
      - main     # Deploy to production
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - branch: develop
            environment: staging
          - branch: main
            environment: production

    environment: ${{ matrix.environment }}

    steps:
      - uses: actions/checkout@v4

      - name: Validate environment config
        run: |
          npm ci
          npm run env:validate -- ${{ matrix.environment }}
        env:
          MAINTAINX_API_KEY_STAGING: ${{ secrets.MAINTAINX_API_KEY_STAGING }}
          MAINTAINX_API_KEY_PROD: ${{ secrets.MAINTAINX_API_KEY_PROD }}

      - name: Deploy to ${{ matrix.environment }}
        run: |
          ./scripts/deploy.sh ${{ matrix.environment }}
        env:
          NODE_ENV: ${{ matrix.environment }}
```

## Output

- Environment-specific configurations
- Secret management integration
- Client factory for multi-environment
- Promotion tools for config sync
- CI/CD environment matrix

## Best Practices

1. **Isolate environments**: Use separate MaintainX organizations per environment
2. **Never share API keys**: Each environment gets unique credentials
3. **Validate before promote**: Always test configuration in lower environments
4. **Document differences**: Track what varies between environments
5. **Audit access**: Log which environment is being accessed

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [12-Factor App Configuration](https://12factor.net/config)
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager)

## Next Steps

For observability setup, see `maintainx-observability`.
