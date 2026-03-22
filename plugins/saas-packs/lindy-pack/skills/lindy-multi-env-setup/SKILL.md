---
name: lindy-multi-env-setup
description: |
  Configure Lindy AI across development, staging, and production environments.
  Use when setting up isolated workspaces, per-environment secrets,
  or environment-specific agent configurations.
  Trigger with phrases like "lindy environments", "lindy staging",
  "lindy dev prod", "lindy environment setup", "lindy workspace isolation".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, deployment]

---
# Lindy Multi-Environment Setup

## Overview
Isolate Lindy AI agents across development, staging, and production using separate
workspaces, dedicated API keys, and environment-specific webhook configurations.
Lindy agents live in workspaces — each environment should use its own workspace
to prevent cross-environment data leakage.

## Prerequisites
- Multiple Lindy workspaces (one per environment) or Enterprise plan
- Secret management solution (env vars, Vault, AWS/GCP secrets)
- CI/CD pipeline with environment-aware deployment
- Application with environment detection logic

## Environment Strategy

| Environment | Workspace | API Key Source | Agent Config |
|-------------|-----------|---------------|-------------|
| Development | `dev-workspace` | `.env.local` | Debug prompts, test integrations |
| Staging | `staging-workspace` | CI/CD secrets | Production-like, test data |
| Production | `prod-workspace` | Secret manager | Hardened prompts, live integrations |

## Instructions

### Step 1: Create Separate Workspaces
1. Log in at https://app.lindy.ai
2. Create workspace for each environment: `[company]-dev`, `[company]-staging`, `[company]-prod`
3. Generate separate API keys in each workspace
4. Store each key in the appropriate secret store

### Step 2: Environment Configuration
```typescript
// config/lindy.ts — Environment-aware Lindy configuration
interface LindyConfig {
  apiKey: string;
  webhookUrl: string;
  webhookSecret: string;
  workspace: string;
  model: string;
}

function getLindyConfig(): LindyConfig {
  const env = process.env.NODE_ENV || 'development';

  const configs: Record<string, LindyConfig> = {
    development: {
      apiKey: process.env.LINDY_API_KEY_DEV!,
      webhookUrl: process.env.LINDY_WEBHOOK_URL_DEV!,
      webhookSecret: process.env.LINDY_WEBHOOK_SECRET_DEV!,
      workspace: 'dev',
      model: 'gemini-flash', // Cheap model for dev
    },
    staging: {
      apiKey: process.env.LINDY_API_KEY_STAGING!,
      webhookUrl: process.env.LINDY_WEBHOOK_URL_STAGING!,
      webhookSecret: process.env.LINDY_WEBHOOK_SECRET_STAGING!,
      workspace: 'staging',
      model: 'claude-sonnet', // Match prod model
    },
    production: {
      apiKey: process.env.LINDY_API_KEY_PROD!,
      webhookUrl: process.env.LINDY_WEBHOOK_URL_PROD!,
      webhookSecret: process.env.LINDY_WEBHOOK_SECRET_PROD!,
      workspace: 'production',
      model: 'claude-sonnet',
    },
  };

  const config = configs[env];
  if (!config) throw new Error(`Unknown environment: ${env}`);
  return config;
}

export const lindyConfig = getLindyConfig();
```

### Step 3: Startup Validation
```typescript
// validate-env.ts — Fail fast if Lindy config is missing
import { z } from 'zod';

const LindyEnvSchema = z.object({
  LINDY_API_KEY: z.string().min(1, 'LINDY_API_KEY required'),
  LINDY_WEBHOOK_SECRET: z.string().min(1, 'LINDY_WEBHOOK_SECRET required'),
  LINDY_WEBHOOK_URL: z.string().url('LINDY_WEBHOOK_URL must be valid URL'),
});

export function validateLindyEnv() {
  const result = LindyEnvSchema.safeParse({
    LINDY_API_KEY: process.env.LINDY_API_KEY,
    LINDY_WEBHOOK_SECRET: process.env.LINDY_WEBHOOK_SECRET,
    LINDY_WEBHOOK_URL: process.env.LINDY_WEBHOOK_URL,
  });

  if (!result.success) {
    console.error('Lindy environment validation failed:');
    result.error.issues.forEach(i => console.error(`  - ${i.path}: ${i.message}`));
    process.exit(1);
  }

  console.log('Lindy environment validated successfully');
}
```

### Step 4: Secret Management
```bash
# Development — .env.local (gitignored)
LINDY_API_KEY=lnd_dev_xxxxxxxxxxxx
LINDY_WEBHOOK_URL=https://public.lindy.ai/api/v1/webhooks/dev-id
LINDY_WEBHOOK_SECRET=whsec_dev_xxxxxxxxxxxx

# Staging — CI/CD secrets (GitHub Actions)
gh secret set LINDY_API_KEY_STAGING --body "lnd_staging_xxxx"
gh secret set LINDY_WEBHOOK_SECRET_STAGING --body "whsec_staging_xxxx"

# Production — Cloud secret manager
# AWS
aws secretsmanager create-secret \
  --name prod/lindy/api-key \
  --secret-string "lnd_prod_xxxxxxxxxxxx"

# GCP
echo -n "lnd_prod_xxxxxxxxxxxx" | \
  gcloud secrets create lindy-api-key-prod --data-file=-
```

### Step 5: Agent Promotion (Dev to Staging to Prod)
```
1. Build and test agent in dev workspace
2. Share agent as Template
3. Import template into staging workspace
4. Re-authorize integrations with staging accounts
5. Update webhook URLs to staging endpoints
6. Test with staging data for 24-48 hours
7. Repeat for production workspace
8. Update webhook URLs to production endpoints
9. Verify all integrations authorized with production accounts
```

**Critical**: OAuth tokens, webhook URLs, and phone numbers do NOT transfer
between workspaces. Each must be reconfigured per environment.

### Step 6: CI/CD Integration
```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    environment: staging
    env:
      LINDY_API_KEY: ${{ secrets.LINDY_API_KEY_STAGING }}
      LINDY_WEBHOOK_SECRET: ${{ secrets.LINDY_WEBHOOK_SECRET_STAGING }}
    steps:
      - run: npm run deploy:staging
      - run: npm run test:lindy:smoke

  deploy-prod:
    if: github.ref == 'refs/heads/main'
    environment: production
    env:
      LINDY_API_KEY: ${{ secrets.LINDY_API_KEY_PROD }}
      LINDY_WEBHOOK_SECRET: ${{ secrets.LINDY_WEBHOOK_SECRET_PROD }}
    steps:
      - run: npm run deploy:prod
      - run: npm run test:lindy:smoke
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Dev agent hits prod data | Shared workspace | Use separate workspaces per environment |
| Staging integration fails | OAuth token expired | Re-authorize with staging service accounts |
| Webhook URL mismatch | Dev URL in prod config | Validate webhook URLs at startup |
| Secret not found in CI | Missing environment secret | Add via `gh secret set` per environment |

## Resources
- [Lindy Documentation](https://docs.lindy.ai)
- [Lindy Templates](https://docs.lindy.ai/fundamentals/lindy-101/templates)

## Next Steps
Proceed to `lindy-observability` for monitoring and alerting.
