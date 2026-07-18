---
name: klaviyo-multi-env-setup
description: 'Configure Klaviyo across development, staging, and production environments.

  Use when setting up multi-environment deployments, configuring per-environment API
  keys,

  or implementing environment-specific Klaviyo configurations.

  Trigger with phrases like "klaviyo environments", "klaviyo staging",

  "klaviyo dev prod", "klaviyo environment setup", "klaviyo config by env".

  '
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Multi-Environment Setup

## Overview

Configure Klaviyo across development, staging, and production with separate API
keys, environment detection, secret management, and production safeguards. Every
environment follows the same shape — detect the env, resolve its config, load
its secret, guard destructive/send operations. The lean workflow and first
skeleton live here; full step-by-step code lives in
[references/implementation.md](references/implementation.md).

## Prerequisites

- Separate Klaviyo accounts or API keys per environment
- Secret management solution (GCP Secret Manager, AWS Secrets Manager, Vault)
- `klaviyo-api` SDK installed

## Environment Strategy

| Environment | Klaviyo Account | API Key | Use Case |
|-------------|----------------|---------|----------|
| Development | Test account | `pk_test_dev_***` | Local development, exploration |
| Staging | Test account | `pk_test_staging_***` | Pre-prod validation, integration tests |
| Production | Production account | `pk_live_***` | Real customer data, live sends |

> **Important:** Klaviyo does not have a sandbox mode. Use a separate test account for dev/staging to avoid sending real emails.

## Instructions

The pattern is the same across all three environments; only the API key and the
per-env flags change. Read the matching section in
[references/implementation.md](references/implementation.md), then:

1. **Write the config module** — use Write/Edit to create `src/config/klaviyo.ts`
   with a `detectEnvironment()` helper and a per-env `ENV_CONFIGS` map that flips
   `enableSending`, cache, and rate-limit concurrency by environment.
2. **Store secrets per environment** — create one secret per env in your platform's
   secret store (`gcloud secrets create`, `aws secretsmanager create-secret`, or
   Vault). Never commit keys; local dev reads a git-ignored `.env.local`.
3. **Add environment guards** — wrap sends and deletions so non-production simply
   logs instead of touching real data (`guardCampaignSend`, `guardedProfileDeletion`).
4. **Wire multi-env CI** — a GitHub Actions matrix maps `staging`→staging key and
   `main`→prod key, verifies connectivity, then deploys.
5. **Validate on startup** — connect once, log the resolved account name, and warn
   loudly if a `pk_live_***` key is detected outside production.

### Config skeleton (first example)

```typescript
// src/config/klaviyo.ts — see reference for the full ENV_CONFIGS + getSession
type Environment = 'development' | 'staging' | 'production';

function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || 'development';
  if (['production', 'staging'].includes(env)) return env as Environment;
  return 'development';
}
// development/staging force enableSending:false; only production sends.
```

The full config module, per-platform secret commands, guard functions, the CI
matrix, and the startup validator are in
[references/implementation.md](references/implementation.md).

## Output

- `src/config/klaviyo.ts` resolving a typed config per environment
- Per-environment secrets stored in GCP / AWS / Vault (never committed)
- Send + deletion guards that no-op in dev/staging and act only in production
- A GitHub Actions matrix deploying staging and production with the right key
- Startup validation that logs the connected account and flags a leaked prod key

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong key for environment | Missing env-specific secret | Verify secret per environment |
| Production key in dev | Key leak risk | Add startup validation warning |
| Sends in staging | `enableSending` not checked | Add campaign send guard |
| Config merge fails | Invalid env value | Validate `NODE_ENV` on startup |

## Examples

**Block a campaign send outside production.** The guard reads the resolved config
and throws when sending is disabled, so a staging run can never email real
customers:

```typescript
guardCampaignSend();   // throws in dev/staging (enableSending:false), passes in prod
```

**Catch a leaked production key in staging.** Startup validation warns when a
`pk_live_***` key is present outside production:

```
[Klaviyo] Environment: staging
[Klaviyo] Sending enabled: false
[Klaviyo] WARNING: Production API key detected in non-production environment!
```

The full config module, secret-store commands for each platform, the guard
implementations, the CI matrix, and the startup validator are in
[references/implementation.md](references/implementation.md).

## Resources

- [Klaviyo Authentication](https://developers.klaviyo.com/en/docs/authenticate_)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [12-Factor App Config](https://12factor.net/config)
- [Full implementation walkthrough](references/implementation.md) — verbatim config, secrets, guards, CI, and startup validation
- For observability setup, see the `klaviyo-observability` skill.
