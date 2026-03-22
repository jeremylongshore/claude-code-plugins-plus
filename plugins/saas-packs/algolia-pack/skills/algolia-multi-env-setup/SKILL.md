---
name: algolia-multi-env-setup
description: |
  Configure Algolia across dev/staging/production: index prefixing, per-environment
  API keys, settings-as-code, and environment isolation guards.
  Trigger: "algolia environments", "algolia staging", "algolia dev prod",
  "algolia environment setup", "algolia config by env".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Multi-Environment Setup

## Overview

Algolia doesn't have built-in environment separation. You either use **separate Algolia applications** (strongest isolation) or **index prefixing** within one application (simpler). This skill covers both approaches.

## Environment Strategies

| Strategy | Isolation | Cost | Complexity |
|----------|-----------|------|------------|
| Index prefixing | Shared app, prefixed names | Lowest | Low |
| Separate API keys | Shared app, scoped keys | Low | Medium |
| Separate applications | Full isolation | Highest | High |

## Instructions

### Step 1: Index Prefixing (Recommended for Most Teams)

```typescript
// src/algolia/config.ts
import { algoliasearch, type Algoliasearch } from 'algoliasearch';

type Environment = 'development' | 'staging' | 'production';

interface AlgoliaConfig {
  appId: string;
  apiKey: string;
  searchKey: string;
  environment: Environment;
}

function getConfig(): AlgoliaConfig {
  const env = (process.env.NODE_ENV || 'development') as Environment;

  return {
    appId: process.env.ALGOLIA_APP_ID!,
    apiKey: process.env.ALGOLIA_ADMIN_KEY!,
    searchKey: process.env.ALGOLIA_SEARCH_KEY!,
    environment: env,
  };
}

// Prefix index names with environment
export function indexName(base: string): string {
  const { environment } = getConfig();
  if (environment === 'production') return base;  // No prefix in prod
  return `${environment}_${base}`;
  // development_products, staging_products, products
}

let _client: Algoliasearch | null = null;

export function getClient(): Algoliasearch {
  if (!_client) {
    const config = getConfig();
    _client = algoliasearch(config.appId, config.apiKey);
  }
  return _client;
}
```

### Step 2: Scoped API Keys Per Environment

```typescript
import { algoliasearch } from 'algoliasearch';

const adminClient = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

// Create environment-scoped keys that can ONLY access their own indices
async function createEnvironmentKeys() {
  // Staging key: can only access staging_* indices
  const { key: stagingKey } = await adminClient.addApiKey({
    apiKey: {
      acl: ['search', 'addObject', 'deleteObject', 'editSettings', 'browse'],
      description: 'Staging environment — full access to staging indices only',
      indexes: ['staging_*'],
      maxQueriesPerIPPerHour: 10000,
    },
  });
  console.log(`Staging key: ${stagingKey}`);

  // Dev key: can only access development_* indices
  const { key: devKey } = await adminClient.addApiKey({
    apiKey: {
      acl: ['search', 'addObject', 'deleteObject', 'editSettings', 'browse'],
      description: 'Development environment — full access to dev indices only',
      indexes: ['development_*'],
      maxQueriesPerIPPerHour: 5000,
    },
  });
  console.log(`Dev key: ${devKey}`);

  // Production search key: search only, restricted
  const { key: prodSearchKey } = await adminClient.addApiKey({
    apiKey: {
      acl: ['search'],
      description: 'Production search — read only',
      indexes: ['products', 'articles', 'faq'],
      maxQueriesPerIPPerHour: 50000,
      maxHitsPerQuery: 100,
    },
  });
  console.log(`Prod search key: ${prodSearchKey}`);
}
```

### Step 3: Environment Variables Per Platform

