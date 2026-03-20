---
name: apollo-sdk-patterns
description: |
  Apply production-ready Apollo.io SDK patterns.
  Use when implementing Apollo integrations, refactoring API usage,
  or establishing team coding standards.
  Trigger with phrases like "apollo sdk patterns", "apollo best practices",
  "apollo code patterns", "idiomatic apollo", "apollo client wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo SDK Patterns

## Overview
Production-ready patterns for Apollo.io API integration with type safety, error handling, and retry logic. Apollo has no official SDK — these patterns wrap the REST API (`https://api.apollo.io/v1`) with robust TypeScript abstractions.

## Prerequisites
- Completed `apollo-install-auth` setup
- Familiarity with async/await patterns
- Understanding of TypeScript generics

## Instructions

### Step 1: Create a Type-Safe Client Singleton
```typescript
// src/apollo/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';
import { z } from 'zod';

const ApolloConfigSchema = z.object({
  apiKey: z.string().min(1),
  baseURL: z.string().url().default('https://api.apollo.io/v1'),
  timeout: z.number().default(30_000),
});

type ApolloConfig = z.infer<typeof ApolloConfigSchema>;

let instance: AxiosInstance | null = null;

export function getApolloClient(config?: Partial<ApolloConfig>): AxiosInstance {
  if (instance) return instance;

  const parsed = ApolloConfigSchema.parse({
    apiKey: config?.apiKey ?? process.env.APOLLO_API_KEY,
    ...config,
  });

  instance = axios.create({
    baseURL: parsed.baseURL,
    timeout: parsed.timeout,
    headers: { 'Content-Type': 'application/json' },
    params: { api_key: parsed.apiKey },
  });

  return instance;
}
```

### Step 2: Add Custom Error Classes
```typescript
// src/apollo/errors.ts
export class ApolloApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public endpoint: string,
    public retryable: boolean,
  ) {
    super(message);
    this.name = 'ApolloApiError';
  }

  static fromAxiosError(err: AxiosError, endpoint: string): ApolloApiError {
    const status = err.response?.status ?? 0;
    const retryable = [429, 500, 502, 503].includes(status);
    const msg = (err.response?.data as any)?.message ?? err.message;
    return new ApolloApiError(msg, status, endpoint, retryable);
  }
}
```

### Step 3: Implement Retry with Exponential Backoff
```typescript
// src/apollo/retry.ts
import { ApolloApiError } from './errors';

interface RetryOptions {
  maxRetries?: number;   // default: 3
  baseDelay?: number;    // default: 1000ms
  maxDelay?: number;     // default: 30000ms
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  opts: RetryOptions = {},
): Promise<T> {
  const { maxRetries = 3, baseDelay = 1000, maxDelay = 30_000 } = opts;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      const isRetryable = err instanceof ApolloApiError && err.retryable;
      if (!isRetryable || attempt === maxRetries) throw err;

      const jitter = Math.random() * 500;
      const delay = Math.min(baseDelay * 2 ** attempt + jitter, maxDelay);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Build an Async Pagination Iterator
```typescript
// src/apollo/paginator.ts
import { getApolloClient } from './client';
import { withRetry } from './retry';

interface PaginatedResponse<T> {
  items: T[];
  pagination: { page: number; per_page: number; total_entries: number };
}

export async function* paginate<T>(
  endpoint: string,
  body: Record<string, unknown>,
  itemKey: string = 'people',
  perPage: number = 100,
): AsyncGenerator<T[], void, undefined> {
  const client = getApolloClient();
  let page = 1;
  let total = Infinity;

  while ((page - 1) * perPage < total) {
    const { data } = await withRetry(() =>
      client.post(endpoint, { ...body, page, per_page: perPage }),
    );

    const items: T[] = data[itemKey] ?? [];
    total = data.pagination?.total_entries ?? items.length;
    yield items;
    page++;
  }
}

// Usage:
// for await (const batch of paginate<Person>('/people/search', { q_organization_domains: ['stripe.com'] })) {
//   await processBatch(batch);
// }
```

### Step 5: Add Request Batching for Bulk Operations
```typescript
// src/apollo/batcher.ts
import { getApolloClient } from './client';
import { withRetry } from './retry';

interface BatchOptions {
  batchSize?: number;       // default: 10
  concurrency?: number;     // default: 2
  delayBetweenMs?: number;  // default: 200
}

export async function batchEnrich<T>(
  items: string[],
  endpoint: string,
  paramKey: string,
  opts: BatchOptions = {},
): Promise<T[]> {
  const { batchSize = 10, concurrency = 2, delayBetweenMs = 200 } = opts;
  const client = getApolloClient();
  const results: T[] = [];

  for (let i = 0; i < items.length; i += batchSize * concurrency) {
    const chunk = items.slice(i, i + batchSize * concurrency);
    const batches: Promise<T[]>[] = [];

    for (let j = 0; j < chunk.length; j += batchSize) {
      const batch = chunk.slice(j, j + batchSize);
      batches.push(
        withRetry(async () => {
          const promises = batch.map((item) =>
            client.post(endpoint, { [paramKey]: item }),
          );
          const responses = await Promise.allSettled(promises);
          return responses
            .filter((r) => r.status === 'fulfilled')
            .map((r) => (r as PromiseFulfilledResult<any>).value.data);
        }),
      );
    }

    const batchResults = await Promise.all(batches);
    results.push(...batchResults.flat());

    if (i + batchSize * concurrency < items.length) {
      await new Promise((r) => setTimeout(r, delayBetweenMs));
    }
  }

  return results;
}
```

## Output
- `src/apollo/client.ts` — Type-safe singleton client with Zod config validation
- `src/apollo/errors.ts` — Custom `ApolloApiError` class with retryable flag
- `src/apollo/retry.ts` — Exponential backoff with jitter helper
- `src/apollo/paginator.ts` — Async generator for paginated endpoints
- `src/apollo/batcher.ts` — Concurrent batch processor for bulk enrichment

## Error Handling
| Pattern | When to Use |
|---------|-------------|
| Singleton | Always — ensures single client instance |
| Retry | Network errors, 429/500 responses |
| Pagination | Large result sets (>100 records) |
| Batching | Multiple enrichment calls |
| Custom Errors | Distinguish error types in catch blocks |

## Examples

### Combine All Patterns
```typescript
import { getApolloClient } from './apollo/client';
import { paginate } from './apollo/paginator';
import { batchEnrich } from './apollo/batcher';

async function enrichLeadPipeline(domain: string) {
  // 1. Paginate through all contacts at target company
  const allPeople: any[] = [];
  for await (const batch of paginate('/people/search', {
    q_organization_domains: [domain],
    person_titles: ['VP', 'Director', 'Head'],
  })) {
    allPeople.push(...batch);
  }
  console.log(`Found ${allPeople.length} decision-makers at ${domain}`);

  // 2. Batch-enrich emails for contacts missing them
  const needsEmail = allPeople
    .filter((p) => !p.email)
    .map((p) => p.id);

  const enriched = await batchEnrich(
    needsEmail,
    '/people/match',
    'id',
    { batchSize: 5, concurrency: 2, delayBetweenMs: 500 },
  );
  console.log(`Enriched ${enriched.length} contacts with email data`);
}
```

## Resources
- [Apollo API Documentation](https://apolloio.github.io/apollo-api-docs/)
- [Zod Schema Validation](https://zod.dev/)
- [Axios Interceptors](https://axios-http.com/docs/interceptors)

## Next Steps
Proceed to `apollo-core-workflow-a` for lead search implementation.
