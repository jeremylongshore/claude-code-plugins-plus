---
name: canva-performance-tuning
description: |
  Optimize Canva Connect API performance with caching, pagination, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Canva integrations.
  Trigger with phrases like "canva performance", "optimize canva",
  "canva latency", "canva caching", "canva slow", "canva pagination".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Performance Tuning

## Overview

Optimize Canva Connect API performance. The REST API at `api.canva.com/rest/v1/*` has per-user rate limits and async operations (exports, uploads, autofills) that require polling.

## Caching Strategy

### Design Metadata Cache

```typescript
import { LRUCache } from 'lru-cache';

// Design metadata changes infrequently — cache aggressively
const designCache = new LRUCache<string, any>({
  max: 500,
  ttl: 5 * 60 * 1000,  // 5 minutes
});

async function getDesignCached(designId: string, token: string) {
  const cached = designCache.get(designId);
  if (cached) return cached;

  const data = await canvaAPI(`/designs/${designId}`, token);
  designCache.set(designId, data);
  return data;
}

// IMPORTANT: Do NOT cache these — they expire quickly:
// - Thumbnail URLs: expire in 15 minutes
// - Edit/view URLs: expire in 30 days
// - Export download URLs: expire in 24 hours
```

### Redis Cache for Distributed Systems

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function cachedCanvaCall<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlSeconds = 300
): Promise<T> {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const result = await fetcher();
  await redis.setex(key, ttlSeconds, JSON.stringify(result));
  return result;
}

// Cache brand template list — rarely changes
const templates = await cachedCanvaCall(
  'canva:brand-templates:list',
  () => canvaAPI('/brand-templates', token),
  3600 // 1 hour
);
```

## Pagination Optimization

```typescript
// Canva uses continuation-based pagination
async function* paginateDesigns(
  token: string,
  opts: { ownership?: string; limit?: number } = {}
): AsyncGenerator<any> {
  let continuation: string | undefined;

  do {
    const params = new URLSearchParams({
      limit: String(opts.limit || 100),  // Max 100 per page
      ...(opts.ownership && { ownership: opts.ownership }),
      ...(continuation && { continuation }),
    });

    const data = await canvaAPI(`/designs?${params}`, token);

    for (const design of data.items) {
      yield design;
    }

    continuation = data.continuation; // undefined = last page
  } while (continuation);
}

// Usage — processes designs as they arrive
for await (const design of paginateDesigns(token, { ownership: 'owned' })) {
  console.log(`${design.title} (${design.id})`);
}
```

## Export Polling Optimization

```typescript
// Smart polling with progressive backoff
async function pollExport(exportId: string, token: string): Promise<string[]> {
  const delays = [500, 1000, 2000, 3000, 5000, 5000, 10000]; // Progressive backoff
  let attempt = 0;

  while (attempt < 20) { // Max ~60s total
    const { job } = await canvaAPI(`/exports/${exportId}`, token);

    if (job.status === 'success') return job.urls;
    if (job.status === 'failed') throw new Error(`Export failed: ${job.error?.message}`);

    const delay = delays[Math.min(attempt, delays.length - 1)];
    await new Promise(r => setTimeout(r, delay));
    attempt++;
  }

  throw new Error('Export polling timeout');
}

// Batch exports with concurrency control
import PQueue from 'p-queue';

const exportQueue = new PQueue({ concurrency: 3 });

async function batchExport(
  designIds: string[],
  format: object,
  token: string
): Promise<Map<string, string[]>> {
  const results = new Map<string, string[]>();

  await Promise.all(
    designIds.map(id =>
      exportQueue.add(async () => {
        const { job } = await canvaAPI('/exports', token, {
          method: 'POST',
          body: JSON.stringify({ design_id: id, format }),
        });
        const urls = await pollExport(job.id, token);
        results.set(id, urls);
      })
    )
  );

  return results;
}
```

## Connection Optimization

```typescript
import { Agent } from 'https';

// Keep-alive for connection reuse
const agent = new Agent({
  keepAlive: true,
  maxSockets: 10,
  maxFreeSockets: 5,
  timeout: 30000,
});

// Use with Node.js fetch or undici
const res = await fetch('https://api.canva.com/rest/v1/designs', {
  headers: { 'Authorization': `Bearer ${token}` },
  // @ts-expect-error — Node.js specific
  agent,
});
```

## Performance Monitoring

```typescript
async function measuredCanvaCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    const ms = (performance.now() - start).toFixed(0);
    console.log(`[canva] ${operation}: ${ms}ms OK`);
    return result;
  } catch (error) {
    const ms = (performance.now() - start).toFixed(0);
    console.error(`[canva] ${operation}: ${ms}ms FAIL`, error);
    throw error;
  }
}
```

## Performance Benchmarks

| Operation | Typical Latency | Rate Limit |
|-----------|----------------|------------|
| GET /users/me | 50-150ms | 10/min |
| POST /designs | 200-500ms | 20/min |
| GET /designs (list) | 100-300ms | 100/min |
| POST /exports | 100-300ms (job start) | 75/5min |
| Export completion | 2-15s (depending on size) | N/A |
| POST /asset-uploads | 300-2000ms | 30/min |
| POST /autofills | 500-3000ms (job start) | 60/min |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Stale cache | Long TTL | Reduce TTL or invalidate on write |
| Export timeout | Large/complex design | Increase poll timeout |
| Memory pressure | Cache too large | Set LRU max entries |
| Connection refused | Pool exhausted | Increase maxSockets |

## Resources

- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For cost optimization, see `canva-cost-tuning`.