```bash
# .env.development
ALGOLIA_APP_ID=YourAppID
ALGOLIA_ADMIN_KEY=dev_scoped_key_here
ALGOLIA_SEARCH_KEY=dev_search_key_here
NODE_ENV=development

# .env.staging
ALGOLIA_APP_ID=YourAppID
ALGOLIA_ADMIN_KEY=staging_scoped_key_here
ALGOLIA_SEARCH_KEY=staging_search_key_here
NODE_ENV=staging

# Production: use secret manager, not env files
# GitHub Actions:
#   ALGOLIA_ADMIN_KEY: ${{ secrets.ALGOLIA_ADMIN_KEY_PROD }}
# GCP Secret Manager:
#   gcloud secrets versions access latest --secret=algolia-admin-key
# Vercel:
#   vercel env add ALGOLIA_ADMIN_KEY production
```

### Step 4: Settings-as-Code with Environment Overrides

```typescript
// config/algolia-settings.ts
import type { IndexSettings } from 'algoliasearch';

const baseSettings: IndexSettings = {
  searchableAttributes: ['name', 'brand', 'category', 'unordered(description)'],
  attributesForFaceting: ['searchable(brand)', 'category', 'filterOnly(price)'],
  customRanking: ['desc(review_count)', 'desc(rating)'],
};

const envOverrides: Partial<Record<string, Partial<IndexSettings>>> = {
  development: {
    // Faster iteration: no replicas in dev
    replicas: [],
  },
  staging: {
    // Mirror prod replicas for testing
    replicas: ['virtual(staging_products_price_asc)'],
  },
  production: {
    replicas: [
      'virtual(products_price_asc)',
      'virtual(products_price_desc)',
      'virtual(products_newest)',
    ],
  },
};

export function getSettings(env: string): IndexSettings {
  return { ...baseSettings, ...envOverrides[env] };
}
```

### Step 5: Environment Isolation Guard

```typescript
// Prevent accidental cross-environment operations
export function guardEnvironment(operation: string, targetIndex: string) {
  const env = process.env.NODE_ENV || 'development';

  if (env === 'production') {
    // In production, block access to dev/staging indices
    if (targetIndex.startsWith('development_') || targetIndex.startsWith('staging_')) {
      throw new Error(`Blocked: ${operation} on ${targetIndex} from production`);
    }
  } else {
    // In dev/staging, block access to production indices (no prefix = production)
    if (!targetIndex.startsWith(`${env}_`)) {
      throw new Error(`Blocked: ${operation} on ${targetIndex} from ${env}. Use prefixed index.`);
    }
  }
}

// Usage in service layer
async function deleteIndex(name: string) {
  guardEnvironment('deleteIndex', name);
  await getClient().deleteIndex({ indexName: name });
}
```

### Step 6: Seed Script Per Environment

```typescript
// scripts/seed-environment.ts
import { getClient, indexName } from '../src/algolia/config';
import { getSettings } from '../config/algolia-settings';

async function seedEnvironment() {
  const env = process.env.NODE_ENV || 'development';
  const client = getClient();
  const idx = indexName('products');

  console.log(`Seeding ${env} environment → index: ${idx}`);

  // Apply settings
  await client.setSettings({ indexName: idx, indexSettings: getSettings(env) });

  // Seed data (dev/staging only)
  if (env !== 'production') {
    const testData = await import('../fixtures/products.json');
    const { taskID } = await client.replaceAllObjects({
      indexName: idx,
      objects: testData.default,
    });
    await client.waitForTask({ indexName: idx, taskID });
    console.log(`Seeded ${testData.default.length} records`);
  }
}

seedEnvironment().catch(console.error);
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong index in production | Missing prefix logic | Use `indexName()` helper everywhere |
| Staging data leaking to prod | Shared API key | Use scoped keys restricted to index patterns |
| Settings drift between envs | Manual dashboard changes | Apply settings from code in CI |
| Dev index polluting record count | Old test indices | Scheduled cleanup job for `development_*` indices |

## Resources

- [API Key Index Restrictions](https://www.algolia.com/doc/guides/security/api-keys/in-depth/api-key-restrictions/)
- [Settings API](https://www.algolia.com/doc/api-reference/api-methods/set-settings/)
- [12-Factor App Config](https://12factor.net/config)

## Next Steps

For observability setup, see `algolia-observability`.
