---
name: clay-multi-env-setup
description: |
  Configure Clay integrations across development, staging, and production environments.
  Use when setting up per-environment Clay tables, managing webhook URLs per environment,
  or implementing environment-specific enrichment configurations.
  Trigger with phrases like "clay environments", "clay staging", "clay dev prod",
  "clay environment setup", "clay config by env".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, deployment]

---
# Clay Multi-Environment Setup

## Overview

Configure Clay integrations across dev/staging/prod with isolated tables, separate webhook URLs, and environment-specific enrichment settings. Clay is a single workspace per account, so multi-environment isolation requires separate tables, careful naming, and environment-aware application code.

## Prerequisites

- Clay account (one workspace can hold multiple tables)
- Environment variable management per deployment target
- Understanding of Clay table and webhook concepts

## Instructions

### Step 1: Create Per-Environment Tables

In Clay, create separate tables for each environment:

| Table Name | Environment | Webhook URL | Auto-Enrich | Credit Cap |
|------------|-------------|-------------|-------------|------------|
| `[DEV] Outbound Leads` | Development | Dev webhook | ON (small batches) | 100 rows |
| `[STG] Outbound Leads` | Staging | Staging webhook | ON | 500 rows |
| `Outbound Leads` | Production | Prod webhook | ON | 10,000 rows |

Each table gets its own webhook URL. Copy each URL to the appropriate environment's secrets.

### Step 2: Environment Configuration

```typescript
// src/config/clay.ts — environment-aware Clay configuration
interface ClayEnvConfig {
  webhookUrl: string;
  apiKey?: string;                // Enterprise API (if applicable)
  maxRowsPerBatch: number;
  delayBetweenRowsMs: number;
  enableCRMSync: boolean;
  tablePrefix: string;
}

function getClayConfig(): ClayEnvConfig {
  const env = process.env.NODE_ENV || 'development';

  const configs: Record<string, ClayEnvConfig> = {
    development: {
      webhookUrl: process.env.CLAY_WEBHOOK_URL_DEV!,
      maxRowsPerBatch: 10,          // Small batches to conserve credits
      delayBetweenRowsMs: 500,      // Slow, safe
      enableCRMSync: false,         // Never push dev data to real CRM
      tablePrefix: '[DEV]',
    },
    staging: {
      webhookUrl: process.env.CLAY_WEBHOOK_URL_STG!,
      maxRowsPerBatch: 100,
      delayBetweenRowsMs: 250,
      enableCRMSync: false,         // Use sandbox CRM if needed
      tablePrefix: '[STG]',
    },
    production: {
      webhookUrl: process.env.CLAY_WEBHOOK_URL!,
      apiKey: process.env.CLAY_API_KEY,
      maxRowsPerBatch: 1000,
      delayBetweenRowsMs: 100,
      enableCRMSync: true,
      tablePrefix: '',
    },
  };

  const config = configs[env];
  if (!config) throw new Error(`Unknown environment: ${env}`);
  if (!config.webhookUrl) throw new Error(`CLAY_WEBHOOK_URL not set for ${env}`);

  return config;
}
```

### Step 3: Environment Variable Management

```bash
# .env.development
CLAY_WEBHOOK_URL_DEV=https://app.clay.com/api/v1/webhooks/dev-webhook-id
NODE_ENV=development

# .env.staging
CLAY_WEBHOOK_URL_STG=https://app.clay.com/api/v1/webhooks/stg-webhook-id
NODE_ENV=staging

# .env.production (never in git — use secrets manager)
CLAY_WEBHOOK_URL=https://app.clay.com/api/v1/webhooks/prod-webhook-id
CLAY_API_KEY=clay_ent_production_key
NODE_ENV=production
```

```bash
# GitHub Actions — per-environment secrets
gh secret set CLAY_WEBHOOK_URL_DEV --body "https://app.clay.com/api/v1/webhooks/dev-id"
gh secret set CLAY_WEBHOOK_URL_STG --body "https://app.clay.com/api/v1/webhooks/stg-id"
gh secret set CLAY_WEBHOOK_URL --body "https://app.clay.com/api/v1/webhooks/prod-id"
gh secret set CLAY_API_KEY --body "clay_ent_production_key"
```

### Step 4: Startup Validation

```typescript
// src/config/validate.ts — fail fast if config is wrong
import { z } from 'zod';

const ClayConfigSchema = z.object({
  webhookUrl: z.string().url().startsWith('https://'),
  apiKey: z.string().startsWith('clay_ent_').optional(),
  maxRowsPerBatch: z.number().positive().max(10_000),
  delayBetweenRowsMs: z.number().min(0),
  enableCRMSync: z.boolean(),
  tablePrefix: z.string(),
});

export function validateClayConfig(config: unknown) {
  const result = ClayConfigSchema.safeParse(config);
  if (!result.success) {
    console.error('Clay configuration invalid:', result.error.format());
    process.exit(1);
  }
  console.log(`Clay config validated for ${process.env.NODE_ENV}`);
  return result.data;
}
```

### Step 5: Environment-Aware Safety Guards

```typescript
// src/clay/guards.ts — prevent production data in dev and vice versa
function safetyCheck(env: string, rowCount: number): void {
  if (env === 'development' && rowCount > 50) {
    throw new Error(`Dev environment: refusing to process ${rowCount} rows (max 50). Use staging or production.`);
  }
  if (env === 'staging' && rowCount > 1000) {
    throw new Error(`Staging environment: refusing to process ${rowCount} rows (max 1000). Use production.`);
  }
}

function preventCrossEnvData(env: string, crmPushEnabled: boolean): void {
  if (env !== 'production' && crmPushEnabled) {
    throw new Error(`CRM sync is disabled in ${env}. Only production can push to CRM.`);
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong table receives data | Dev webhook URL in production | Validate webhook URL matches environment |
| Dev data in production CRM | CRM sync enabled in dev | Guard CRM sync to production only |
| Credit waste in dev/staging | Full enrichment on test data | Set low row caps on dev/staging tables |
| Missing webhook URL at startup | Environment variable not set | Add startup validation with Zod |

## Resources

- [Clay University -- Table Management Settings](https://university.clay.com/docs/table-management-settings)
- [Zod Documentation](https://zod.dev/)

## Next Steps

For monitoring and observability, see `clay-observability`.
