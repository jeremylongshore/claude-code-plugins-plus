---
name: gamma-multi-env-setup
description: |
  Configure Gamma across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Gamma configurations.
  Trigger with phrases like "gamma environments", "gamma staging",
  "gamma dev prod", "gamma environment setup", "gamma config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, deployment]

---
# Gamma Multi-Environment Setup

## Overview

Configure Gamma API access across development, staging, and production environments. Since Gamma is a SaaS API with no self-hosted option, environment separation is achieved through separate workspaces (API keys), mock servers for development, and environment-aware client configuration.

## Prerequisites

- Separate Gamma workspaces (or at minimum separate API keys) per environment
- Secret management solution
- Completed `gamma-install-auth` setup

## Environment Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Development                                             │
│  API: localhost:9876 (mock server) or Gamma API          │
│  Key: GAMMA_API_KEY=gma_dev_xxx                         │
│  Mock: enabled (no credits consumed)                     │
├─────────────────────────────────────────────────────────┤
│  Staging                                                 │
│  API: public-api.gamma.app (separate workspace)         │
│  Key: GAMMA_API_KEY=gma_stg_xxx                         │
│  Mock: disabled                                          │
├─────────────────────────────────────────────────────────┤
│  Production                                              │
│  API: public-api.gamma.app (production workspace)       │
│  Key: GAMMA_API_KEY=gma_prod_xxx (from secret manager)  │
│  Mock: disabled                                          │
└─────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Environment Configuration

```typescript
// src/config/gamma.ts
interface GammaEnvConfig {
  apiKey: string;
  baseUrl: string;
  useMock: boolean;
  timeoutMs: number;
  maxRetries: number;
}

function getGammaConfig(): GammaEnvConfig {
  const env = process.env.NODE_ENV ?? "development";

  const configs: Record<string, Partial<GammaEnvConfig>> = {
    development: {
      baseUrl: process.env.GAMMA_MOCK === "true"
        ? "http://localhost:9876/v1.0"
        : "https://public-api.gamma.app/v1.0",
      useMock: process.env.GAMMA_MOCK === "true",
      timeoutMs: 60000,
      maxRetries: 1,
    },
    staging: {
      baseUrl: "https://public-api.gamma.app/v1.0",
      useMock: false,
      timeoutMs: 30000,
      maxRetries: 3,
    },
    production: {
      baseUrl: "https://public-api.gamma.app/v1.0",
      useMock: false,
      timeoutMs: 30000,
      maxRetries: 5,
    },
  };

  const apiKey = process.env.GAMMA_API_KEY;
  if (!apiKey && !configs[env]?.useMock) {
    throw new Error(`GAMMA_API_KEY required for ${env} environment`);
  }

  return {
    apiKey: apiKey ?? "mock-key",
    ...configs[env],
  } as GammaEnvConfig;
}

export const gammaConfig = getGammaConfig();
```

### Step 2: Environment-Aware Client Factory

```typescript
// src/gamma/factory.ts
import { createGammaClient } from "./client";
import { gammaConfig } from "../config/gamma";

let client: ReturnType<typeof createGammaClient> | null = null;

export function getGammaClient() {
  if (!client) {
    client = createGammaClient({
      apiKey: gammaConfig.apiKey,
      baseUrl: gammaConfig.baseUrl,
      timeoutMs: gammaConfig.timeoutMs,
    });
  }
  return client;
}

// Reset for testing
export function resetGammaClient() {
  client = null;
}
```

### Step 3: Environment Files

```bash
# .env.development
GAMMA_API_KEY=gma_dev_xxxxxxxxxxxx
GAMMA_MOCK=false
NODE_ENV=development
LOG_LEVEL=debug

# .env.test
GAMMA_MOCK=true
NODE_ENV=test
LOG_LEVEL=warn

# .env.staging
GAMMA_API_KEY=gma_stg_xxxxxxxxxxxx
NODE_ENV=staging
LOG_LEVEL=info

# .env.production (use secret manager instead)
# GAMMA_API_KEY loaded from AWS Secrets Manager / Vault
NODE_ENV=production
LOG_LEVEL=warn
```

### Step 4: Production Secret Management

```typescript
// src/config/secrets.ts
// For production, fetch API key from secret manager at startup

import { SecretsManager } from "@aws-sdk/client-secrets-manager";

let cachedKey: string | null = null;
let cacheExpiry = 0;

async function getProductionApiKey(): Promise<string> {
  if (cachedKey && Date.now() < cacheExpiry) return cachedKey;

  const sm = new SecretsManager({ region: "us-east-1" });
  const secret = await sm.getSecretValue({ SecretId: "gamma/api-key" });
  cachedKey = JSON.parse(secret.SecretString!).apiKey;
  cacheExpiry = Date.now() + 300000; // Cache for 5 minutes

  return cachedKey!;
}
```

### Step 5: Environment Guards

```typescript
// src/guards.ts
function blockProduction(operation: string) {
  if (process.env.NODE_ENV === "production") {
    throw new Error(`${operation} is blocked in production`);
  }
}

// Block destructive operations in production
async function deleteAllGenerations() {
  blockProduction("deleteAllGenerations");
  // ... cleanup logic for dev/staging
}

// Warn about credit-consuming operations in non-production
function warnCredits(env: string) {
  if (env !== "production" && !gammaConfig.useMock) {
    console.warn("WARNING: Using live Gamma API — credits will be consumed");
  }
}
```

### Step 6: CI/CD Environment Configuration

```yaml
# .github/workflows/gamma.yml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      GAMMA_MOCK: 'true'
      NODE_ENV: test
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test
      # Uses mock server — no API key needed, no credits consumed

  staging:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    env:
      GAMMA_API_KEY: ${{ secrets.GAMMA_STAGING_API_KEY }}
      NODE_ENV: staging
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run test:integration

  production:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    env:
      GAMMA_API_KEY: ${{ secrets.GAMMA_PRODUCTION_API_KEY }}
      NODE_ENV: production
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run deploy
```

## Environment Checklist

| Check | Dev | Test | Staging | Production |
|-------|-----|------|---------|------------|
| API key source | .env file | Not needed (mock) | GitHub Secret | Secret Manager |
| Mock mode | Optional | Yes | No | No |
| Debug logging | On | On | On | Off |
| Credit consumption | Optional | None | Real (staging workspace) | Real |
| Secret manager | No | No | Optional | Required |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong API key for env | Env var mismatch | Verify `NODE_ENV` and matching key |
| Credits consumed in dev | Mock mode off | Set `GAMMA_MOCK=true` in development |
| Secret fetch fails | IAM permissions | Check secret manager access policy |
| Production data in dev | No env guard | Add `blockProduction()` guards |

## Resources

- [12-Factor App Config](https://12factor.net/config)
- [Gamma API Key Management](https://gamma.app/settings)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)

## Next Steps

Proceed to `gamma-observability` for monitoring setup.
