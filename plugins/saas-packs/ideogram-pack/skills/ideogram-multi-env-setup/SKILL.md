---
name: ideogram-multi-env-setup
description: |
  Configure Ideogram across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment keys,
  or implementing environment-specific Ideogram configurations.
  Trigger with phrases like "ideogram environments", "ideogram staging",
  "ideogram dev prod", "ideogram environment setup", "ideogram multi-env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, deployment, environments]

---
# Ideogram Multi-Environment Setup

## Overview
Configure Ideogram API access across development, staging, and production with isolated API keys, environment-specific model/speed settings, and proper secret management. Each environment gets its own key and configuration to prevent cross-environment issues.

## Environment Strategy

| Environment | API Key Source | Model | Speed | Cache | Billing |
|-------------|---------------|-------|-------|-------|---------|
| Development | `.env.local` | V_2_TURBO | TURBO | Disabled | Minimal top-up |
| Staging | CI/CD secrets | V_2 | DEFAULT | 5 min TTL | Moderate |
| Production | Secret manager | V_2 or V3 | DEFAULT | 10 min TTL | Full auto top-up |

## Instructions

### Step 1: Configuration Structure
```typescript
// config/ideogram.ts
type Environment = "development" | "staging" | "production";

interface IdeogramConfig {
  apiKey: string;
  defaultModel: string;
  renderingSpeed: string;
  timeout: number;
  maxRetries: number;
  concurrency: number;
  cache: { enabled: boolean; ttlSeconds: number };
  debug: boolean;
}

const configs: Record<Environment, Omit<IdeogramConfig, "apiKey">> = {
  development: {
    defaultModel: "V_2_TURBO",
    renderingSpeed: "TURBO",
    timeout: 30000,
    maxRetries: 1,
    concurrency: 2,
    cache: { enabled: false, ttlSeconds: 60 },
    debug: true,
  },
  staging: {
    defaultModel: "V_2",
    renderingSpeed: "DEFAULT",
    timeout: 60000,
    maxRetries: 3,
    concurrency: 5,
    cache: { enabled: true, ttlSeconds: 300 },
    debug: false,
  },
  production: {
    defaultModel: "V_2",
    renderingSpeed: "DEFAULT",
    timeout: 60000,
    maxRetries: 5,
    concurrency: 8,
    cache: { enabled: true, ttlSeconds: 600 },
    debug: false,
  },
};

export function getIdeogramConfig(): IdeogramConfig {
  const env = detectEnvironment();
  const apiKey = getApiKeyForEnv(env);

  if (!apiKey) {
    throw new Error(`IDEOGRAM_API_KEY not set for environment: ${env}`);
  }

  return { ...configs[env], apiKey };
}

function detectEnvironment(): Environment {
  const env = process.env.NODE_ENV || "development";
  if (env === "production") return "production";
  if (env === "staging" || process.env.VERCEL_ENV === "preview") return "staging";
  return "development";
}

function getApiKeyForEnv(env: Environment): string {
  const envVar = {
    development: "IDEOGRAM_API_KEY_DEV",
    staging: "IDEOGRAM_API_KEY_STAGING",
    production: "IDEOGRAM_API_KEY",
  }[env];

  return process.env[envVar] || process.env.IDEOGRAM_API_KEY || "";
}
```

### Step 2: Environment Files
```bash
# .env.local (development -- git-ignored)
IDEOGRAM_API_KEY_DEV=your-dev-key
NODE_ENV=development

# .env.staging (CI only)
IDEOGRAM_API_KEY_STAGING=your-staging-key
NODE_ENV=staging

# Production: use secret manager, never .env files
```

### Step 3: Secret Management by Platform
```bash
set -euo pipefail
# --- GitHub Actions ---
gh secret set IDEOGRAM_API_KEY_STAGING --env staging
gh secret set IDEOGRAM_API_KEY --env production

# --- AWS Secrets Manager ---
aws secretsmanager create-secret \
  --name ideogram/staging/api-key \
  --secret-string "your-staging-key"

aws secretsmanager create-secret \
  --name ideogram/production/api-key \
  --secret-string "your-production-key"

# --- GCP Secret Manager ---
echo -n "your-staging-key" | gcloud secrets create ideogram-api-key-staging --data-file=-
echo -n "your-production-key" | gcloud secrets create ideogram-api-key-prod --data-file=-
```

### Step 4: GitHub Actions with Environment Secrets
```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    env:
      IDEOGRAM_API_KEY_STAGING: ${{ secrets.IDEOGRAM_API_KEY_STAGING }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - run: npm run deploy:staging

  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    needs: deploy-staging
    env:
      IDEOGRAM_API_KEY: ${{ secrets.IDEOGRAM_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - run: npm run deploy:production
```

### Step 5: Startup Validation
```typescript
import { z } from "zod";

const configSchema = z.object({
  apiKey: z.string().min(10, "API key too short"),
  defaultModel: z.enum(["V_1", "V_1_TURBO", "V_2", "V_2_TURBO", "V_2A", "V_2A_TURBO"]),
  timeout: z.number().min(5000).max(120000),
  concurrency: z.number().min(1).max(10),
});

// Validate at application startup
try {
  const config = configSchema.parse(getIdeogramConfig());
  console.log(`Ideogram configured for ${detectEnvironment()} (model: ${config.defaultModel})`);
} catch (err: any) {
  console.error("Ideogram config invalid:", err.message);
  process.exit(1);
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment detected | Missing `NODE_ENV` | Set in deployment platform |
| Secret not found | Wrong variable name | Check env-specific key name |
| Cross-env data leak | Shared API key | Create separate keys per env |
| Staging using prod key | No env isolation | Validate key identity at startup |

## Output
- Environment-aware configuration with separate API keys
- Secret management for GitHub Actions, AWS, and GCP
- Startup validation preventing misconfiguration
- CI/CD pipeline with environment gates

## Resources
- [Ideogram API Setup](https://developer.ideogram.ai/ideogram-api/api-setup)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments)

## Next Steps
For deployment patterns, see `ideogram-deploy-integration`.
