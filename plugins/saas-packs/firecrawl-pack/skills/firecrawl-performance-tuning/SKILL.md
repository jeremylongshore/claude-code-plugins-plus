---
name: firecrawl-performance-tuning
description: |
  Optimize FireCrawl API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for FireCrawl integrations.
  Trigger with phrases like "firecrawl performance", "optimize firecrawl",
  "firecrawl latency", "firecrawl caching", "firecrawl slow", "firecrawl batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# FireCrawl Performance Tuning

## Overview
Optimize FireCrawl API performance with caching, batching, and connection pooling.

## Prerequisites
- FireCrawl SDK installed
- Understanding of async patterns
- Redis or in-memory cache available (optional)
- Performance monitoring in place

## Latency Benchmarks

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Read | 50ms | 150ms | 300ms |
| Write | 100ms | 250ms | 500ms |
| List | 75ms | 200ms | 400ms |

## Caching Strategy

### Response Caching
```typescript
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, any>({
  max: 1000,  # 1000: 1 second in ms
  ttl: 60000, // 1 minute  # 60000: 1 minute in ms
  updateAgeOnGet: true,
});

async function cachedFireCrawlRequest<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl?: number
): Promise<T> {
  const cached = cache.get(key);
  if (cached) return cached as T;

  const result = await fetcher();
  cache.set(key, result, { ttl });
  return result;
}
```

### Redis Caching (Distributed)
```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function cachedWithRedis<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlSeconds = 60
): Promise<T> {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const result = await fetcher();
  await redis.setex(key, ttlSeconds, JSON.stringify(result));
  return result;
}
```

## Request Batching

```typescript
import DataLoader from 'dataloader';

const firecrawlLoader = new DataLoader<string, any>(
  async (ids) => {
    // Batch fetch from FireCrawl
    const results = await firecrawlClient.batchGet(ids);
    return ids.map(id => results.find(r => r.id === id) || null);
  },
  {
    maxBatchSize: 100,
    batchScheduleFn: callback => setTimeout(callback, 10),
  }
);

// Usage - automatically batched
const [item1, item2, item3] = await Promise.all([
  firecrawlLoader.load('id-1'),
  firecrawlLoader.load('id-2'),
  firecrawlLoader.load('id-3'),
]);
```

## Connection Optimization

```typescript
import { Agent } from 'https';

// Keep-alive connection pooling
const agent = new Agent({
  keepAlive: true,
  maxSockets: 10,
  maxFreeSockets: 5,
  timeout: 30000,  # 30000: 30 seconds in ms
});

const client = new FireCrawlClient({
  apiKey: process.env.FIRECRAWL_API_KEY!,
  httpAgent: agent,
});
```

## Pagination Optimization

```typescript
async function* paginatedFireCrawlList<T>(
  fetcher: (cursor?: string) => Promise<{ data: T[]; nextCursor?: string }>
): AsyncGenerator<T> {
  let cursor: string | undefined;

  do {
    const { data, nextCursor } = await fetcher(cursor);
    for (const item of data) {
      yield item;
    }
    cursor = nextCursor;
  } while (cursor);
}

// Usage
for await (const item of paginatedFireCrawlList(cursor =>
  firecrawlClient.list({ cursor, limit: 100 })
)) {
  await process(item);
}
```

## Performance Monitoring

```typescript
async function measuredFireCrawlCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    const duration = performance.now() - start;
    console.log({ operation, duration, status: 'success' });
    return result;
  } catch (error) {
    const duration = performance.now() - start;
    console.error({ operation, duration, status: 'error', error });
    throw error;
  }
}
```

## Instructions

### Step 1: Establish Baseline
Measure current latency for critical FireCrawl operations.

### Step 2: Implement Caching
Add response caching for frequently accessed data.

### Step 3: Enable Batching
Use DataLoader or similar for automatic request batching.

### Step 4: Optimize Connections
Configure connection pooling with keep-alive.

## Output
- Reduced API latency
- Caching layer implemented
- Request batching enabled
- Connection pooling configured

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cache miss storm | TTL expired | Use stale-while-revalidate |
| Batch timeout | Too many items | Reduce batch size |
| Connection exhausted | No pooling | Configure max sockets |
| Memory pressure | Cache too large | Set max cache entries |

## Examples

### Quick Performance Wrapper
```typescript
const withPerformance = <T>(name: string, fn: () => Promise<T>) =>
  measuredFireCrawlCall(name, () =>
    cachedFireCrawlRequest(`cache:${name}`, fn)
  );
```

## Resources
- [FireCrawl Performance Guide](https://docs.firecrawl.com/performance)
- [DataLoader Documentation](https://github.com/graphql/dataloader)
- [LRU Cache Documentation](https://github.com/isaacs/node-lru-cache)

## Next Steps
For cost optimization, see `firecrawl-cost-tuning`.