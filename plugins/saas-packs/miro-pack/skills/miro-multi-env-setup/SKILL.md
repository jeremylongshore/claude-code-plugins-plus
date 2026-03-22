---
name: miro-multi-env-setup
description: |
  Configure Miro REST API v2 across development, staging, and production
  with separate OAuth apps, isolated test boards, and secret management.
  Trigger with phrases like "miro environments", "miro staging",
  "miro dev prod", "miro environment setup", "miro multi env".
allowed-tools: Read, Write, Edit, Bash(gcloud:*), Bash(aws:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, environments, configuration]
compatible-with: claude-code
---

# Miro Multi-Environment Setup

## Overview

Configure separate Miro app credentials, OAuth scopes, and board access for development, staging, and production. Miro does not provide a sandbox API; all environments use `https://api.miro.com/v2/` — isolation is achieved through separate apps and dedicated boards.

## Environment Strategy

| Environment | Miro App | Boards | Scopes | Token Storage |
|-------------|----------|--------|--------|---------------|
| Development | `MyApp (Dev)` | 1 dedicated test board | `boards:read`, `boards:write` | `.env.local` |
| Staging | `MyApp (Staging)` | Staging workspace boards | All required scopes | Secret Manager |
| Production | `MyApp (Production)` | Production boards | Minimum required scopes | Secret Manager + rotation |

**Key insight:** Create a separate Miro app at https://developers.miro.com for each environment. This gives you independent client IDs, secrets, and OAuth redirect URIs.

## Configuration Structure

```
config/
├── miro.base.ts          # Shared settings (timeouts, retry policy)
├── miro.development.ts   # Dev overrides
├── miro.staging.ts       # Staging overrides
└── miro.production.ts    # Prod overrides
```

### Base Configuration

```typescript
// config/miro.base.ts
export const miroBaseConfig = {
  apiBase: 'https://api.miro.com/v2',
  tokenEndpoint: 'https://api.miro.com/v1/oauth/token',
  timeout: 30000,
  retries: 3,
  backoff: { baseMs: 1000, maxMs: 32000, jitterMs: 500 },
  cache: { ttlSeconds: 120 },
  rateLimit: { maxConcurrency: 5, requestsPerSecond: 10 },
};
```

### Environment Configs

```typescript
// config/miro.development.ts
import { miroBaseConfig } from './miro.base';

export const miroDevConfig = {
  ...miroBaseConfig,
  clientId: process.env.MIRO_CLIENT_ID!,
  clientSecret: process.env.MIRO_CLIENT_SECRET!,
  redirectUri: 'http://localhost:3000/auth/miro/callback',
  testBoardId: process.env.MIRO_TEST_BOARD_ID,   // Dedicated dev board
  cache: { ttlSeconds: 10 },                      // Short TTL for dev
  logLevel: 'debug',
};

// config/miro.staging.ts
export const miroStagingConfig = {
  ...miroBaseConfig,
  clientId: process.env.MIRO_CLIENT_ID_STAGING!,
  clientSecret: process.env.MIRO_CLIENT_SECRET_STAGING!,
  redirectUri: 'https://staging.myapp.com/auth/miro/callback',
  cache: { ttlSeconds: 60 },
  logLevel: 'info',
};

// config/miro.production.ts
export const miroProdConfig = {
  ...miroBaseConfig,
  clientId: process.env.MIRO_CLIENT_ID_PROD!,
  clientSecret: process.env.MIRO_CLIENT_SECRET_PROD!,
  redirectUri: 'https://myapp.com/auth/miro/callback',
  retries: 5,                                      // More retries in prod
  cache: { ttlSeconds: 120 },
  logLevel: 'warn',
};
```

### Config Loader

```typescript
// config/index.ts
type Environment = 'development' | 'staging' | 'production';

export function loadMiroConfig() {
  const env = (process.env.NODE_ENV ?? 'development') as Environment;

  switch (env) {
    case 'production': return miroProdConfig;
    case 'staging': return miroStagingConfig;
    default: return miroDevConfig;
  }
}
```

