---
name: klaviyo-performance-tuning
description: |
  Optimize Klaviyo API performance with caching, batching, and pagination tuning.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Klaviyo integrations.
  Trigger with phrases like "klaviyo performance", "optimize klaviyo",
  "klaviyo latency", "klaviyo caching", "klaviyo slow", "klaviyo batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Performance Tuning

## Overview

Optimize Klaviyo API performance with response caching, request batching, cursor-based pagination, sparse fieldsets, and connection pooling.

## Prerequisites

- `klaviyo-api` SDK installed
- Understanding of Klaviyo's rate limits (75 req/s burst, 700 req/min)
- Redis or in-memory cache (optional)

## Klaviyo API Performance Characteristics

| Operation | Typical Latency | Max Page Size |
|-----------|----------------|---------------|
| Get Profile by ID | 50-150ms | N/A |
| Get Profiles (list) | 100-300ms | 20 (default), 100 (some endpoints) |
| Create Profile | 100-200ms | N/A |
| Create Event | 50-100ms | N/A |
| Get Segment Profiles | 200-500ms | 20 |
| Campaign Operations | 200-500ms | 20 |

## Instructions

### Step 1: Sparse Fieldsets (Reduce Payload Size)

Klaviyo supports JSON:API sparse fieldsets -- request only the fields you need.

```typescript
// BAD: Fetches all profile fields (20+ attributes)
const profiles = await profilesApi.getProfiles();

// GOOD: Only fetch email and firstName (much smaller payload)
const profiles = await profilesApi.getProfiles({
  fieldsProfile: ['email', 'first_name', 'created'],
});
// Note: fieldsProfile uses snake_case field names (API-level names)

// Fetch profiles with included list relationships
const profilesWithLists = await profilesApi.getProfiles({
  fieldsProfile: ['email', 'first_name'],
  include: ['lists'],
  fieldsLists: ['name'],
});
```

### Step 2: Response Caching

```typescript
// src/klaviyo/cache.ts
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, any>({
  max: 5000,             // Max cached items
  ttl: 60 * 1000,        // 1 minute default TTL
  updateAgeOnGet: true,   // Reset TTL on access
});

export async function cachedKlaviyoCall<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlMs?: number
): Promise<T> {
  const cached = cache.get(key);
  if (cached !== undefined) return cached as T;

  const result = await fetcher();
  cache.set(key, result, { ttl: ttlMs });
  return result;
}

// Cache profile lookups by email
export async function getCachedProfile(email: string) {
  return cachedKlaviyoCall(
    `profile:${email}`,
    () => profilesApi.getProfiles({ filter: `equals(email,"${email}")` }),
    5 * 60 * 1000  // 5 minute TTL for profiles
  );
}

// Cache segment data (changes less frequently)
export async function getCachedSegments() {
  return cachedKlaviyoCall(
    'segments:all',
    () => segmentsApi.getSegments(),
    15 * 60 * 1000  // 15 minute TTL for segments
  );
}
```

### Step 3: Efficient Pagination

```typescript
// src/klaviyo/pagination.ts

/**
 * Auto-paginate with configurable page size and concurrency.
 * Klaviyo cursor pagination: response.body.links.next contains the cursor URL.
 */
export async function fetchAllPages<T>(
  fetcher: (pageCursor?: string) => Promise<{
    body: { data: T[]; links?: { next?: string } };
  }>,
  options = { maxPages: 100 }
): Promise<T[]> {
  const results: T[] = [];
  let cursor: string | undefined;
  let pageCount = 0;

  do {
    const response = await fetcher(cursor);
    results.push(...response.body.data);
    pageCount++;

    const nextLink = response.body.links?.next;
    if (nextLink && pageCount < options.maxPages) {
      const url = new URL(nextLink);
      cursor = url.searchParams.get('page[cursor]') || undefined;
    } else {
      cursor = undefined;
    }
  } while (cursor);

  return results;
}

// Usage: fetch all profiles in a list
const allProfiles = await fetchAllPages(
  (cursor) => listsApi.getListProfiles({ id: listId, pageCursor: cursor })
);
console.log(`Total profiles: ${allProfiles.length}`);
```

