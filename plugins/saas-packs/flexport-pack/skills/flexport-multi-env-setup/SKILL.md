---
name: flexport-multi-env-setup
description: |
  Configure Flexport API across dev, staging, and production environments
  with isolated API keys, separate webhook endpoints, and environment guards.
  Trigger: "flexport environments", "flexport staging", "flexport multi-env".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Multi-Environment Setup

## Overview

Configure isolated Flexport environments for development, staging, and production with separate API keys, webhook endpoints, and safety guards to prevent production data access from dev.

## Instructions

### Environment Configuration

```typescript
// src/config/flexport.ts
interface FlexportConfig {
  apiKey: string;
  baseUrl: string;
  webhookSecret: string;
  cacheTtlMs: number;
  logLevel: 'debug' | 'info' | 'warn';
}

const configs: Record<string, FlexportConfig> = {
  development: {
    apiKey: process.env.FLEXPORT_API_KEY_DEV!,
    baseUrl: 'https://api.flexport.com',  // Same base, different key scope
    webhookSecret: process.env.FLEXPORT_WEBHOOK_SECRET_DEV!,
    cacheTtlMs: 30_000,   // 30s in dev for fast iteration
    logLevel: 'debug',
  },
  staging: {
    apiKey: process.env.FLEXPORT_API_KEY_STAGING!,
    baseUrl: 'https://api.flexport.com',
    webhookSecret: process.env.FLEXPORT_WEBHOOK_SECRET_STAGING!,
    cacheTtlMs: 60_000,
    logLevel: 'info',
  },
  production: {
    apiKey: process.env.FLEXPORT_API_KEY!,
    baseUrl: 'https://api.flexport.com',
    webhookSecret: process.env.FLEXPORT_WEBHOOK_SECRET!,
    cacheTtlMs: 300_000,  // 5min in prod
    logLevel: 'warn',
  },
};

export function getFlexportConfig(): FlexportConfig {
  const env = process.env.NODE_ENV || 'development';
  const config = configs[env];
  if (!config) throw new Error(`No Flexport config for env: ${env}`);
  if (!config.apiKey) throw new Error(`Missing FLEXPORT_API_KEY for ${env}`);
  return config;
}
```

### Environment Variable Template

```bash
# .env.example
# Development (read-only scope, limited data access)
FLEXPORT_API_KEY_DEV=fp_dev_...
FLEXPORT_WEBHOOK_SECRET_DEV=whsec_dev_...

# Staging (read-write scope, test data)
FLEXPORT_API_KEY_STAGING=fp_stg_...
FLEXPORT_WEBHOOK_SECRET_STAGING=whsec_stg_...

# Production (full scope, real shipments)
FLEXPORT_API_KEY=fp_prod_...
FLEXPORT_WEBHOOK_SECRET=whsec_prod_...
```

### Production Safety Guard

```typescript
// Prevent accidental production API calls from dev/test
function assertNotProduction(operation: string) {
  if (process.env.NODE_ENV === 'production') return;
  const config = getFlexportConfig();
  if (config.apiKey.startsWith('fp_prod_')) {
    throw new Error(`SAFETY: ${operation} blocked — production key detected in ${process.env.NODE_ENV}`);
  }
}

// Usage in destructive operations
async function deleteProduct(id: string) {
  assertNotProduction('deleteProduct');
  await flexport(`/products/${id}`, { method: 'DELETE' });
}
```

## Environment Matrix

| Aspect | Dev | Staging | Production |
|--------|-----|---------|------------|
| API key scope | Read-only | Read-write | Full |
| Webhook endpoint | localhost:3000 | staging.app.com | app.com |
| Cache TTL | 30s | 60s | 5min |
| Rate limit budget | 10/min | 50/min | 100/min |
| Logging | Debug (all) | Info | Warn + errors |

## Resources

- [Flexport Developer Portal](https://developers.flexport.com/)

## Next Steps

For observability setup, see `flexport-observability`.
