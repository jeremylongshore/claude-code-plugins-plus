---
name: intercom-multi-env-setup
description: 'Configure Intercom across development, staging, and production workspaces.

  Use when setting up multi-environment deployments, configuring per-environment

  access tokens, or implementing workspace isolation.

  Trigger with phrases like "intercom environments", "intercom staging",

  "intercom dev prod", "intercom environment setup", "intercom workspace isolation".

  '
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Multi-Environment Setup

## Overview

Configure separate Intercom workspaces for development, staging, and production with environment-specific access tokens, webhook URLs, and safety guards. This skill establishes a single config loader, an environment-aware client factory, per-platform secret storage, and production guards so the same codebase behaves correctly in every environment.

The full step-by-step code lives in [references/implementation.md](references/implementation.md); this file carries the workflow and the Step 1 skeleton so you can follow it end to end, then drill into the reference for depth.

## Prerequisites

- Separate Intercom workspaces (or at minimum, separate apps in Developer Hub)
- Secret management solution (Vault, AWS Secrets Manager, GCP Secret Manager)
- CI/CD pipeline with environment variable support

## Environment Strategy

| Environment | Workspace | Token Type | Data | Webhooks |
|-------------|-----------|-----------|------|----------|
| Development | Dev/sandbox workspace | Dev access token | Test data | localhost via ngrok |
| Staging | Staging workspace | Staging token | Seed data | staging.example.com |
| Production | Production workspace | Production token | Real data | api.example.com |

## Instructions

Work through six steps. Read the Step 1 skeleton below to see the shape of the config, then open [references/implementation.md](references/implementation.md) for the complete code of every step.

1. **Environment Configuration** — a single `loadConfig()` reads `NODE_ENV` and merges shared secrets with per-environment defaults (debug, cache TTL, rate-limit concurrency). Skeleton below.
2. **Environment-Aware Client Factory** — a lazily-initialised `getClient()` that throws a clear, environment-named error when the token is missing.
3. **Secret Management by Platform** — store tokens in git-ignored `.env.<environment>` files locally and in GitHub Actions, AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault in CI/prod.
4. **Production Safety Guards** — an `EnvironmentGuard` with `requireProduction()` / `preventProduction()` so destructive jobs can never fire in the wrong workspace.
5. **Webhook URL per Environment** — map `NODE_ENV` to the correct public webhook URL so no code changes between deploys.
6. **Environment Validation on Startup** — probe the workspace on boot; fail fast in production, warn (but continue) elsewhere.

Step 1 skeleton — the config loader every other step depends on:

```typescript
// src/config/intercom.ts
function loadConfig(): IntercomEnvironmentConfig {
  const env = (process.env.NODE_ENV || "development") as IntercomEnvironmentConfig["environment"];
  const shared = {
    accessToken: process.env.INTERCOM_ACCESS_TOKEN!,
    webhookSecret: process.env.INTERCOM_WEBHOOK_SECRET!,
    environment: env,
    baseUrl: "https://api.intercom.io",
  };
  const envDefaults = {
    development: { debug: true, cache: { enabled: false, ttlSeconds: 0 }, rateLimit: { maxConcurrency: 2 } },
    staging: { debug: false, cache: { enabled: true, ttlSeconds: 60 }, rateLimit: { maxConcurrency: 5 } },
    production: { debug: false, cache: { enabled: true, ttlSeconds: 300 }, rateLimit: { maxConcurrency: 10 } },
  };
  return { ...shared, ...envDefaults[env] } as IntercomEnvironmentConfig;
}
export const intercomConfig = loadConfig();
```

See [references/implementation.md](references/implementation.md) for the full `IntercomEnvironmentConfig` interface, the client factory, all four secret-store commands, the guard class, the webhook map, the startup validator, and the GitHub Actions environment matrix.

## Output

Applying this skill produces:

- `src/config/intercom.ts` — the environment-aware config loader (`intercomConfig`).
- `src/intercom/client.ts` — the memoised `getClient()` factory.
- Per-environment secret sets: git-ignored `.env.<environment>` files locally plus tokens in your CI/prod secret store (`INTERCOM_DEV_TOKEN`, `INTERCOM_STAGING_TOKEN`, `INTERCOM_PROD_TOKEN`).
- An `EnvironmentGuard` wired into destructive and production-only operations.
- A startup log line confirming the connected workspace, e.g. `[Intercom] Connected to staging workspace`.

At runtime, `validateIntercomSetup()` prints `[Intercom] Validating <environment> setup...` followed by the connected admin, and throws (production) or warns (dev/staging) if the token cannot reach the workspace.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong workspace | Dev token used in staging | Validate workspace on startup |
| Token not found | Missing env file | Copy `.env.example` to `.env.<environment>` |
| Guard blocked operation | Environment mismatch | Verify `NODE_ENV` is correct |
| Webhook URL mismatch | Forgot to update URL | Use env-based URL config |

## Examples

Three worked, end-to-end scenarios are in [references/examples.md](references/examples.md):

- **Bootstrap a new staging workspace** — create the secret set, mirror it into CI, and confirm the workspace via startup validation.
- **Guard a destructive cleanup job** — use `preventProduction()` so a nightly test-contact purge can never run against production.
- **Route webhooks per environment in CI** — a GitHub Actions matrix that sets `NODE_ENV` so each deploy selects the correct token and webhook URL.

Quick taste — guarding a destructive job so it can never touch production:

```typescript
const guard = new EnvironmentGuard(intercomConfig.environment);

async function nightlyCleanup() {
  guard.preventProduction("nightlyCleanup"); // throws if NODE_ENV=production
  await deleteAllTestContacts();
}
```

## Resources

- [Full implementation walkthrough](references/implementation.md)
- [Worked examples](references/examples.md)
- [Intercom Developer Hub](https://developers.intercom.com/docs/build-an-integration/getting-started)
- [Authentication](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication)
- [12-Factor App Config](https://12factor.net/config)
- For observability setup, see the `intercom-observability` skill.
