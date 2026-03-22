---
name: clickhouse-multi-env-setup
description: |
  Configure ClickHouse across dev, staging, and production with environment-specific
  settings, secrets management, and infrastructure-as-code patterns.
  Use when setting up per-environment ClickHouse instances, managing connection
  configs, or deploying to multiple environments.
  Trigger: "clickhouse environments", "clickhouse dev staging prod",
  "clickhouse multi-env", "clickhouse environment config", "clickhouse staging setup".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, database, analytics, clickhouse, olap]
compatible-with: claude-code
---

# ClickHouse Multi-Environment Setup

## Overview

Configure separate ClickHouse instances for development, staging, and production
with proper secrets management, environment detection, and infrastructure-as-code.

## Prerequisites

- ClickHouse Cloud account or self-hosted instances per environment
- Secret management solution (Vault, AWS Secrets Manager, GCP Secret Manager)
- CI/CD pipeline with environment variables

## Instructions

### Step 1: Environment Strategy

| Environment | Instance | Purpose | Data |
|-------------|----------|---------|------|
| Development | Docker local | Fast iteration | Synthetic seed data |
| Staging | ClickHouse Cloud (Dev tier) | Pre-prod validation | Sampled prod copy |
| Production | ClickHouse Cloud (Prod tier) | Live traffic | Real data |

### Step 2: Configuration Module

```typescript
// src/config/clickhouse.ts
interface ClickHouseEnvConfig {
  url: string;
  username: string;
  password: string;
  database: string;
  maxConnections: number;
  requestTimeout: number;
  compression: boolean;
}

const configs: Record<string, ClickHouseEnvConfig> = {
  development: {
    url: 'http://localhost:8123',
    username: 'default',
    password: process.env.CLICKHOUSE_PASSWORD ?? 'dev_password',
    database: 'app_dev',
    maxConnections: 5,
    requestTimeout: 60_000,    // Longer for debugging
    compression: false,         // Easier to debug raw
  },
  staging: {
    url: process.env.CLICKHOUSE_HOST ?? 'https://staging.clickhouse.cloud:8443',
    username: process.env.CLICKHOUSE_USER ?? 'app_staging',
    password: process.env.CLICKHOUSE_PASSWORD!,
    database: 'app_staging',
    maxConnections: 10,
    requestTimeout: 30_000,
    compression: true,
  },
  production: {
    url: process.env.CLICKHOUSE_HOST!,
    username: process.env.CLICKHOUSE_USER!,
    password: process.env.CLICKHOUSE_PASSWORD!,
    database: 'app_prod',
    maxConnections: 20,
    requestTimeout: 30_000,
    compression: true,
  },
};

export function getConfig(): ClickHouseEnvConfig {
  const env = process.env.NODE_ENV ?? 'development';
  const config = configs[env];
  if (!config) throw new Error(`Unknown environment: ${env}`);

  // Validate required fields in non-dev environments
  if (env !== 'development') {
    if (!config.password) throw new Error(`CLICKHOUSE_PASSWORD not set for ${env}`);
    if (!config.url.startsWith('https://')) {
      throw new Error(`ClickHouse ${env} must use HTTPS`);
    }
  }

  return config;
}
```

### Step 3: Client Factory

```typescript
// src/clickhouse/client.ts
import { createClient, ClickHouseClient } from '@clickhouse/client';
import { getConfig } from '../config/clickhouse';

let client: ClickHouseClient | null = null;

export function getClient(): ClickHouseClient {
  if (!client) {
    const config = getConfig();
    client = createClient({
      url: config.url,
      username: config.username,
      password: config.password,
      database: config.database,
      max_open_connections: config.maxConnections,
      request_timeout: config.requestTimeout,
      compression: {
        request: config.compression,
        response: config.compression,
      },
    });
  }
  return client;
}
```

### Step 4: Secrets Management

