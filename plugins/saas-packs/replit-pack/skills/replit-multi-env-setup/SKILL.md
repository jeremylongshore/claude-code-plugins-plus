---
name: replit-multi-env-setup
description: |
  Configure Replit dev/staging/production environments with separate databases, secrets, and deployment tiers.
  Use when setting up multi-environment deployments, managing per-environment secrets,
  or implementing environment-specific Replit configurations.
  Trigger with phrases like "replit environments", "replit staging",
  "replit dev prod", "replit environment setup", "replit separate databases".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, deployment, environments]

---
# Replit Multi-Environment Setup

## Overview
Configure development, staging, and production environments on Replit. Leverages Replit's built-in dev/prod database separation, environment-specific secrets, and deployment types. Covers the Replit-native approach (single Repl, dual databases) and the multi-Repl approach (separate Repls per environment).

## Prerequisites
- Replit Core or Teams plan (deployment access)
- PostgreSQL provisioned in Database pane
- Understanding of Replit Secrets

## Environment Strategy

### Approach 1: Single Repl, Dual Databases (Recommended)
Replit natively provides separate development and production databases:
```markdown
Workspace "Run" button → Development database
Deployed app (.replit.app) → Production database

Both use the same DATABASE_URL env var — Replit routes automatically.
No code changes needed between environments.
```

### Approach 2: Multi-Repl (Staging + Production)
For teams that need a staging environment:
```markdown
Repl 1: my-app-staging → Autoscale deployment → staging.replit.app
Repl 2: my-app-prod   → Reserved VM deployment → app.example.com

Each Repl has its own:
- Secrets (different API keys per environment)
- PostgreSQL database (separate data)
- Deployment configuration
- GitHub branch (staging → staging, main → production)
```

## Instructions

### Step 1: Environment Detection
```typescript
// src/config/environment.ts
type Environment = 'development' | 'staging' | 'production';

export function detectEnvironment(): Environment {
  // Replit deployment context
  if (process.env.REPL_DEPLOYMENT) {
    // Check if this is the staging Repl
    if (process.env.REPL_SLUG?.includes('staging')) return 'staging';
    return 'production';
  }

  // Workspace "Run" context
  if (process.env.REPL_SLUG) return 'development';

  // Fallback to NODE_ENV
  const env = process.env.NODE_ENV || 'development';
  if (env === 'production') return 'production';
  if (env === 'staging') return 'staging';
  return 'development';
}

export const ENV = detectEnvironment();
export const IS_PROD = ENV === 'production';
```

### Step 2: Environment-Specific Configuration
```typescript
// src/config/index.ts
import { ENV, IS_PROD } from './environment';

const configs = {
  development: {
    logLevel: 'debug',
    corsOrigins: ['*'],
    rateLimit: { windowMs: 60000, max: 1000 },
    cache: { ttlMs: 5000 },
    features: { debugEndpoints: true },
  },
  staging: {
    logLevel: 'info',
    corsOrigins: ['https://staging.example.com'],
    rateLimit: { windowMs: 60000, max: 200 },
    cache: { ttlMs: 30000 },
    features: { debugEndpoints: true },
  },
  production: {
    logLevel: 'warn',
    corsOrigins: ['https://app.example.com'],
    rateLimit: { windowMs: 60000, max: 100 },
    cache: { ttlMs: 300000 },
    features: { debugEndpoints: false },
  },
};

export const config = {
  env: ENV,
  port: parseInt(process.env.PORT || '3000'),
  ...configs[ENV],
  db: {
    // DATABASE_URL auto-switches between dev and prod on Replit
    url: process.env.DATABASE_URL,
  },
};

// Validate production secrets
if (IS_PROD) {
  const required = ['DATABASE_URL', 'JWT_SECRET'];
  const missing = required.filter(k => !process.env[k]);
  if (missing.length) {
    console.error(`FATAL: Missing production secrets: ${missing.join(', ')}`);
    process.exit(1);
  }
}
```

### Step 3: Separate Secrets Per Environment
```markdown
For Single Repl (dev/prod separation):
- All secrets set once in Secrets tab
- DATABASE_URL auto-switches (Replit manages)
- Same JWT_SECRET for both (or use REPL_IDENTITY for dev)

For Multi-Repl (staging + prod):
- Each Repl has its own Secrets tab
- staging Repl: JWT_SECRET=staging-secret, API_KEY=test-key
- production Repl: JWT_SECRET=prod-secret, API_KEY=live-key

Account-level secrets (shared across all Repls):
- Settings > Secrets > Account secrets
- Useful for: monitoring tokens, shared infrastructure keys
```

### Step 4: GitHub Branch Strategy (Multi-Repl)
```markdown
Repository setup:
- main branch → connected to production Repl
- staging branch → connected to staging Repl
- feature branches → PR to staging first

Workflow:
1. Feature branch → PR to staging
2. Tests pass + review → merge to staging
3. Staging Repl auto-deploys → verify staging
4. Staging → PR to main
5. Merge → production Repl auto-deploys
```

```yaml
# .github/workflows/deploy.yml
name: Deploy Pipeline

on:
  push:
    branches: [staging, main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test

  verify-staging:
    if: github.ref == 'refs/heads/staging'
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Wait for Replit deploy
        run: sleep 60
      - name: Health check staging
        run: curl -sf ${{ secrets.STAGING_URL }}/health

  verify-production:
    if: github.ref == 'refs/heads/main'
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Wait for Replit deploy
        run: sleep 60
      - name: Health check production
        run: curl -sf ${{ secrets.PRODUCTION_URL }}/health
```

### Step 5: Database Migration Between Environments
```typescript
// scripts/promote-data.ts — Copy staging data to production (carefully!)
import { Pool } from 'pg';

const staging = new Pool({ connectionString: process.env.STAGING_DATABASE_URL });
const production = new Pool({ connectionString: process.env.PRODUCTION_DATABASE_URL });

async function promoteConfig() {
  // Only promote configuration/reference data, never user data
  const { rows: configs } = await staging.query('SELECT * FROM feature_flags');

  for (const config of configs) {
    await production.query(
      `INSERT INTO feature_flags (key, value, updated_at)
       VALUES ($1, $2, NOW())
       ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()`,
      [config.key, config.value]
    );
  }

  console.log(`Promoted ${configs.length} feature flags to production`);
}
```

### Step 6: Environment Indicator in UI
```typescript
// Show environment badge in development/staging
app.use((req, res, next) => {
  if (!IS_PROD) {
    res.setHeader('X-Environment', ENV);
  }
  next();
});

app.get('/api/status', (req, res) => {
  res.json({
    environment: ENV,
    version: process.env.npm_package_version,
    repl: process.env.REPL_SLUG,
  });
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong database in prod | Manual DATABASE_URL override | Let Replit manage DB routing |
| Staging secrets in prod | Copied secrets incorrectly | Each Repl has independent Secrets |
| GitHub sync conflict | Both Repls on same branch | Use separate branches per Repl |
| Config validation fails | Missing env-specific secret | Add secret to correct Repl's Secrets tab |

## Resources
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Replit Secrets](https://docs.replit.com/replit-workspace/workspace-features/secrets)
- [Deploying from GitHub](https://docs.replit.com/hosting/deployments/deploying-a-github-repository)
- [PostgreSQL Dev/Prod Databases](https://docs.replit.com/cloud-services/storage-and-databases/postgresql-on-replit)

## Next Steps
For monitoring, see `replit-observability`. For deployment, see `replit-deploy-integration`.
