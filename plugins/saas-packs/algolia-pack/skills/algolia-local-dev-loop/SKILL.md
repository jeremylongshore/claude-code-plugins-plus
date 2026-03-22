---
name: algolia-local-dev-loop
description: |
  Configure Algolia local development with separate dev index, mocking, and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Algolia.
  Trigger: "algolia dev setup", "algolia local development", "algolia dev environment", "test algolia locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for Algolia. Use separate dev indices, mock the client in tests, and iterate without touching production data.

## Prerequisites

- Completed `algolia-install-auth` setup
- Node.js 18+ with npm/pnpm
- Vitest or Jest for testing

## Instructions

### Step 1: Environment-Based Index Names

```typescript
// src/algolia/config.ts
import { algoliasearch } from 'algoliasearch';

const ENV = process.env.NODE_ENV || 'development';

// Each environment gets its own index prefix
export function indexName(base: string): string {
  if (ENV === 'production') return base;
  return `${ENV}_${base}`; // e.g., "development_products"
}

export const client = algoliasearch(
  process.env.ALGOLIA_APP_ID!,
  process.env.ALGOLIA_ADMIN_KEY!
);
```

### Step 2: Seed Script for Dev Data

```typescript
// scripts/seed-algolia.ts
import { client, indexName } from '../src/algolia/config';

const SEED_DATA = [
  { objectID: 'prod-1', name: 'Widget A', category: 'tools', price: 29.99 },
  { objectID: 'prod-2', name: 'Widget B', category: 'tools', price: 49.99 },
  { objectID: 'prod-3', name: 'Gadget C', category: 'electronics', price: 199.99 },
];

async function seed() {
  const idx = indexName('products');

  // replaceAllObjects atomically swaps index content
  const { taskID } = await client.replaceAllObjects({
    indexName: idx,
    objects: SEED_DATA,
  });
  await client.waitForTask({ indexName: idx, taskID });

  // Configure settings for the dev index
  await client.setSettings({
    indexName: idx,
    indexSettings: {
      searchableAttributes: ['name', 'category'],
      attributesForFaceting: ['category', 'filterOnly(price)'],
      customRanking: ['asc(price)'],
    },
  });

  console.log(`Seeded ${SEED_DATA.length} records into ${idx}`);
}

seed().catch(console.error);
```

```json
{
  "scripts": {
    "seed:algolia": "npx tsx scripts/seed-algolia.ts",
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch"
  }
}
```

### Step 3: Mock Algolia in Unit Tests

```typescript
// tests/algolia.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the entire algoliasearch module
vi.mock('algoliasearch', () => ({
  algoliasearch: vi.fn(() => ({
    searchSingleIndex: vi.fn().mockResolvedValue({
      hits: [
        { objectID: '1', name: 'Widget A', _highlightResult: {} },
      ],
      nbHits: 1,
      page: 0,
      nbPages: 1,
    }),
    saveObjects: vi.fn().mockResolvedValue({ taskID: 123 }),
    waitForTask: vi.fn().mockResolvedValue({}),
  })),
}));

import { algoliasearch } from 'algoliasearch';

describe('Product Search', () => {
  const client = algoliasearch('test-app-id', 'test-api-key');

  it('returns matching products', async () => {
    const { hits } = await client.searchSingleIndex({
      indexName: 'development_products',
      searchParams: { query: 'widget' },
    });
    expect(hits).toHaveLength(1);
    expect(hits[0].name).toBe('Widget A');
  });
});
```

### Step 4: Integration Test with Real API

```typescript
// tests/integration/algolia.integration.test.ts
import { describe, it, expect } from 'vitest';
import { algoliasearch } from 'algoliasearch';

describe.skipIf(!process.env.ALGOLIA_APP_ID)('Algolia Integration', () => {
  const client = algoliasearch(
    process.env.ALGOLIA_APP_ID!,
    process.env.ALGOLIA_ADMIN_KEY!
  );
  const testIndex = `test_${Date.now()}_products`;

  it('indexes and searches records', async () => {
    // Index
    const { taskID } = await client.saveObjects({
      indexName: testIndex,
      objects: [{ objectID: '1', name: 'Test Product' }],
    });
    await client.waitForTask({ indexName: testIndex, taskID });

    // Search
    const { hits } = await client.searchSingleIndex({
      indexName: testIndex,
      searchParams: { query: 'test' },
    });
    expect(hits.length).toBeGreaterThan(0);

    // Cleanup
    await client.deleteIndex({ indexName: testIndex });
  });
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Index does not exist` | Dev index not seeded | Run `npm run seed:algolia` |
| Test pollution | Shared index between tests | Use unique timestamped index names |
| Stale search results | Indexing not waited | Always `await client.waitForTask()` after writes |
| Mock not applied | Wrong import order | Ensure `vi.mock()` is before imports |

## Examples

### Clean Dev Index on Start

```typescript
// scripts/reset-dev-algolia.ts
import { client, indexName } from '../src/algolia/config';

async function reset() {
  const idx = indexName('products');
  try {
    await client.deleteIndex({ indexName: idx });
    console.log(`Deleted ${idx}`);
  } catch (e) {
    // Index may not exist yet — that's fine
  }
}

reset().catch(console.error);
```

## Resources

- [Algolia JavaScript v5 Client](https://www.algolia.com/doc/libraries/javascript/v5/methods/search/)
- [Vitest Documentation](https://vitest.dev/)
- [tsx (TypeScript execute)](https://github.com/privatenumber/tsx)

## Next Steps

See `algolia-sdk-patterns` for production-ready code patterns.
