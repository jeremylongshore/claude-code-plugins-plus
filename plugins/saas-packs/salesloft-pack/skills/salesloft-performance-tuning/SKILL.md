---
name: salesloft-performance-tuning
description: |
  Optimize SalesLoft API performance with caching, pagination strategies, and connection pooling.
  Use when experiencing slow API responses, reducing latency for bulk operations,
  or optimizing cadence sync throughput.
  Trigger: "salesloft performance", "optimize salesloft", "salesloft slow", "salesloft caching".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft Performance Tuning

## Overview

Optimize SalesLoft REST API v2 performance. Key bottlenecks: deep pagination (cost multiplier), no batch endpoints, and per-minute rate limits. Solutions: caching, incremental sync, and pagination-aware request planning.

## Latency Benchmarks

| Operation | Typical | With Caching |
|-----------|---------|-------------|
| GET /me.json | 80ms | N/A (auth) |
| GET /people.json (page 1) | 120ms | 1ms (cached) |
| POST /people.json | 200ms | N/A (write) |
| GET /activities/emails.json | 150ms | 1ms (cached) |
| Full sync (10k people) | ~20min | ~5min (incremental) |

## Instructions

### Step 1: Response Caching

```typescript
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, any>({ max: 5000, ttl: 60_000 });

async function cachedGet<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
  const key = `${endpoint}:${JSON.stringify(params || {})}`;
  const hit = cache.get(key);
  if (hit) return hit as T;

  const { data } = await api.get(endpoint, { params });
  cache.set(key, data);
  return data;
}

// Cache people lookups (frequent during cadence enrollment)
const person = await cachedGet('/people.json', { email_addresses: ['alex@co.com'] });
```

### Step 2: Incremental Sync with updated_at

```typescript
// Only fetch records changed since last sync
async function incrementalSync(lastSyncTime: string) {
  const updated: any[] = [];
  let page = 1;

  while (true) {
    const { data } = await api.get('/people.json', {
      params: {
        updated_at: { gt: lastSyncTime }, // ISO 8601
        per_page: 100,
        page,
        sort_by: 'updated_at',
        sort_direction: 'ASC',
      },
    });
    updated.push(...data.data);
    if (page >= data.metadata.paging.total_pages) break;
    page++;
  }

  return { updated, newSyncTime: new Date().toISOString() };
}
```

### Step 3: Avoid Deep Pagination Cost

```typescript
// Deep pages cost 3-30x. Instead of paginating all 25k records,
// use updated_at filter to get incremental changes
function shouldUseIncremental(totalCount: number): boolean {
  // If total records > 1000, incremental sync is more efficient
  // Full pagination of 250 pages = 910 cost points vs.
  // incremental of last 50 changes = 1 page = 1 point
  return totalCount > 1000;
}
```

### Step 4: Connection Pooling

```typescript
import { Agent } from 'https';

const agent = new Agent({
  keepAlive: true,
  maxSockets: 10,     // Max concurrent connections
  maxFreeSockets: 5,  // Keep idle connections alive
  timeout: 30_000,
});

const api = axios.create({
  baseURL: 'https://api.salesloft.com/v2',
  headers: { Authorization: `Bearer ${process.env.SALESLOFT_API_KEY}` },
  httpsAgent: agent,
});
```

### Step 5: Parallel Safe Reads

```typescript
// Parallelize independent reads (each costs 1 point)
const [people, cadences, activities] = await Promise.all([
  api.get('/people.json', { params: { per_page: 100 } }),
  api.get('/cadences.json', { params: { per_page: 50 } }),
  api.get('/activities/emails.json', { params: { per_page: 100 } }),
]);
// 3 points total, ~120ms parallel vs ~360ms sequential
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cache stampede | TTL expiry under load | Stale-while-revalidate pattern |
| Incremental misses | Clock skew | Use `updated_at` from last response, not local clock |
| Connection timeout | Pool exhausted | Increase `maxSockets` or reduce concurrency |
| Rate limit on bulk | Too many parallel requests | Use `p-queue` with `intervalCap: 10` |

## Resources

- [SalesLoft Rate Limits](https://developers.salesloft.com/docs/platform/api-basics/rate-limits/)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)

## Next Steps

For cost optimization, see `salesloft-cost-tuning`.
