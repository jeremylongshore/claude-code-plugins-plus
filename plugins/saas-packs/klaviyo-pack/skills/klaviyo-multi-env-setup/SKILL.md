---
name: klaviyo-multi-env-setup
description: |
  Configure Klaviyo across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment API keys,
  or implementing environment-specific Klaviyo configurations.
  Trigger with phrases like "klaviyo environments", "klaviyo staging",
  "klaviyo dev prod", "klaviyo environment setup", "klaviyo config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Multi-Environment Setup

## Overview

Configure Klaviyo across development, staging, and production with separate API keys, environment detection, secret management, and production safeguards.

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

### Step 1: Environment Configuration

```typescript
// src/config/klaviyo.ts
import { ApiKeySession } from 'klaviyo-api';

type Environment = 'development' | 'staging' | 'production';

interface KlaviyoEnvConfig {
  privateKey: string;
  revision: string;
  webhookSecret: string;
  enableSending: boolean;
  rateLimitConcurrency: number;
  cacheEnabled: boolean;
  cacheTtlMs: number;
}

function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || 'development';
  if (['production', 'staging'].includes(env)) return env as Environment;
  return 'development';
}

const ENV_CONFIGS: Record<Environment, Partial<KlaviyoEnvConfig>> = {
  development: {
    enableSending: false,     // Never send real emails from dev
    rateLimitConcurrency: 5,
    cacheEnabled: false,
    cacheTtlMs: 0,
  },
  staging: {
    enableSending: false,     // Only send to test addresses
    rateLimitConcurrency: 10,
    cacheEnabled: true,
    cacheTtlMs: 60_000,
  },
  production: {
    enableSending: true,
    rateLimitConcurrency: 20,
    cacheEnabled: true,
    cacheTtlMs: 300_000,
  },
};

export function getKlaviyoConfig(): KlaviyoEnvConfig {
  const env = detectEnvironment();
  const envConfig = ENV_CONFIGS[env];

  return {
    privateKey: process.env.KLAVIYO_PRIVATE_KEY || '',
    revision: '2024-10-15',
    webhookSecret: process.env.KLAVIYO_WEBHOOK_SIGNING_SECRET || '',
    enableSending: false,
    rateLimitConcurrency: 10,
    cacheEnabled: true,
    cacheTtlMs: 60_000,
    ...envConfig,
  };
}

export function getSession(): ApiKeySession {
  const config = getKlaviyoConfig();
  if (!config.privateKey) throw new Error(`KLAVIYO_PRIVATE_KEY not set for ${detectEnvironment()}`);
  return new ApiKeySession(config.privateKey);
}
```

### Step 2: Secret Management by Platform

#### GCP Secret Manager
```bash
# Create secrets per environment
echo -n "pk_test_dev_***" | gcloud secrets create klaviyo-key-dev --data-file=-
echo -n "pk_test_staging_***" | gcloud secrets create klaviyo-key-staging --data-file=-
echo -n "pk_live_***" | gcloud secrets create klaviyo-key-prod --data-file=-

# Access in Cloud Run
gcloud run deploy my-app \
  --set-secrets=KLAVIYO_PRIVATE_KEY=klaviyo-key-prod:latest
```

#### AWS Secrets Manager
```bash
aws secretsmanager create-secret \
  --name klaviyo/production/private-key \
  --secret-string "pk_live_***"

aws secretsmanager create-secret \
  --name klaviyo/staging/private-key \
  --secret-string "pk_test_staging_***"
```

```typescript
// Load from AWS at startup
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

async function loadKlaviyoKey(env: string): Promise<string> {
  const client = new SecretsManager();
  const result = await client.getSecretValue({ SecretId: `klaviyo/${env}/private-key` });
  return result.SecretString!;
}
```

#### Local Development
```bash
# .env.local (git-ignored)
KLAVIYO_PRIVATE_KEY=pk_test_dev_********************************
KLAVIYO_PUBLIC_KEY=DevKey
KLAVIYO_WEBHOOK_SIGNING_SECRET=whsec_test_***
NODE_ENV=development
```

