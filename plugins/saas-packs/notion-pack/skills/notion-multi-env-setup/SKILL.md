---
name: notion-multi-env-setup
description: |
  Configure Notion integrations across development, staging, and production environments.
  Use when setting up multi-environment deployments, managing per-environment tokens,
  or implementing environment-specific Notion configurations.
  Trigger with phrases like "notion environments", "notion staging",
  "notion dev prod", "notion environment setup", "notion config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Multi-Environment Setup

## Overview
Configure separate Notion integrations and databases for development, staging, and production. Each environment should use its own integration token and target different Notion databases.

## Prerequisites
- Notion workspace(s) for each environment
- Secret management solution
- CI/CD pipeline with environment variables

## Instructions

### Step 1: Create Per-Environment Integrations
Create separate integrations at https://www.notion.so/my-integrations:

| Environment | Integration Name | Capabilities | Purpose |
|-------------|-----------------|--------------|---------|
| Development | `my-app-dev` | All (for debugging) | Local development |
| Staging | `my-app-staging` | Read + Update + Insert | Pre-prod testing |
| Production | `my-app-prod` | Minimum required | Live traffic |

### Step 2: Environment Configuration
```typescript
// src/config/notion.ts
import { Client, LogLevel } from '@notionhq/client';

interface NotionEnvConfig {
  token: string;
  databaseIds: Record<string, string>;
  logLevel: LogLevel;
  timeoutMs: number;
}

function getConfig(): NotionEnvConfig {
  const env = process.env.NODE_ENV || 'development';

  const configs: Record<string, Partial<NotionEnvConfig>> = {
    development: {
      logLevel: LogLevel.DEBUG,
      timeoutMs: 60_000,
    },
    staging: {
      logLevel: LogLevel.WARN,
      timeoutMs: 30_000,
    },
    production: {
      logLevel: LogLevel.ERROR,
      timeoutMs: 30_000,
    },
  };

  return {
    token: process.env.NOTION_TOKEN!,
    databaseIds: {
      tasks: process.env.NOTION_TASKS_DB_ID!,
      users: process.env.NOTION_USERS_DB_ID!,
      logs: process.env.NOTION_LOGS_DB_ID!,
    },
    logLevel: LogLevel.WARN,
    timeoutMs: 30_000,
    ...configs[env],
  };
}

export function createNotionClient(): Client {
  const config = getConfig();

  if (!config.token) {
    throw new Error(`NOTION_TOKEN not set for ${process.env.NODE_ENV}`);
  }

  return new Client({
    auth: config.token,
    logLevel: config.logLevel,
    timeoutMs: config.timeoutMs,
  });
}

export function getDatabaseId(name: string): string {
  const config = getConfig();
  const id = config.databaseIds[name];
  if (!id) {
    throw new Error(`Database ID not configured for "${name}". Set NOTION_${name.toUpperCase()}_DB_ID`);
  }
  return id;
}
```

### Step 3: Environment Files
```bash
# .env.development
NOTION_TOKEN=ntn_dev_xxxxx
NOTION_TASKS_DB_ID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
NOTION_USERS_DB_ID=ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj

# .env.staging
NOTION_TOKEN=ntn_staging_xxxxx
NOTION_TASKS_DB_ID=11111111-2222-3333-4444-555555555555
NOTION_USERS_DB_ID=66666666-7777-8888-9999-000000000000

# .env.production (stored in secret manager, NOT as a file)
# NOTION_TOKEN=ntn_prod_xxxxx
# NOTION_TASKS_DB_ID=abcdefab-cdef-abcd-efab-cdefabcdefab
```

### Step 4: Secret Management

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name notion/production \
  --secret-string '{"token":"ntn_prod_xxx","tasks_db":"db-id","users_db":"db-id"}'

# Load in application
# const secrets = JSON.parse(await getSecret('notion/production'));

# GCP Secret Manager
echo -n "ntn_prod_xxx" | gcloud secrets create notion-token-prod --data-file=-
echo -n "db-id" | gcloud secrets create notion-tasks-db-prod --data-file=-

# Cloud Run deployment
gcloud run deploy my-service \
  --set-secrets=NOTION_TOKEN=notion-token-prod:latest,NOTION_TASKS_DB_ID=notion-tasks-db-prod:latest

# HashiCorp Vault
vault kv put secret/notion/production \
  token=ntn_prod_xxx \
  tasks_db_id=db-id
```

### Step 5: Environment Guards
```typescript
// Prevent dangerous operations in wrong environment
function requireEnvironment(required: string) {
  const current = process.env.NODE_ENV || 'development';
  if (current !== required) {
    throw new Error(`Operation requires ${required} environment, currently in ${current}`);
  }
}

// Usage
async function migrateAllData() {
  requireEnvironment('production'); // Block in dev/staging
  // ... migration logic
}

async function clearTestData() {
  if (process.env.NODE_ENV === 'production') {
    throw new Error('Cannot clear data in production');
  }
  // ... cleanup logic
}
```

### Step 6: CI/CD Per-Environment
```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    env:
      NOTION_TOKEN: ${{ secrets.NOTION_TOKEN_STAGING }}
      NOTION_TASKS_DB_ID: ${{ secrets.NOTION_TASKS_DB_ID_STAGING }}
    steps:
      - run: npm test
      - run: npm run deploy:staging

  deploy-production:
    if: github.ref == 'refs/heads/main'
    env:
      NOTION_TOKEN: ${{ secrets.NOTION_TOKEN_PROD }}
      NOTION_TASKS_DB_ID: ${{ secrets.NOTION_TASKS_DB_ID_PROD }}
    steps:
      - run: npm test
      - run: INTEGRATION=true npm run test:integration
      - run: npm run deploy:production
```

## Output
- Separate Notion integrations per environment
- Environment-aware configuration loading
- Secrets stored in platform-appropriate secret managers
- Guards preventing cross-environment mistakes

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong database in prod | Env var misconfigured | Validate database IDs at startup |
| Token for wrong env | Secret manager error | Check secret names match environment |
| Dev data in prod | Missing guard | Add environment checks |
| Missing env var | Incomplete setup | Validate all required vars at startup |

## Examples

### Startup Validation
```typescript
function validateConfig() {
  const required = ['NOTION_TOKEN', 'NOTION_TASKS_DB_ID'];
  const missing = required.filter(v => !process.env[v]);
  if (missing.length > 0) {
    throw new Error(`Missing environment variables: ${missing.join(', ')}`);
  }
  console.log(`Notion configured for ${process.env.NODE_ENV}`);
}
```

## Resources
- [Notion Create Integrations](https://developers.notion.com/docs/create-a-notion-integration)
- [12-Factor App Config](https://12factor.net/config)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)

## Next Steps
For observability setup, see `notion-observability`.