## Secret Management

### Development: .env.local

```bash
# .env.local (git-ignored)
MIRO_CLIENT_ID=3458764500000001
MIRO_CLIENT_SECRET=dev_secret_here
MIRO_ACCESS_TOKEN=dev_access_token
MIRO_REFRESH_TOKEN=dev_refresh_token
MIRO_TEST_BOARD_ID=uXjVN_dev_board
MIRO_WEBHOOK_SECRET=dev_webhook_secret
```

### Staging/Production: Secret Manager

```bash
# GCP Secret Manager
gcloud secrets create miro-client-secret-staging --data-file=<(echo -n "staging_secret")
gcloud secrets create miro-client-secret-prod --data-file=<(echo -n "prod_secret")

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name miro/staging/client-secret \
  --secret-string "staging_secret"

aws secretsmanager create-secret \
  --name miro/production/client-secret \
  --secret-string "prod_secret"

# HashiCorp Vault
vault kv put secret/miro/staging client_secret=staging_secret
vault kv put secret/miro/production client_secret=prod_secret
```

### CI/CD Secrets (GitHub Actions)

```bash
# Per-environment secrets
gh secret set MIRO_CLIENT_ID_DEV --body "dev_client_id"
gh secret set MIRO_CLIENT_SECRET_DEV --body "dev_client_secret"
gh secret set MIRO_CLIENT_ID_STAGING --body "staging_client_id"
gh secret set MIRO_CLIENT_SECRET_STAGING --body "staging_client_secret"
gh secret set MIRO_CLIENT_ID_PROD --body "prod_client_id"
gh secret set MIRO_CLIENT_SECRET_PROD --body "prod_client_secret"
```

## Environment Guards

Prevent production-dangerous operations in development:

```typescript
const config = loadMiroConfig();

function guardProduction(operation: string): void {
  if (config.environment === 'development') {
    throw new Error(`${operation} blocked in development — use staging or production`);
  }
}

function guardDestructive(operation: string, boardId: string): void {
  const protectedBoards = process.env.MIRO_PROTECTED_BOARDS?.split(',') ?? [];
  if (protectedBoards.includes(boardId)) {
    throw new Error(`${operation} blocked on protected board ${boardId}`);
  }
}

// Prevent accidental deletion of production boards
async function deleteBoard(boardId: string): Promise<void> {
  guardDestructive('deleteBoard', boardId);
  await api.fetch(`/v2/boards/${boardId}`, 'DELETE');
}
```

## OAuth Redirect URI per Environment

Each Miro app must have its redirect URI configured to match the environment:

| Environment | Redirect URI | Where to Configure |
|-------------|-------------|-------------------|
| Development | `http://localhost:3000/auth/miro/callback` | Miro app "Dev" settings |
| Staging | `https://staging.myapp.com/auth/miro/callback` | Miro app "Staging" settings |
| Production | `https://myapp.com/auth/miro/callback` | Miro app "Production" settings |

Miro requires exact redirect URI match. No wildcards.

## Board Isolation Strategy

```typescript
// Development: Use a single dedicated test board
// Clean up after each test run
async function cleanupDevBoard(): Promise<void> {
  const testBoardId = config.testBoardId;
  if (!testBoardId) return;

  const items = await api.fetchAll(`/v2/boards/${testBoardId}/items`);
  for (const item of items) {
    await api.fetch(`/v2/boards/${testBoardId}/items/${item.id}`, 'DELETE');
  }
  console.log(`Cleaned ${items.length} items from dev board`);
}

// Staging: Use a separate Miro workspace or team
// Production: Real user boards — never clean up automatically
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong redirect URI | Env mismatch | Check Miro app settings for this environment |
| Staging token on prod board | Mixed credentials | Use separate Miro apps per env |
| Secret not found | Wrong secret path | Verify secret manager key for this env |
| Dev board full | No cleanup between runs | Run `cleanupDevBoard()` in test teardown |

## Resources

- [Miro App Settings](https://developers.miro.com)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps

For observability setup, see `miro-observability`.
