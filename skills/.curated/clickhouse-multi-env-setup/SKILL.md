---
name: clickhouse-multi-env-setup
description: |
  Configure ClickHouse across dev, staging, and production with
  environment-specific settings, secrets management, and infrastructure-as-code
  patterns. Use when setting up per-environment ClickHouse instances, managing
  connection configs, wiring secrets per environment, or deploying to multiple
  environments. Trigger with "clickhouse environments", "clickhouse dev staging
  prod", "clickhouse multi-env", "clickhouse environment config", "clickhouse
  staging setup".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Multi-Environment Setup

## Overview

Configure separate ClickHouse instances for development, staging, and production
with proper secrets management, environment detection, and infrastructure-as-code.
A single typed config module resolves the right instance from `NODE_ENV`, so
application code never branches on environment and destructive operations are
blocked outside dev/staging.

The full code for every step lives in
[references/implementation.md](references/implementation.md); worked end-to-end
flows are in [references/examples.md](references/examples.md).

## Prerequisites

- ClickHouse Cloud account or self-hosted instances per environment
- Secret management solution (Vault, AWS Secrets Manager, GCP Secret Manager)
- CI/CD pipeline with environment variables

## Instructions

### Step 1: Choose an environment strategy

Provision one instance per tier, isolated by data sensitivity:

| Environment | Instance | Purpose | Data |
|-------------|----------|---------|------|
| Development | Docker local | Fast iteration | Synthetic seed data |
| Staging | ClickHouse Cloud (Dev tier) | Pre-prod validation | Sampled prod copy |
| Production | ClickHouse Cloud (Prod tier) | Live traffic | Real data |

### Step 2: Build a typed config module

Create `src/config/clickhouse.ts` with one `ClickHouseEnvConfig` per environment,
keyed by `NODE_ENV`. Fail fast in non-dev environments — require a password and
enforce HTTPS at startup:

```typescript
export function getConfig(): ClickHouseEnvConfig {
  const env = process.env.NODE_ENV ?? 'development';
  const config = configs[env];
  if (!config) throw new Error(`Unknown environment: ${env}`);
  if (env !== 'development') {
    if (!config.password) throw new Error(`CLICKHOUSE_PASSWORD not set for ${env}`);
    if (!config.url.startsWith('https://')) {
      throw new Error(`ClickHouse ${env} must use HTTPS`);
    }
  }
  return config;
}
```

Full per-environment config table (pool sizes, timeouts, compression):
[references/implementation.md](references/implementation.md).

### Step 3: Add a client factory

A lazily-initialized singleton in `src/clickhouse/client.ts` builds the pool once
per process from the resolved config. Full code:
[references/implementation.md](references/implementation.md).

### Step 4: Wire secrets per environment

Dev uses a git-ignored `.env.local`; every other tier pulls from a secret manager
(AWS Secrets Manager, GCP Secret Manager, or Vault) — never commit credentials.
CLI recipes for all three:
[references/implementation.md](references/implementation.md).

### Step 5: Apply schema deterministically

Run sorted `.sql` files through a migration runner (`scripts/apply-schema.ts`).
Fail hard in production, log-and-continue in dev/staging:
[references/implementation.md](references/implementation.md).

### Step 6: Add environment guards

`requireNonProduction` blocks TRUNCATE/reset in prod and `validateDatabaseName`
catches cross-environment queries. Full guards:
[references/implementation.md](references/implementation.md).

### Step 7: Integrate with CI/CD

Auto-deploy staging; gate production behind `needs: deploy-staging` plus a
manual-approval environment. Full workflow:
[references/examples.md](references/examples.md).

## Output

Completing this workflow yields:

- `src/config/clickhouse.ts` — typed, per-environment ClickHouse config with
  startup validation (password present, HTTPS enforced outside dev).
- `src/clickhouse/client.ts` — a singleton client factory keyed off `NODE_ENV`.
- `scripts/apply-schema.ts` — a deterministic, sorted migration runner.
- Environment guards preventing destructive operations against production.
- Secrets stored in a secret manager per environment (nothing committed).
- A `.github/workflows/deploy.yml` pipeline that migrates schema and deploys
  staging automatically, production behind manual approval.

Application code then calls `getClient()` with zero environment branching.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong database in prod | Env var not set | Validate config on startup |
| TLS error in staging | Using `http://` for Cloud | Force `https://` in non-dev |
| Schema drift | Applied manually | Use migration runner in CI |
| Secret not found | Missing env var | Check secret manager + CI config |

## Examples

Query from application code with no environment logic — `getConfig()` resolves the
right instance from `NODE_ENV`:

```typescript
import { getClient } from './clickhouse/client';

const rows = await getClient().query({
  query: 'SELECT count() AS c FROM events WHERE date = today()',
  format: 'JSONEachRow',
});
console.log(await rows.json());
```

More worked flows — the environment-strategy layout, the full CI/CD deploy
pipeline, and end-to-end query usage — are in
[references/examples.md](references/examples.md).

## Resources

- [full implementation walkthrough](references/implementation.md)
- [worked examples](references/examples.md)
- [12-Factor App Config](https://12factor.net/config)
- [ClickHouse Cloud Console](https://clickhouse.cloud/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager)

## Next Steps

For monitoring and observability, see the `clickhouse-observability` skill, which
covers query performance dashboards, slow-query logging, and alerting across the
same dev/staging/production tiers you configured here.
