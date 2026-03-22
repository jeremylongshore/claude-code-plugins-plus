---
name: hubspot-multi-env-setup
description: |
  Configure HubSpot across development, staging, and production environments.
  Use when setting up per-environment HubSpot portals, configuring separate
  access tokens, or implementing environment isolation for HubSpot integrations.
  Trigger with phrases like "hubspot environments", "hubspot staging",
  "hubspot dev prod", "hubspot test account", "hubspot config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Multi-Environment Setup

## Overview

Configure HubSpot integrations across dev/staging/production using separate HubSpot portals (test accounts), environment-specific tokens, and configuration management.

## Prerequisites

- HubSpot developer account (for test portals)
- Secret management solution (Vault, AWS SM, GCP SM)
- CI/CD pipeline with environment variables

## Instructions

### Step 1: Environment Strategy

| Environment | HubSpot Portal | Token Type | Data |
|-------------|---------------|------------|------|
| Development | Developer test account | Test private app token | Fake/seed data |
| Staging | Sandbox portal | Staging private app token | Anonymized copy |
| Production | Production portal | Production private app token | Real customer data |

Create a free developer test account at [developers.hubspot.com](https://developers.hubspot.com/get-started).

### Step 2: Environment Configuration

```typescript
// src/config/hubspot.ts
import * as hubspot from '@hubspot/api-client';

type Environment = 'development' | 'staging' | 'production';

interface HubSpotEnvConfig {
  accessToken: string;
  portalId: string;
  retries: number;
  cacheTtlMs: number;
}

const ENV_CONFIG: Record<Environment, Partial<HubSpotEnvConfig>> = {
  development: {
    retries: 1,
    cacheTtlMs: 0, // no cache in dev for fresh data
  },
  staging: {
    retries: 3,
    cacheTtlMs: 60000,
  },
  production: {
    retries: 5,
    cacheTtlMs: 300000,
  },
};

function getEnvironment(): Environment {
  const env = process.env.NODE_ENV || 'development';
  if (['development', 'staging', 'production'].includes(env)) {
    return env as Environment;
  }
  return 'development';
}

export function getHubSpotConfig(): HubSpotEnvConfig {
  const env = getEnvironment();
  return {
    accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
    portalId: process.env.HUBSPOT_PORTAL_ID!,
    ...ENV_CONFIG[env],
  } as HubSpotEnvConfig;
}

export function createHubSpotClient(): hubspot.Client {
  const config = getHubSpotConfig();
  return new hubspot.Client({
    accessToken: config.accessToken,
    numberOfApiCallRetries: config.retries,
  });
}
```

### Step 3: Per-Environment Secrets

```bash
# .env.development (git-ignored)
HUBSPOT_ACCESS_TOKEN=pat-na1-test-xxxxx    # developer test account
HUBSPOT_PORTAL_ID=12345678

# .env.staging (git-ignored)
HUBSPOT_ACCESS_TOKEN=pat-na1-staging-xxxxx  # sandbox portal
HUBSPOT_PORTAL_ID=23456789

# .env.production (NEVER in files -- use secret manager)
# Stored in AWS Secrets Manager / GCP Secret Manager / Vault
```

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name hubspot/production \
  --secret-string '{"access_token":"pat-na1-xxxxx","portal_id":"34567890"}'

# Load at runtime
aws secretsmanager get-secret-value --secret-id hubspot/production \
  --query SecretString --output text | jq -r .access_token

# GCP Secret Manager
echo -n "pat-na1-xxxxx" | gcloud secrets create hubspot-access-token --data-file=-
gcloud secrets versions access latest --secret=hubspot-access-token
```

### Step 4: Environment Isolation Guards

```typescript
// Prevent accidental production operations in non-prod
function requireProduction(operation: string): void {
  if (getEnvironment() !== 'production') {
    throw new Error(
      `"${operation}" is only allowed in production. ` +
      `Current environment: ${getEnvironment()}`
    );
  }
}

// Prevent destructive operations in production without confirmation
function requireNonProduction(operation: string): void {
  if (getEnvironment() === 'production') {
    throw new Error(
      `"${operation}" is blocked in production. ` +
      `Use the staging environment instead.`
    );
  }
}

// Usage
async function bulkDeleteContacts(ids: string[]) {
  requireNonProduction('bulkDeleteContacts'); // safety guard
  for (const id of ids) {
    await client.crm.contacts.basicApi.archive(id);
  }
}

async function sendMarketingEmail(emailId: string) {
  requireProduction('sendMarketingEmail'); // only send real emails in prod
  // ...
}
```

### Step 5: CI/CD Environment Matrix

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    strategy:
      matrix:
        environment: [staging, production]
    environment: ${{ matrix.environment }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to ${{ matrix.environment }}
        env:
          HUBSPOT_ACCESS_TOKEN: ${{ secrets[format('HUBSPOT_{0}_TOKEN', matrix.environment)] }}
          HUBSPOT_PORTAL_ID: ${{ secrets[format('HUBSPOT_{0}_PORTAL_ID', matrix.environment)] }}
          NODE_ENV: ${{ matrix.environment }}
        run: |
          npm ci
          npm run build
          npm run deploy
```

## Output

- Separate HubSpot portals per environment
- Environment-specific configuration with proper defaults
- Secrets stored in platform secret managers (not env files)
- Guards preventing cross-environment mistakes
- CI/CD deploying to correct environment

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong portal in staging | Env var pointing to prod | Verify `HUBSPOT_PORTAL_ID` matches environment |
| Guard triggered | Running prod code in dev | Check `NODE_ENV` is set correctly |
| Secret not found | Missing secret manager entry | Create secret with `aws secretsmanager create-secret` |
| Test data in production | Environment leak | Add portal ID validation at startup |

## Resources

- [HubSpot Developer Test Accounts](https://developers.hubspot.com/docs/guides/apps/developer-test-accounts)
- [12-Factor App Config](https://12factor.net/config)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)

## Next Steps

For observability setup, see `hubspot-observability`.
