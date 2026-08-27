---
name: appfolio-performance-tuning
description: 'Optimize AppFolio API performance with caching and batch operations.

  Trigger: "appfolio performance".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio Performance Tuning

## Overview

AppFolio's property management API handles bulk tenant queries, property portfolio pagination, and work order batch processing. Large portfolios with thousands of units generate heavy read traffic on listing endpoints. Optimizing cache lifetimes for slow-changing property data, batching work order updates, and pooling HTTP connections reduces API call volume by 60-80% and cuts dashboard load times from seconds to sub-second.

## Prerequisites

- A measured baseline for latency, call volume, error rate, payload size, cache
  hit behavior, and data freshness for the specific permitted endpoint.
- Endpoint-specific rate/concurrency limits, a request budget, and a data policy
  that excludes tenant, payment, and raw response payloads from generic caches.
- Synthetic fixtures and a rollback feature flag for validating performance
  changes without altering production read/write semantics.

## Instructions

1. Start with the smallest safe read and capture a baseline before changing
   caching, concurrency, pagination, or connection settings.
2. Cache only minimized data under a bounded entry/byte policy and invalidate
   on known writes; show stale age to callers where decisions need freshness.
3. Respect the smallest endpoint limit, preserve cursors, and stop parallel
   batches before they turn a rate-limit signal into a retry storm.
4. Promote only when performance improves without changing result completeness,
   authorization, PII boundaries, or write/idempotency behavior; roll back on
   any correctness regression.

## Caching Strategy

```typescript
const cache = new Map<string, { data: unknown; expiry: number }>();
const MAX_CACHE_ENTRIES = 1_000;
const TTL = { properties: 300_000, tenants: 120_000, units: 300_000, workOrders: 60_000 };

async function cached(key: string, ttlKey: keyof typeof TTL, fn: () => Promise<any>) {
  const entry = cache.get(key);
  if (entry && entry.expiry > Date.now()) return entry.data;
  const data = await fn();
  if (!cache.has(key) && cache.size >= MAX_CACHE_ENTRIES) cache.delete(cache.keys().next().value!);
  cache.set(key, { data, expiry: Date.now() + TTL[ttlKey] });
  return data;
}
```

## Batch Operations

```typescript
async function batchWorkOrders(client: any, ids: string[], batchSize = 25) {
  const results = [];
  for (let i = 0; i < ids.length; i += batchSize) {
    const batch = ids.slice(i, i + batchSize);
    const res = await Promise.all(batch.map(id => client.http.get(`/work_orders/${id}`)));
    results.push(...res.map(r => r.data));
    if (i + batchSize < ids.length) await new Promise(r => setTimeout(r, 200));
  }
  return results;
}
```

## Connection Pooling

```typescript
import { Agent } from 'https';
const agent = new Agent({ keepAlive: true, maxSockets: 10, maxFreeSockets: 5, timeout: 30_000 });
// Pass to axios/fetch: { httpsAgent: agent }
```

## Rate Limit Management

```typescript
async function withRateLimit(fn: () => Promise<any>): Promise<any> {
  const res = await fn();
  const remaining = parseInt(res.headers['x-ratelimit-remaining'] || '100');
  if (remaining < 5) {
    const retryAfter = parseInt(res.headers['retry-after'] || '2') * 1000;
    await new Promise(r => setTimeout(r, retryAfter));
  }
  return res;
}
```

## Monitoring

```typescript
const metrics = { apiCalls: 0, cacheHits: 0, errors: 0, totalLatency: 0 };
function track(startMs: number, hit: boolean, error?: boolean) {
  metrics.apiCalls++; metrics.totalLatency += Date.now() - startMs;
  if (hit) metrics.cacheHits++; if (error) metrics.errors++;
}
// Log: avg latency, cache hit rate, error rate per minute
```

## Performance Checklist

- [ ] Cache property and unit listings with 5-min TTL
- [ ] Use incremental sync via last_modified timestamps
- [ ] Batch work order updates in groups of 25
- [ ] Enable HTTP keep-alive with connection pooling
- [ ] Parse rate limit headers and back off proactively
- [ ] Parallelize independent dashboard queries with Promise.all
- [ ] Monitor cache hit ratio (target > 70%)
- [ ] Set request timeouts to 30s to avoid hung connections

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 Too Many Requests | Exceeded API rate limit | Parse Retry-After header, exponential backoff |
| Stale tenant data | Cache TTL too long | Reduce tenant cache to 2 min, add cache-bust on writes |
| Timeout on portfolio list | Large dataset with no pagination | Add page_size=100 and cursor-based iteration |
| Connection reset | Socket exhaustion | Enable keep-alive agent with maxSockets cap |

## Output

- A baseline-to-candidate comparison of latency, call volume, cache hit rate,
  error rate, and result completeness
- A bounded/minimized cache and endpoint-specific concurrency policy
- A rollout or rollback decision with a freshness and correctness receipt

## Examples

For a property-dashboard regression, benchmark one synthetic portfolio page,
then enable a bounded property-summary cache behind a feature flag. Compare
p95 latency, request count, cache hits, and returned IDs before and after the
change. Confirm that an authorized write invalidates the affected entry and
that a full rate-limit response pauses new work. If the candidate yields stale,
partial, unauthorized, or differently ordered results, disable the flag and
reconcile before trying another optimization.

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps

See `appfolio-reference-architecture`.
