---
name: clickup-multi-env-setup
description: |
  Configure ClickUp API access across dev, staging, and production environments
  with per-environment tokens and workspace isolation.
  Trigger: "clickup environments", "clickup staging", "clickup dev prod",
  "clickup environment setup", "clickup config by env", "clickup multi-env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Multi-Environment Setup

## Overview

Configure separate ClickUp workspaces and API tokens for development, staging, and production. ClickUp does not have sandbox environments, so the recommended approach is separate workspaces with separate tokens per environment.

## Environment Strategy

| Environment | Workspace | Token | Rate Limit | Purpose |
|-------------|-----------|-------|-----------|---------|
| Development | Dev workspace | Personal token | 100 req/min | Local development, testing |
| Staging | Staging workspace | Service token | 100 req/min | Integration testing, QA |
| Production | Production workspace | Service token | Per plan | Live traffic |

**Key point:** All ClickUp API calls go to `https://api.clickup.com/api/v2/` regardless of environment. Environment isolation comes from using different tokens that are authorized for different workspaces.

## Configuration

```typescript
// src/config/clickup.ts
interface ClickUpEnvConfig {
  token: string;
  teamId: string;
  defaultListId?: string;
  timeout: number;
  retries: number;
  cacheEnabled: boolean;
  cacheTtlMs: number;
}

function getClickUpConfig(): ClickUpEnvConfig {
  const env = process.env.NODE_ENV ?? 'development';

  const base = {
    timeout: 30000,
    retries: 3,
    cacheEnabled: true,
    cacheTtlMs: 60000,
  };

  switch (env) {
    case 'production':
      return {
        ...base,
        token: requireEnv('CLICKUP_API_TOKEN_PROD'),
        teamId: requireEnv('CLICKUP_TEAM_ID_PROD'),
        retries: 5,          // More retries in prod
        cacheTtlMs: 300000,  // 5 min cache in prod
      };
    case 'staging':
      return {
        ...base,
        token: requireEnv('CLICKUP_API_TOKEN_STAGING'),
        teamId: requireEnv('CLICKUP_TEAM_ID_STAGING'),
      };
    default:
      return {
        ...base,
        token: requireEnv('CLICKUP_API_TOKEN'),
        teamId: process.env.CLICKUP_TEAM_ID ?? '',
        cacheEnabled: false,  // No cache in dev for fresh data
      };
  }
}

function requireEnv(key: string): string {
  const value = process.env[key];
  if (!value) throw new Error(`Missing required env var: ${key}`);
  return value;
}
```

## Environment Files

```bash
# .env.development (local dev, git-ignored)
CLICKUP_API_TOKEN=pk_dev_12345_ABCDEF
CLICKUP_TEAM_ID=1111111

# .env.staging (CI/CD only, git-ignored)
CLICKUP_API_TOKEN_STAGING=pk_stg_67890_GHIJKL
CLICKUP_TEAM_ID_STAGING=2222222

# .env.production (secrets manager only, NEVER in files)
# CLICKUP_API_TOKEN_PROD=pk_prod_... (stored in Vault/AWS/GCP)
# CLICKUP_TEAM_ID_PROD=3333333
```

```bash
# .env.example (commit this as template)
CLICKUP_API_TOKEN=pk_your_token_here
CLICKUP_TEAM_ID=your_team_id_here
```

## Secrets by Platform

```bash
# GitHub Actions
gh secret set CLICKUP_API_TOKEN_STAGING --body "pk_stg_..."
gh secret set CLICKUP_API_TOKEN_PROD --body "pk_prod_..."

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name clickup/production/api-token \
  --secret-string "pk_prod_..."

# GCP Secret Manager
echo -n "pk_prod_..." | gcloud secrets create clickup-api-token-prod --data-file=-

# HashiCorp Vault
vault kv put secret/clickup/production api_token="pk_prod_..."
```

## Environment Guards

```typescript
// Prevent destructive operations in production
function guardDestructiveOp(operation: string): void {
  const config = getClickUpConfig();
  const env = process.env.NODE_ENV ?? 'development';

  // In production, require explicit confirmation
  if (env === 'production' && !process.env.CLICKUP_ALLOW_DESTRUCTIVE) {
    throw new Error(
      `${operation} blocked in production. Set CLICKUP_ALLOW_DESTRUCTIVE=true to override.`
    );
  }
}

// Usage: prevent bulk delete in prod
async function deleteCompletedTasks(listId: string) {
  guardDestructiveOp('deleteCompletedTasks');

  const { tasks } = await clickupRequest(
    `/list/${listId}/task?statuses[]=complete`
  );
  for (const task of tasks) {
    await clickupRequest(`/task/${task.id}`, { method: 'DELETE' });
  }
}
```

## Verify Environment Setup

```bash
#!/bin/bash
# verify-clickup-env.sh
echo "=== ClickUp Environment Verification ==="
echo "NODE_ENV: ${NODE_ENV:-development}"

for ENV_SUFFIX in "" "_STAGING" "_PROD"; do
  TOKEN_VAR="CLICKUP_API_TOKEN${ENV_SUFFIX}"
  TOKEN="${!TOKEN_VAR}"

  if [ -z "$TOKEN" ]; then
    echo "${TOKEN_VAR}: NOT SET"
    continue
  fi

  echo -n "${TOKEN_VAR}: "
  RESULT=$(curl -sf https://api.clickup.com/api/v2/user \
    -H "Authorization: $TOKEN" 2>/dev/null)
  if [ $? -eq 0 ]; then
    USERNAME=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['username'])" 2>/dev/null)
    echo "OK (user: $USERNAME)"
  else
    echo "FAILED"
  fi
done
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong workspace in prod | Using dev token | Verify CLICKUP_TEAM_ID matches token's workspace |
| Missing env var | Not configured | Check .env file or secrets manager |
| Cross-env data leak | Shared token | Use separate tokens per environment |
| Destructive op in prod | Missing guard | Implement environment guards |

## Resources

- [ClickUp Authentication](https://developer.clickup.com/docs/authentication)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps

For observability setup, see `clickup-observability`.
