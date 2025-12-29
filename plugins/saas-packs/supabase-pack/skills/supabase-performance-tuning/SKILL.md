---
name: supabase-performance-tuning
description: |
  Supabase latency optimization, caching, and batching patterns.
  Use when Supabase API calls are slow or need optimization.
  Trigger with phrases like "supabase performance", "optimize supabase",
  "supabase latency", "supabase caching", "supabase slow".
allowed-tools: Read, Write, Edit, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Performance Tuning

## Overview
Optimize Supabase API performance with caching, batching, and connection pooling.

## Prerequisites
- supabase-install-auth completed
- Performance metrics baseline established
- Redis/cache infrastructure (for distributed caching)
- Profiling tools available (optional)

## Instructions

### Step 1: Establish Latency Benchmarks

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Select | 15ms | 50ms | 100ms |
| Insert | 25ms | 75ms | 150ms |
| Real-time Subscribe | 50ms | 150ms | 300ms |

## Caching Strategy

### Response Caching
```typescript
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, any>({
  max: 1000,
  ttl: 30000, // 1 minute
  updateAgeOnGet: true,
});

async function cachedSupabaseRequest<T>(
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

const supabaseLoader = new DataLoader<string, any>(
  async (ids) => {
    // Batch fetch from Supabase
    const results = await supabaseClient.batchGet(ids);
    return ids.map(id => results.find(r => r.id === id) || null);
  },
  {
    maxBatchSize: 100,
    batchScheduleFn: callback => setTimeout(callback, 10),
  }
);

// Usage - automatically batched
const [item1, item2, item3] = await Promise.all([
  supabaseLoader.load('id-1'),
  supabaseLoader.load('id-2'),
  supabaseLoader.load('id-3'),
]);
```

## Connection Optimization

```typescript
import { Agent } from 'https';

// Keep-alive connection pooling
const agent = new Agent({
  keepAlive: true,
  maxSockets: 15,
  maxFreeSockets: 5,
  timeout: 30000,
});

const client = new SupabaseClient({
  apiKey: process.env.SUPABASE_API_KEY!,
  httpAgent: agent,
});
```

## Pagination Optimization

```typescript
async function* paginatedSupabaseList<T>(
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
for await (const item of paginatedSupabaseList(cursor =>
  supabaseClient.list({ cursor, limit: 100 })
)) {
  await process(item);
}
```

### Step 2: Performance Monitoring

```typescript
async function measuredSupabaseCall<T>(
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

## Output
- Response times reduced by 40-60%
- Cache hit rates > 80% for read operations
- Batch operations reducing API calls by 10x
- Connection pool preventing socket exhaustion

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Cache miss thundering herd | Many requests for uncached key | Use cache stampede protection |
| Connection pool exhausted | Too many concurrent requests | Increase pool size or add backpressure |
| Batch too large | Exceeds API batch limit | Split into smaller batches |
| Memory pressure | Large cache size | Reduce TTL or max entries |

## Examples

### OpenTelemetry Integration
```typescript
import { trace } from '@opentelemetry/api';

const tracer = trace.getTracer('supabase-client');

async function tracedSupabaseCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(operation, async (span) => {
    try {
      const result = await fn();
      span.setStatus({ code: 1 }); // OK
      return result;
    } catch (error) {
      span.setStatus({ code: 2, message: error.message }); // ERROR
      throw error;
    } finally {
      span.end();
    }
  });
}
```

## Resources
- [Supabase Performance Guide](https://supabase.com/docs/performance)
- [Rate Limits Reference](https://supabase.com/docs/rate-limits)
- [Caching Best Practices](https://supabase.com/docs/caching)

## Next Steps
For cost optimization, see `supabase-cost-tuning`.