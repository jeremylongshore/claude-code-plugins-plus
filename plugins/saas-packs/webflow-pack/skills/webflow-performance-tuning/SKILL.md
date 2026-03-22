---
name: webflow-performance-tuning
description: |
  Optimize Webflow API performance with response caching, bulk endpoint batching,
  CDN-cached live item reads, pagination optimization, and connection pooling.
  Use when experiencing slow API responses or optimizing request throughput.
  Trigger with phrases like "webflow performance", "optimize webflow",
  "webflow latency", "webflow caching", "webflow slow", "webflow batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Performance Tuning

## Overview

Optimize Webflow Data API v2 performance. Key insight: **CDN-cached requests
to live items have no rate limits** — use the Content Delivery API for read-heavy
workloads and reserve write API calls for mutations.

## Prerequisites

- `webflow-api` SDK installed
- Understanding of your read/write ratio
- Redis or in-memory cache (optional)

## Webflow Performance Characteristics

| Operation | Typical Latency | Rate Limited | Cacheable |
|-----------|----------------|--------------|-----------|
| Live items (CDN) | 5-50ms | No | Yes (CDN) |
| Staged items | 50-200ms | Yes | Application cache |
| Create/update item | 100-300ms | Yes | No |
| Bulk create (100) | 200-500ms | Yes (1 count) | No |
| Site publish | 500-2000ms | 1/min | No |
| List collections | 50-150ms | Yes | Application cache |

**Key optimization: CDN-cached live item reads do not count against rate limits.**

## Instructions

### Strategy 1: Use Content Delivery API for Reads

```typescript
// For published content that visitors see, use live item endpoints.
// These are served by Webflow's CDN and have no rate limits.

async function getPublishedContent(collectionId: string) {
  // CDN-cached — fast, no rate limit
  const { items } = await webflow.collections.items.listItemsLive(collectionId, {
    limit: 100,
  });
  return items;
}

// Single live item — also CDN-cached
async function getPublishedItem(collectionId: string, itemId: string) {
  return webflow.collections.items.getItemLive(collectionId, itemId);
}
```

### Strategy 2: Application-Level Response Caching

```typescript
import { LRUCache } from "lru-cache";

const cache = new LRUCache<string, any>({
  max: 500,              // Max entries
  ttl: 5 * 60 * 1000,   // 5-minute TTL
  updateAgeOnGet: true,  // Reset TTL on access
});

async function cachedFetch<T>(
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

// Usage — cache collection schema (changes rarely)
const collections = await cachedFetch(
  `collections:${siteId}`,
  () => webflow.collections.list(siteId).then(r => r.collections),
  30 * 60 * 1000 // 30-minute cache for schemas
);

// Cache live items (shorter TTL for dynamic content)
const items = await cachedFetch(
  `items:live:${collectionId}`,
  () => webflow.collections.items.listItemsLive(collectionId).then(r => r.items),
  60 * 1000 // 1-minute cache
);
```

### Strategy 3: Redis Distributed Cache

```typescript
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL!);

async function cachedWithRedis<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlSeconds = 300
): Promise<T> {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached) as T;

  const result = await fetcher();
  await redis.setex(key, ttlSeconds, JSON.stringify(result));
  return result;
}

// Invalidate cache on webhook events
async function invalidateOnWebhook(triggerType: string, payload: any) {
  if (triggerType === "collection_item_changed" || triggerType === "collection_item_created") {
    const collectionId = payload.collectionId;
    await redis.del(`items:live:${collectionId}`);
    await redis.del(`items:staged:${collectionId}`);
    console.log(`Cache invalidated for collection ${collectionId}`);
  }

  if (triggerType === "site_publish") {
    // Flush all item caches on publish
    const keys = await redis.keys("items:*");
    if (keys.length > 0) await redis.del(...keys);
    console.log(`Flushed ${keys.length} cache entries on site publish`);
  }
}
```

