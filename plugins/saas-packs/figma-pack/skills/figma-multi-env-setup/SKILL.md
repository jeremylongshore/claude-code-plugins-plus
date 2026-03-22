---
name: figma-multi-env-setup
description: |
  Configure Figma API access across dev, staging, and production environments.
  Use when setting up per-environment tokens, managing multiple Figma files,
  or isolating development from production Figma resources.
  Trigger with phrases like "figma environments", "figma staging",
  "figma dev prod", "figma environment config".
allowed-tools: Read, Write, Edit, Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Multi-Environment Setup

## Overview
Configure separate Figma API credentials and file targets per environment. Use different PATs with minimal scopes, point to different Figma files, and prevent accidental production operations from dev.

## Prerequisites
- Separate Figma PATs for each environment
- Secret management solution
- Environment detection in application

## Instructions

### Step 1: Environment Strategy

| Environment | PAT Scopes | Figma File | Cache TTL |
|-------------|-----------|------------|-----------|
| Development | `file_content:read` | Copy of design file | 10s (fast iteration) |
| Staging | `file_content:read`, `file_comments:read` | Staging branch/file | 60s |
| Production | `file_content:read`, `webhooks:write` | Production design file | 300s |

### Step 2: Configuration by Environment
```typescript
// src/config/figma.ts
interface FigmaEnvConfig {
  token: string;
  fileKey: string;
  cacheTTL: number;
  webhookPasscode?: string;
  maxConcurrency: number;
}

function getFigmaConfig(): FigmaEnvConfig {
  const env = process.env.NODE_ENV || 'development';

  const configs: Record<string, Partial<FigmaEnvConfig>> = {
    development: {
      token: process.env.FIGMA_PAT_DEV!,
      fileKey: process.env.FIGMA_FILE_KEY_DEV!,
      cacheTTL: 10_000,
      maxConcurrency: 1,
    },
    staging: {
      token: process.env.FIGMA_PAT_STAGING!,
      fileKey: process.env.FIGMA_FILE_KEY_STAGING!,
      cacheTTL: 60_000,
      maxConcurrency: 3,
    },
    production: {
      token: process.env.FIGMA_PAT_PROD!,
      fileKey: process.env.FIGMA_FILE_KEY_PROD!,
      cacheTTL: 300_000,
      maxConcurrency: 5,
      webhookPasscode: process.env.FIGMA_WEBHOOK_PASSCODE,
    },
  };

  const config = configs[env];
  if (!config?.token) throw new Error(`Figma token not configured for env: ${env}`);
  if (!config?.fileKey) throw new Error(`Figma file key not configured for env: ${env}`);

  return config as FigmaEnvConfig;
}
```

### Step 3: Environment Files
```bash
# .env.development
FIGMA_PAT_DEV="figd_dev-token-read-only"
FIGMA_FILE_KEY_DEV="devFileKey123"

# .env.staging
FIGMA_PAT_STAGING="figd_staging-token"
FIGMA_FILE_KEY_STAGING="stagingFileKey456"

# .env.production (stored in secret manager, not in repo)
FIGMA_PAT_PROD="figd_prod-token"
FIGMA_FILE_KEY_PROD="prodFileKey789"
FIGMA_WEBHOOK_PASSCODE="webhook-secret"

# .env.example (committed to repo as template)
FIGMA_PAT_DEV=
FIGMA_FILE_KEY_DEV=
```

### Step 4: Secret Management
```bash
# GitHub Actions -- use environment-scoped secrets
gh secret set FIGMA_PAT_PROD --env production --body "figd_..."
gh secret set FIGMA_PAT_STAGING --env staging --body "figd_..."

# Google Cloud Secret Manager
echo -n "figd_prod-token" | gcloud secrets create figma-pat-prod --data-file=-
echo -n "figd_staging-token" | gcloud secrets create figma-pat-staging --data-file=-

# Load in Cloud Run
gcloud run deploy my-service \
  --set-secrets="FIGMA_PAT_PROD=figma-pat-prod:latest"
```

### Step 5: Environment Guards
```typescript
// Prevent production-specific operations in non-production
function requireProduction(operation: string) {
  if (process.env.NODE_ENV !== 'production') {
    throw new Error(
      `${operation} is only allowed in production. ` +
      `Current env: ${process.env.NODE_ENV}`
    );
  }
}

// Prevent destructive operations in production
function blockInProduction(operation: string) {
  if (process.env.NODE_ENV === 'production') {
    throw new Error(`${operation} is blocked in production for safety`);
  }
}

// Usage
async function createWebhook(config: any) {
  requireProduction('createWebhook'); // Only in prod
  return fetch('https://api.figma.com/v2/webhooks', { ... });
}

async function deleteAllCachedData() {
  blockInProduction('deleteAllCachedData'); // Never in prod
  await cache.clear();
}
```

## Output
- Per-environment Figma configuration
- Secrets stored in appropriate secret managers
- Environment guards preventing cross-env mistakes
- Template env files for team onboarding

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong file in dev | Using prod file key | Verify FIGMA_FILE_KEY_DEV |
| PAT expired in CI | 90-day expiry | Set rotation reminder per environment |
| Staging webhook pointing to prod | Wrong endpoint URL | Verify webhook endpoint per env |
| Config not loading | Missing NODE_ENV | Set NODE_ENV in deployment config |

## Resources
- [Figma Authentication](https://developers.figma.com/docs/rest-api/authentication/)
- [12-Factor App Config](https://12factor.net/config)
- [GitHub Environments](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment)

## Next Steps
For observability setup, see `figma-observability`.
