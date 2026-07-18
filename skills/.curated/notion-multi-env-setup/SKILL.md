---
name: notion-multi-env-setup
description: |
  Configure Notion integrations across development, staging, and production environments.
  Use when setting up multi-environment deployments, managing per-environment tokens,
  or implementing environment-specific Notion configurations.
  Trigger with phrases like "notion environments", "notion staging",
  "notion dev prod", "notion environment setup", "notion config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Multi-Environment Setup

## Overview

Configure separate Notion integrations for development, staging, and production. Each environment uses its own integration token, targets different databases, and applies environment-appropriate log levels and timeouts. This prevents dev data leaking into prod and enforces least-privilege per tier.

## Prerequisites

- Notion workspace(s) per environment (one workspace can serve dev/staging via separate integrations)
- `@notionhq/client` v2+ installed (`npm install @notionhq/client`)
- Python alternative: `notion-client` (`pip install notion-client`)
- Secret management platform (AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault)
- CI/CD pipeline with per-environment variable injection

## Instructions

The build has three steps. The lean skeleton below is enough to follow the workflow end to end; the [full walkthrough](references/implementation.md) carries the complete TypeScript and Python factories, every secret-manager command, and the CI/CD workflow.

### Step 1: Per-environment integrations and an env-aware client

Create one integration per environment at <https://www.notion.so/my-integrations>, each with capabilities scoped to the tier — dev gets full access, prod gets the minimum required:

| Environment | Integration | Capabilities | Timeout | Log Level |
| ------------- | ------------- | -------------- | --------- | ----------- |
| Development | `my-app-dev` | All (read+update+insert+delete) | 60s | DEBUG |
| Staging | `my-app-staging` | Read + Update + Insert | 30s | WARN |
| Production | `my-app-prod` | Minimum required only | 30s | ERROR |

A single client factory reads `NODE_ENV` (or `APP_ENV`), pulls the token and database IDs from the environment, and applies the per-tier log level and timeout. It throws a descriptive error when `NOTION_TOKEN` is missing so misconfiguration fails loudly:

```typescript
export function createNotionClient(): Client {
  const config = getConfig(); // reads NODE_ENV, token, per-tier defaults
  return new Client({
    auth: config.token,
    logLevel: config.logLevel,
    timeoutMs: config.timeoutMs,
  });
}
```

Full TypeScript `getConfig`/`getDatabaseId` and the Python equivalent: [implementation.md, Step 1](references/implementation.md).

### Step 2: Secret management and environment files

Keep dev/staging tokens in git-ignored per-environment files (`.env.development`, `.env.staging`). **Never store production tokens in files** — put them in a secret manager and inject at deploy time:

```bash
# AWS example — prod secret stored once, injected by the platform
aws secretsmanager create-secret --name "notion/production" \
  --secret-string '{"token":"ntn_prod_...","tasks_db":"...","users_db":"..."}'
```

AWS Secrets Manager, GCP Secret Manager (with Cloud Run injection), and HashiCorp Vault commands: [implementation.md, Step 2](references/implementation.md).

### Step 3: Environment guards and CI/CD

Add guards so a destructive call cannot run in the wrong tier — `requireNonProduction()` blocks seeding/test writes in prod, `requireEnvironment('production')` gates migrations. A startup validator fails fast on missing vars and catches an obvious token/tier mismatch:

```typescript
function requireNonProduction() {
  if (process.env.NODE_ENV === 'production') {
    throw new Error('Destructive operation blocked in production');
  }
}
```

Full guard set, startup validation, and the per-environment GitHub Actions deploy workflow: [implementation.md, Step 3](references/implementation.md).

## Output

- Separate Notion integrations per environment with scoped capabilities
- Environment-aware client factory (TypeScript and Python)
- Secrets stored in platform-appropriate secret managers (never in files for production)
- Startup validation that fails fast on misconfiguration
- Guards preventing cross-environment mistakes (no prod data in dev, no test data in prod)
- CI/CD pipeline deploying with per-environment secrets

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| `NOTION_TOKEN not set` | Missing env var | Check the per-environment `.env` file or secret manager config |
| Wrong database in prod | Env var misconfigured | Add startup validation to compare token prefix with env |
| Token for wrong environment | Secret manager mapping error | Validate token prefix at startup |
| Dev data written to prod DB | Missing environment guard | Add `requireNonProduction()` to destructive operations |
| 401 Unauthorized | Token revoked or expired | Regenerate at notion.so/my-integrations, update secret |
| `database_id` not found | Page not shared with integration | Share target database with the correct env integration |

## Examples

Two end-to-end examples live in [examples.md](references/examples.md):

- **Full initialization pattern** — chains `validateNotionConfig()`, the client factory, and a live connectivity + database-access check into one `initNotion()` boot function.
- **Quick environment check script** — a `verify-notion-env.sh` pre-deploy script that confirms the injected token authenticates and reports the workspace it points at.

```bash
# verify-notion-env.sh (excerpt) — confirm the injected token before deploy
curl -sf https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq '{name, type}'
```

## Resources

- [Full implementation walkthrough](references/implementation.md) — all code for Steps 1–3
- [Worked examples](references/examples.md) — init pattern + pre-deploy check script
- [Notion Create Integrations](https://developers.notion.com/docs/create-a-notion-integration)
- [Notion Authentication](https://developers.notion.com/reference/authentication)
- [12-Factor App Config](https://12factor.net/config)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [HashiCorp Vault KV](https://developer.hashicorp.com/vault/docs/secrets/kv)

For monitoring your Notion integration health across environments, see the `notion-observability` skill.