### Step 4: Request Batching with DataLoader

```typescript
import DataLoader from 'dataloader';
import { ProfilesApi } from 'klaviyo-api';

// Batch profile lookups: multiple getProfile(id) calls within
// a single tick are combined into one getProfiles() call
const profileLoader = new DataLoader<string, any>(
  async (profileIds) => {
    // Klaviyo doesn't have a batch-get-by-IDs endpoint,
    // so we fetch individually but with concurrency control
    const results = await Promise.allSettled(
      profileIds.map(id => profilesApi.getProfile({ id }))
    );
    return results.map(r =>
      r.status === 'fulfilled' ? r.value.body.data : null
    );
  },
  {
    maxBatchSize: 10,  // Stay well under rate limits
    batchScheduleFn: cb => setTimeout(cb, 50),  // 50ms batch window
    cache: true,  // In-memory cache within the DataLoader
  }
);

// These three calls are batched into concurrent requests
const [p1, p2, p3] = await Promise.all([
  profileLoader.load('PROFILE_ID_1'),
  profileLoader.load('PROFILE_ID_2'),
  profileLoader.load('PROFILE_ID_3'),
]);
```

### Step 5: Parallel API Calls with Concurrency Control

```typescript
import PQueue from 'p-queue';

// Process large operations with controlled concurrency
const queue = new PQueue({
  concurrency: 10,    // Max 10 parallel requests
  interval: 1000,     // Per second
  intervalCap: 50,    // 50 requests/second (safe margin under 75 burst)
});

// Example: update 10,000 profiles efficiently
async function bulkUpdateProfiles(updates: Array<{ email: string; data: any }>) {
  let completed = 0;

  const promises = updates.map(update =>
    queue.add(async () => {
      await profilesApi.createOrUpdateProfile({
        data: {
          type: 'profile' as any,
          attributes: { email: update.email, ...update.data },
        },
      });
      completed++;
      if (completed % 500 === 0) {
        console.log(`Progress: ${completed}/${updates.length}`);
      }
    })
  );

  await Promise.allSettled(promises);
  console.log(`Done: ${completed}/${updates.length}`);
}
```

### Step 6: Performance Monitoring

```typescript
// src/klaviyo/perf-monitor.ts

interface PerfMetrics {
  operation: string;
  durationMs: number;
  success: boolean;
  cached: boolean;
}

const perfLog: PerfMetrics[] = [];

export async function measuredCall<T>(
  operation: string,
  fn: () => Promise<T>,
  cached = false
): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    perfLog.push({ operation, durationMs: performance.now() - start, success: true, cached });
    return result;
  } catch (error) {
    perfLog.push({ operation, durationMs: performance.now() - start, success: false, cached });
    throw error;
  }
}

export function getPerfSummary(): Record<string, { avg: number; p95: number; count: number }> {
  const byOp: Record<string, number[]> = {};
  for (const m of perfLog) {
    (byOp[m.operation] ??= []).push(m.durationMs);
  }
  const summary: Record<string, any> = {};
  for (const [op, durations] of Object.entries(byOp)) {
    durations.sort((a, b) => a - b);
    summary[op] = {
      avg: Math.round(durations.reduce((a, b) => a + b, 0) / durations.length),
      p95: Math.round(durations[Math.floor(durations.length * 0.95)]),
      count: durations.length,
    };
  }
  return summary;
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cache stampede | Many requests on cache miss | Use stale-while-revalidate pattern |
| Pagination timeout | Very large datasets | Set `maxPages` limit, process in chunks |
| Rate limit on bulk ops | Too much concurrency | Reduce `PQueue` concurrency/intervalCap |
| Slow filter queries | Complex filter expressions | Simplify filters, use segment IDs instead |

## Resources

- [Klaviyo API Filtering](https://developers.klaviyo.com/en/reference/api_overview#filtering)
- [JSON:API Sparse Fieldsets](https://jsonapi.org/format/#fetching-sparse-fieldsets)
- [DataLoader](https://github.com/graphql/dataloader)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For cost optimization, see `klaviyo-cost-tuning`.
