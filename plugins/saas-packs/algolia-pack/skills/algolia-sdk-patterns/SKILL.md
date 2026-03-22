---
name: algolia-sdk-patterns
description: |
  Apply production-ready algoliasearch v5 patterns: singleton client, typed search,
  error handling, and batch operations.
  Use when implementing Algolia integrations, refactoring SDK usage,
  or establishing team coding standards.
  Trigger: "algolia SDK patterns", "algolia best practices", "algolia code patterns", "idiomatic algolia".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia SDK Patterns

## Overview

Production-ready patterns for `algoliasearch` v5. Key architectural change from v4: all methods live on the client directly — no more `client.initIndex()`. Index name is passed as a parameter to every call.

## Prerequisites

- `algoliasearch` v5+ installed
- Completed `algolia-install-auth` setup
- TypeScript project (patterns work in JS too, you just lose type safety)

## Instructions

### Pattern 1: Typed Singleton Client

```typescript
// src/algolia/client.ts
import { algoliasearch, type Algoliasearch } from 'algoliasearch';

let _client: Algoliasearch | null = null;

export function getClient(): Algoliasearch {
  if (!_client) {
    const appId = process.env.ALGOLIA_APP_ID;
    const apiKey = process.env.ALGOLIA_ADMIN_KEY;
    if (!appId || !apiKey) {
      throw new Error(
        'ALGOLIA_APP_ID and ALGOLIA_ADMIN_KEY must be set. '
        + 'Get them from dashboard.algolia.com > Settings > API Keys'
      );
    }
    _client = algoliasearch(appId, apiKey);
  }
  return _client;
}

// For testing: reset singleton
export function resetClient(): void {
  _client = null;
}
```

### Pattern 2: Typed Search Results

```typescript
// src/algolia/types.ts

// Define your record shape — extends Algolia's Hit type
interface Product {
  objectID: string;
  name: string;
  category: string;
  price: number;
  description: string;
  image_url: string;
}

// src/algolia/search.ts
import { getClient } from './client';

export async function searchProducts(
  query: string,
  options?: {
    filters?: string;
    facetFilters?: string[][];
    hitsPerPage?: number;
    page?: number;
  }
) {
  const client = getClient();

  const { hits, nbHits, nbPages, page } = await client.searchSingleIndex<Product>({
    indexName: 'products',
    searchParams: {
      query,
      filters: options?.filters,
      facetFilters: options?.facetFilters,
      hitsPerPage: options?.hitsPerPage ?? 20,
      page: options?.page ?? 0,
      attributesToRetrieve: ['name', 'category', 'price', 'image_url'],
      attributesToHighlight: ['name', 'description'],
    },
  });

  return { hits, totalHits: nbHits, totalPages: nbPages, currentPage: page };
}

// Usage: const { hits } = await searchProducts('laptop', { filters: 'price < 1000' });
```

### Pattern 3: Error Handling with Algolia Error Types

```typescript
// src/algolia/errors.ts
import { ApiError } from 'algoliasearch';

export async function safeAlgoliaCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<{ data: T | null; error: string | null }> {
  try {
    const data = await fn();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ApiError) {
      // ApiError has status and message from Algolia API
      const msg = `Algolia ${operation} failed [${err.status}]: ${err.message}`;
      console.error(msg);

      // Specific handling for common codes
      if (err.status === 429) {
        console.warn('Rate limited — reduce request frequency or contact Algolia');
      } else if (err.status === 404) {
        console.warn('Index or object not found — verify index name');
      }

      return { data: null, error: msg };
    }
    // Non-Algolia error (network, etc.)
    const msg = err instanceof Error ? err.message : 'Unknown error';
    console.error(`${operation} error: ${msg}`);
    return { data: null, error: msg };
  }
}

// Usage:
// const { data, error } = await safeAlgoliaCall('search', () =>
//   client.searchSingleIndex({ indexName: 'products', searchParams: { query: 'foo' } })
// );
```

### Pattern 4: Batch Operations

```typescript
// src/algolia/batch.ts
import { getClient } from './client';

// saveObjects handles batching internally — send up to 1000 objects per call
export async function bulkIndex(indexName: string, records: Record<string, any>[]) {
  const client = getClient();
  const BATCH_SIZE = 1000;

  for (let i = 0; i < records.length; i += BATCH_SIZE) {
    const batch = records.slice(i, i + BATCH_SIZE);
    const { taskID } = await client.saveObjects({
      indexName,
      objects: batch,
    });
    await client.waitForTask({ indexName, taskID });
    console.log(`Indexed ${Math.min(i + BATCH_SIZE, records.length)}/${records.length}`);
  }
}

// Partial update — only send changed fields
export async function updateFields(
  indexName: string,
  objectID: string,
  fields: Record<string, any>
) {
  const client = getClient();
  return client.partialUpdateObject({
    indexName,
    objectID,
    attributesToUpdate: fields,
  });
}
```

### Pattern 5: Multi-Tenant Client Factory

```typescript
// src/algolia/multi-tenant.ts
import { algoliasearch, type Algoliasearch } from 'algoliasearch';

const tenantClients = new Map<string, Algoliasearch>();

export function getClientForTenant(tenantId: string): Algoliasearch {
  if (!tenantClients.has(tenantId)) {
    // Each tenant might have their own Algolia app, or use index prefixes
    const appId = process.env[`ALGOLIA_APP_ID_${tenantId.toUpperCase()}`]
      || process.env.ALGOLIA_APP_ID!;
    const apiKey = process.env[`ALGOLIA_ADMIN_KEY_${tenantId.toUpperCase()}`]
      || process.env.ALGOLIA_ADMIN_KEY!;

    tenantClients.set(tenantId, algoliasearch(appId, apiKey));
  }
  return tenantClients.get(tenantId)!;
}

// Or use a single app with index prefixing
export function tenantIndex(tenantId: string, base: string): string {
  return `${tenantId}_${base}`; // "acme_products"
}
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeAlgoliaCall` wrapper | All API calls | Prevents uncaught exceptions, structured error info |
| `ApiError` check | Distinguishing API vs network errors | Targeted retry/recovery logic |
| `waitForTask` | After every write operation | Ensures reads see latest data |
| Batch chunking | Large datasets | Avoids record-too-big and timeout errors |

## Resources

- [algoliasearch v5 Methods](https://www.algolia.com/doc/libraries/javascript/v5/methods/search/)
- [v4 to v5 Migration Guide](https://www.algolia.com/doc/libraries/javascript/v5/upgrade/)
- [API Error Codes](https://www.algolia.com/doc/api-reference/api-methods/)

## Next Steps

Apply patterns in `algolia-core-workflow-a` for search implementation.
