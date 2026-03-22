---
name: langfuse-multi-env-setup
description: |
  Configure Langfuse across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment keys,
  or implementing environment-specific Langfuse configurations.
  Trigger with phrases like "langfuse environments", "langfuse staging",
  "langfuse dev prod", "langfuse environment setup", "langfuse config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, deployment]

---
# Langfuse Multi-Environment Setup

## Overview
Configure Langfuse across dev/staging/production with isolated API keys, environment-specific SDK settings, secret management, and CI/CD integration to prevent cross-environment data leakage.

## Prerequisites
- Separate Langfuse API key pairs per environment (or separate projects)
- Secret management solution (env vars, Vault, AWS/GCP secrets)
- CI/CD pipeline with environment-aware deployment

## Environment Strategy

| Environment | API Key Source | Langfuse Project | Settings |
|-------------|---------------|-----------------|----------|
| Development | `.env.local` | Dev project | Debug on, flush immediately, 100% sampling |
| Staging | CI/CD secrets | Staging project | Prod-like settings, 50% sampling |
| Production | Secret manager | Prod project | Optimized batching, 10% sampling |

## Instructions

### Step 1: Environment-Specific Configuration

```typescript
// src/config/langfuse.ts
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseClient } from "@langfuse/client";

type Env = "development" | "staging" | "production";

interface LangfuseEnvConfig {
  exportIntervalMillis: number;
  maxExportBatchSize: number;
  debug: boolean;
  sampleRate: number;
}

const ENV_CONFIGS: Record<Env, LangfuseEnvConfig> = {
  development: {
    exportIntervalMillis: 1000,
    maxExportBatchSize: 1,
    debug: true,
    sampleRate: 1.0,
  },
  staging: {
    exportIntervalMillis: 5000,
    maxExportBatchSize: 25,
    debug: false,
    sampleRate: 0.5,
  },
  production: {
    exportIntervalMillis: 10000,
    maxExportBatchSize: 50,
    debug: false,
    sampleRate: 0.1,
  },
};

function detectEnvironment(): Env {
  const env = process.env.NODE_ENV || "development";
  if (env === "production") return "production";
  if (env === "staging" || process.env.VERCEL_ENV === "preview") return "staging";
  return "development";
}

export function initLangfuse() {
  const env = detectEnvironment();
  const config = ENV_CONFIGS[env];

  // Validate credentials
  const required = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"];
  for (const key of required) {
    if (!process.env[key]) {
      throw new Error(`${key} not set for environment: ${env}`);
    }
  }

  // Initialize OTel with env-specific settings
  const processor = new LangfuseSpanProcessor({
    exportIntervalMillis: config.exportIntervalMillis,
    maxExportBatchSize: config.maxExportBatchSize,
  });

  const sdk = new NodeSDK({ spanProcessors: [processor] });
  sdk.start();

  // Client for prompts, datasets, scores
  const client = new LangfuseClient();

  console.log(`Langfuse initialized [${env}] (sample: ${config.sampleRate * 100}%)`);

  return { sdk, client, env, config };
}
```

### Step 2: Environment Variable Files

```bash
# .env.local (development -- git-ignored)
LANGFUSE_PUBLIC_KEY=pk-lf-dev-...
LANGFUSE_SECRET_KEY=sk-lf-dev-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
NODE_ENV=development

# .env.staging (used by CI/CD)
LANGFUSE_BASE_URL=https://cloud.langfuse.com
NODE_ENV=staging
# Keys injected via CI secrets

# .env.production (used by CI/CD)
LANGFUSE_BASE_URL=https://cloud.langfuse.com
NODE_ENV=production
# Keys injected via secret manager
```

```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

### Step 3: Secret Management

```bash
set -euo pipefail
# GitHub Actions: Add per-environment secrets
# Settings > Environments > staging > Secrets
# Settings > Environments > production > Secrets

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name "langfuse/production/public-key" \
  --secret-string "pk-lf-prod-..."

aws secretsmanager create-secret \
  --name "langfuse/production/secret-key" \
  --secret-string "sk-lf-prod-..."

# GCP Secret Manager
echo -n "pk-lf-prod-..." | gcloud secrets create langfuse-public-key-prod --data-file=-
echo -n "sk-lf-prod-..." | gcloud secrets create langfuse-secret-key-prod --data-file=-
```

### Step 4: CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main, staging]

jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/staging'
    runs-on: ubuntu-latest
    environment: staging
    env:
      LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
      LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
      LANGFUSE_BASE_URL: https://cloud.langfuse.com
      NODE_ENV: staging
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build && npm run deploy:staging

  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    env:
      LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
      LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
      LANGFUSE_BASE_URL: https://cloud.langfuse.com
      NODE_ENV: production
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build && npm run deploy:production
```

### Step 5: Startup Validation with Zod

```typescript
import { z } from "zod";

const langfuseConfigSchema = z.object({
  LANGFUSE_PUBLIC_KEY: z.string().startsWith("pk-lf-", "Must start with pk-lf-"),
  LANGFUSE_SECRET_KEY: z.string().startsWith("sk-lf-", "Must start with sk-lf-"),
  LANGFUSE_BASE_URL: z.string().url().optional(),
  NODE_ENV: z.enum(["development", "staging", "production"]).default("development"),
});

// Validate at startup -- fail fast on misconfiguration
const config = langfuseConfigSchema.parse(process.env);
console.log(`Langfuse config validated for ${config.NODE_ENV}`);
```

## Cross-Environment Safety

| Risk | Mitigation |
|------|-----------|
| Dev traces in prod project | Separate API keys per environment |
| Prod keys in dev env | Validate key prefix at startup |
| Leaked keys in git | `.env` in `.gitignore`, secret scanning in CI |
| Wrong env detected | Explicit `NODE_ENV` in deployment config |
| Config drift | Zod schema validation at startup |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Missing `NODE_ENV` | Set explicitly in deployment config |
| Secret not found | Wrong secret path | Verify secret manager paths match |
| Cross-env data leak | Shared API key | Use separate keys per environment |
| Startup crash | Missing config | Add Zod validation with clear error messages |

## Resources
- [TypeScript SDK Setup](https://langfuse.com/docs/observability/sdk/typescript/setup)
- [Self-Hosting Configuration](https://langfuse.com/self-hosting/configuration)
- [Advanced SDK Configuration](https://langfuse.com/docs/observability/sdk/typescript/advanced-usage)
