---
name: finta-performance-tuning
description: 'Optimize Finta fundraise workflow efficiency.

  Trigger with phrases like "finta performance", "finta efficiency", "optimize finta".

  '
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- fundraising-crm
- investor-management
- finta
compatibility: Designed for Claude Code
---
# Finta Performance Tuning

## Overview

Finta's fundraising API handles investor list pagination, round data aggregation, and CRM sync batching. Founders querying large investor databases (1,000+ contacts) hit pagination bottlenecks, while round aggregation across multiple funding stages compounds latency. Optimizing paginated fetches with cursor-based iteration, caching investor profiles, and batching CRM sync writes reduces pipeline load times by 50-70% and keeps fundraising dashboards responsive during active rounds.

## Caching Strategy
```typescript
const cache = new Map<string, { data: any; expiry: number }>();
const TTL = { investors: 600_000, rounds: 300_000, pipeline: 120_000 };

async function cached(key: string, ttlKey: keyof typeof TTL, fn: () => Promise<any>) {
  const entry = cache.get(key);
  if (entry && entry.expiry > Date.now()) return entry.data;
  const data = await fn();
  cache.set(key, { data, expiry: Date.now() + TTL[ttlKey] });
  return data;
}
// Investor profiles change rarely (10 min). Pipeline stages are volatile (2 min).
```

## Batch Operations
```typescript
async function syncInvestorsBatch(client: any, cursor?: string, pageSize = 100) {
  const allInvestors = [];
  let nextCursor = cursor;
  do {
    const page = await client.listInvestors({ cursor: nextCursor, limit: pageSize });
    allInvestors.push(...page.data);
    nextCursor = page.next_cursor;
    if (nextCursor) await new Promise(r => setTimeout(r, 200));
  } while (nextCursor);
  return allInvestors;
}
```

## Connection Pooling
```typescript
import { Agent } from 'https';
const agent = new Agent({ keepAlive: true, maxSockets: 8, maxFreeSockets: 4, timeout: 30_000 });
// Finta API calls are lightweight — moderate socket count suffices
```

## Rate Limit Management
```typescript
async function withRateLimit(fn: () => Promise<any>): Promise<any> {
  const res = await fn();
  const remaining = parseInt(res.headers?.['x-ratelimit-remaining'] || '50');
  if (remaining < 3) {
    const resetMs = parseInt(res.headers?.['x-ratelimit-reset'] || '5') * 1000;
    await new Promise(r => setTimeout(r, resetMs));
  }
  return res;
}
```

## Monitoring
```typescript
const metrics = { apiCalls: 0, cacheHits: 0, syncErrors: 0, avgLatencyMs: 0 };
function track(startMs: number, cached: boolean, error?: boolean) {
  metrics.apiCalls++;
  metrics.avgLatencyMs = (metrics.avgLatencyMs * (metrics.apiCalls - 1) + (Date.now() - startMs)) / metrics.apiCalls;
  if (cached) metrics.cacheHits++; if (error) metrics.syncErrors++;
}
```

## Performance Checklist
- [ ] Use cursor-based pagination for investor lists (not offset)
- [ ] Cache investor profiles with 10-min TTL
- [ ] Batch CRM sync writes in groups of 50
- [ ] Aggregate round data client-side to avoid repeated queries
- [ ] Enable HTTP keep-alive for persistent connections
- [ ] Parse rate limit headers and pause before exhaustion
- [ ] Prefetch deal room analytics during idle periods
- [ ] Set pipeline cache TTL to 2 min for active-round freshness

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| Slow investor list load | Offset-based pagination on large dataset | Switch to cursor-based iteration with limit=100 |
| Stale round totals | Aggregation cache too long during active round | Reduce round TTL to 5 min, invalidate on write |
| CRM sync timeout | Too many individual writes | Batch CRM updates in groups of 50 |
| 429 Rate Limited | Burst of API calls during pipeline refresh | Parse rate limit headers, add progressive backoff |

## Resources
- [Finta Developer Docs](https://www.trustfinta.com/developers)
- [Finta Blog](https://www.trustfinta.com/blog)

## Next Steps
See `finta-reference-architecture`.