### Strategy 4: Bulk Endpoints for Writes

One bulk request = 1 rate limit count for up to 100 items:

```typescript
// BAD: 100 API calls for 100 items
for (const item of items) {
  await webflow.collections.items.createItem(collectionId, {
    fieldData: item,
  });
}
// Rate limit cost: 100

// GOOD: 1 API call for 100 items
await webflow.collections.items.createItemsBulk(collectionId, {
  items: items.slice(0, 100).map(item => ({ fieldData: item })),
});
// Rate limit cost: 1

// For >100 items, batch with delay:
async function batchCreate(
  collectionId: string,
  allItems: Array<Record<string, any>>
) {
  for (let i = 0; i < allItems.length; i += 100) {
    const batch = allItems.slice(i, i + 100);
    await webflow.collections.items.createItemsBulk(collectionId, {
      items: batch.map(item => ({ fieldData: item, isDraft: false })),
    });
    if (i + 100 < allItems.length) {
      await new Promise(r => setTimeout(r, 500)); // Breathing room
    }
  }
}
```

### Strategy 5: Parallel Requests with Concurrency Control

```typescript
import PQueue from "p-queue";

const queue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 10,
});

// Fetch items from multiple collections in parallel
async function fetchFromMultipleCollections(collectionIds: string[]) {
  const results = await Promise.all(
    collectionIds.map(id =>
      queue.add(() =>
        webflow.collections.items.listItemsLive(id, { limit: 100 })
      )
    )
  );
  return results;
}
```

### Strategy 6: Efficient Pagination

```typescript
// Fetch all items with optimal page size
async function fetchAll(collectionId: string) {
  const allItems = [];
  let offset = 0;
  const limit = 100; // Maximum allowed

  while (true) {
    const { items, pagination } = await webflow.collections.items.listItems(
      collectionId,
      { offset, limit }
    );

    allItems.push(...(items || []));

    if (allItems.length >= (pagination?.total || 0)) break;
    offset += limit;
  }

  return allItems;
}
```

### Strategy 7: Performance Monitoring

```typescript
async function timedCall<T>(label: string, fn: () => Promise<T>): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    const ms = (performance.now() - start).toFixed(1);
    console.log(`[perf] ${label}: ${ms}ms`);
    return result;
  } catch (error) {
    const ms = (performance.now() - start).toFixed(1);
    console.error(`[perf] ${label}: FAILED after ${ms}ms`);
    throw error;
  }
}

// Usage
const items = await timedCall("listItemsLive", () =>
  webflow.collections.items.listItemsLive(collectionId)
);
```

## Performance Optimization Summary

| Strategy | Impact | Effort |
|----------|--------|--------|
| Live item API (CDN) | 10x faster reads, no rate limits | Low |
| Bulk endpoints | 100x fewer API calls | Low |
| LRU cache | Eliminates repeat reads | Medium |
| Redis distributed cache | Multi-instance caching | Medium |
| Webhook cache invalidation | Fresh data without polling | Medium |
| Concurrency control | Max throughput without 429s | Low |

## Output

- CDN-cached reads for published content
- Application-level caching with TTL
- Bulk writes reducing API call count 100x
- Webhook-triggered cache invalidation
- Performance monitoring for all API calls

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Stale cache | TTL too long | Reduce TTL or use webhook invalidation |
| Cache miss storm | All entries expire simultaneously | Add jitter to TTL |
| Bulk request 400 | >100 items | Cap batches at 100 |
| Memory pressure | LRU cache too large | Set `max` limit on cache |

## Resources

- [Content Delivery API](https://developers.webflow.com/data/docs/working-with-the-cms/content-delivery)
- [Rate Limits](https://developers.webflow.com/data/reference/rate-limits)
- [Bulk CMS Endpoints](https://developers.webflow.com/data/changelog/10232024)

## Next Steps

For cost optimization, see `webflow-cost-tuning`.