```bash
# --- Development ---
# .env.local (git-ignored)
CLICKHOUSE_PASSWORD=dev_password

# --- Staging (GitHub Actions) ---
# Set via: gh secret set CLICKHOUSE_PASSWORD_STAGING
# Access in workflow:
#   env:
#     CLICKHOUSE_PASSWORD: ${{ secrets.CLICKHOUSE_PASSWORD_STAGING }}

# --- Production (AWS Secrets Manager) ---
aws secretsmanager create-secret \
  --name clickhouse/production \
  --secret-string '{"host":"https://prod.clickhouse.cloud:8443","password":"..."}'

# Fetch at runtime:
aws secretsmanager get-secret-value \
  --secret-id clickhouse/production \
  --query SecretString --output text

# --- Production (GCP Secret Manager) ---
echo -n "https://prod.clickhouse.cloud:8443" | \
  gcloud secrets create ch-prod-host --data-file=-

gcloud secrets versions access latest --secret=ch-prod-host

# --- Production (HashiCorp Vault) ---
vault kv put secret/clickhouse/prod \
  host="https://prod.clickhouse.cloud:8443" \
  password="..."
vault kv get -field=password secret/clickhouse/prod
```

### Step 5: Schema Management Across Environments

```typescript
// scripts/apply-schema.ts
import { getClient } from '../src/clickhouse/client';
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';

async function applySchema() {
  const client = getClient();
  const env = process.env.NODE_ENV ?? 'development';
  const schemaDir = join(__dirname, '../src/clickhouse/schemas');
  const files = readdirSync(schemaDir).filter((f) => f.endsWith('.sql')).sort();

  console.log(`Applying ${files.length} schema files to ${env}...`);

  for (const file of files) {
    const sql = readFileSync(join(schemaDir, file), 'utf-8');
    try {
      await client.command({ query: sql });
      console.log(`  [OK] ${file}`);
    } catch (err) {
      console.error(`  [FAIL] ${file}: ${(err as Error).message}`);
      if (env === 'production') throw err;  // Fail hard in prod
    }
  }
}

applySchema();
```

### Step 6: Environment Guards

```typescript
// Prevent dangerous operations in production
function requireNonProduction(operation: string): void {
  if (process.env.NODE_ENV === 'production') {
    throw new Error(`${operation} is blocked in production`);
  }
}

// TRUNCATE only in dev/staging
async function resetTestData() {
  requireNonProduction('resetTestData');
  const client = getClient();
  await client.command({ query: 'TRUNCATE TABLE events' });
}

// Prevent accidental cross-environment queries
function validateDatabaseName(database: string): void {
  const env = process.env.NODE_ENV ?? 'development';
  const expected = `app_${env === 'development' ? 'dev' : env}`;
  if (database !== expected) {
    throw new Error(`Database mismatch: expected ${expected}, got ${database}`);
  }
}
```

### Step 7: CI/CD Integration

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    env:
      NODE_ENV: staging
      CLICKHOUSE_HOST: ${{ secrets.CLICKHOUSE_HOST_STAGING }}
      CLICKHOUSE_USER: ${{ secrets.CLICKHOUSE_USER_STAGING }}
      CLICKHOUSE_PASSWORD: ${{ secrets.CLICKHOUSE_PASSWORD_STAGING }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run schema:apply   # Apply schema changes
      - run: npm run test:integration  # Run against staging CH
      - run: npm run deploy:staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production   # Requires manual approval
    env:
      NODE_ENV: production
      CLICKHOUSE_HOST: ${{ secrets.CLICKHOUSE_HOST_PROD }}
      CLICKHOUSE_USER: ${{ secrets.CLICKHOUSE_USER_PROD }}
      CLICKHOUSE_PASSWORD: ${{ secrets.CLICKHOUSE_PASSWORD_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run schema:apply
      - run: npm run deploy:production
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong database in prod | Env var not set | Validate config on startup |
| TLS error in staging | Using `http://` for Cloud | Force `https://` in non-dev |
| Schema drift | Applied manually | Use migration runner in CI |
| Secret not found | Missing env var | Check secret manager + CI config |

## Resources

- [12-Factor App Config](https://12factor.net/config)
- [ClickHouse Cloud Console](https://clickhouse.cloud/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)

## Next Steps

For monitoring and observability, see `clickhouse-observability`.