### Step 3: Environment Guards

```typescript
// src/klaviyo/guards.ts

/** Prevent dangerous operations in non-production environments */
export function requireProduction(operation: string): void {
  const env = process.env.NODE_ENV;
  if (env !== 'production') {
    throw new Error(`[Klaviyo Guard] ${operation} is only allowed in production (current: ${env})`);
  }
}

/** Prevent campaign sends in non-production */
export function guardCampaignSend(): void {
  const config = getKlaviyoConfig();
  if (!config.enableSending) {
    throw new Error('[Klaviyo Guard] Campaign sending is disabled in this environment');
  }
}

/** Restrict deletion operations */
export async function guardedProfileDeletion(profileId: string): Promise<void> {
  const env = process.env.NODE_ENV;

  // In dev/staging, just log instead of deleting
  if (env !== 'production') {
    console.log(`[Klaviyo Guard] Would delete profile ${profileId} (skipped in ${env})`);
    return;
  }

  // In production, proceed with actual deletion
  const dataPrivacyApi = new DataPrivacyApi(getSession());
  await dataPrivacyApi.requestProfileDeletion({
    data: {
      type: 'data-privacy-deletion-job',
      attributes: { profile: { data: { type: 'profile', id: profileId } } },
    },
  });
}
```

### Step 4: GitHub Actions Multi-Environment CI

```yaml
name: Deploy
on:
  push:
    branches: [main, staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - branch: staging
            env: staging
            secret_key: KLAVIYO_KEY_STAGING
          - branch: main
            env: production
            secret_key: KLAVIYO_KEY_PROD
    if: github.ref == format('refs/heads/{0}', matrix.branch)
    env:
      NODE_ENV: ${{ matrix.env }}
      KLAVIYO_PRIVATE_KEY: ${{ secrets[matrix.secret_key] }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test
      - name: Verify Klaviyo connectivity
        run: |
          curl -s -w "HTTP %{http_code}" -o /dev/null \
            -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
            -H "revision: 2024-10-15" \
            "https://a.klaviyo.com/api/accounts/"
      - run: npm run deploy:${{ matrix.env }}
```

### Step 5: Environment Validation on Startup

```typescript
// src/startup.ts
import { AccountsApi } from 'klaviyo-api';
import { getSession, getKlaviyoConfig } from './config/klaviyo';

export async function validateKlaviyoEnvironment(): Promise<void> {
  const config = getKlaviyoConfig();
  console.log(`[Klaviyo] Environment: ${process.env.NODE_ENV}`);
  console.log(`[Klaviyo] Sending enabled: ${config.enableSending}`);
  console.log(`[Klaviyo] Cache: ${config.cacheEnabled ? `enabled (${config.cacheTtlMs}ms)` : 'disabled'}`);

  try {
    const api = new AccountsApi(getSession());
    const accounts = await api.getAccounts();
    const name = accounts.body.data[0].attributes.contactInformation?.organizationName;
    console.log(`[Klaviyo] Connected to: ${name}`);

    // Warn if production key is used in non-production
    if (process.env.NODE_ENV !== 'production' && config.privateKey.includes('live')) {
      console.error('[Klaviyo] WARNING: Production API key detected in non-production environment!');
    }
  } catch (error: any) {
    console.error(`[Klaviyo] Connection failed: ${error.status} ${error.message}`);
    if (process.env.NODE_ENV === 'production') process.exit(1);
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong key for environment | Missing env-specific secret | Verify secret per environment |
| Production key in dev | Key leak risk | Add startup validation warning |
| Sends in staging | `enableSending` not checked | Add campaign send guard |
| Config merge fails | Invalid env value | Validate `NODE_ENV` on startup |

## Resources

- [Klaviyo Authentication](https://developers.klaviyo.com/en/docs/authenticate_)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps

For observability setup, see `klaviyo-observability`.
