---
name: maintainx-cost-tuning
description: |
  Optimize MaintainX API usage for cost efficiency.
  Use when managing API costs, optimizing request volume,
  or implementing cost-effective integration patterns with MaintainX.
  Trigger with phrases like "maintainx cost", "maintainx billing",
  "reduce maintainx usage", "maintainx api costs", "maintainx optimization".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Cost Tuning

## Overview
Reduce MaintainX API request volume and optimize costs through caching, webhook-driven sync, request batching, and smart polling strategies.

## Prerequisites
- MaintainX integration deployed and working
- Redis or in-memory cache available
- Baseline API usage metrics

## Instructions

### Step 1: Request Volume Tracking

```typescript
// src/cost/usage-tracker.ts

class ApiUsageTracker {
  private counts: Map<string, number> = new Map();
  private startTime = Date.now();

  record(endpoint: string) {
    const key = endpoint.split('?')[0]; // Strip query params
    this.counts.set(key, (this.counts.get(key) || 0) + 1);
  }

  report() {
    const elapsed = (Date.now() - this.startTime) / 1000 / 60; // minutes
    console.log(`\n=== API Usage Report (${elapsed.toFixed(1)} min) ===`);
    const sorted = [...this.counts.entries()].sort((a, b) => b[1] - a[1]);
    for (const [endpoint, count] of sorted) {
      const rate = (count / elapsed).toFixed(1);
      console.log(`  ${endpoint}: ${count} calls (${rate}/min)`);
    }
    console.log(`  TOTAL: ${[...this.counts.values()].reduce((a, b) => a + b, 0)} calls`);
  }
}

export const tracker = new ApiUsageTracker();
// Report every 10 minutes
setInterval(() => tracker.report(), 600_000);
```

### Step 2: Response Caching

```typescript
// src/cost/cached-client.ts

interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

class CachedMaintainXClient {
  private cache = new Map<string, CacheEntry<any>>();
  private client: MaintainXClient;

  // TTL per resource type (in seconds)
  private ttl: Record<string, number> = {
    '/users': 300,       // 5 min - users rarely change
    '/locations': 300,   // 5 min - locations are static
    '/assets': 120,      // 2 min - assets change infrequently
    '/workorders': 30,   // 30 sec - work orders change often
    '/teams': 600,       // 10 min - teams are very static
  };

  constructor(client: MaintainXClient) {
    this.client = client;
  }

  async get<T>(endpoint: string, params?: any): Promise<T> {
    const cacheKey = `${endpoint}:${JSON.stringify(params || {})}`;
    const cached = this.cache.get(cacheKey);

    if (cached && cached.expiresAt > Date.now()) {
      console.log(`[CACHE HIT] ${endpoint}`);
      return cached.data;
    }

    const basePath = '/' + endpoint.split('/').filter(Boolean)[0];
    const ttlSec = this.ttl[basePath] || 60;

    const data = await this.client.request('GET', endpoint, undefined, params);
    this.cache.set(cacheKey, {
      data,
      expiresAt: Date.now() + ttlSec * 1000,
    });

    tracker.record(endpoint);
    return data as T;
  }

  invalidate(pattern: string) {
    for (const key of this.cache.keys()) {
      if (key.startsWith(pattern)) {
        this.cache.delete(key);
      }
    }
  }
}
```

### Step 3: Webhook-Driven Sync (Replace Polling)

Polling every 30 seconds costs thousands of requests/day per endpoint. Webhooks reduce this to near zero.

```typescript
// Before: Polling (expensive)
// Calculation: 1 request every 30 sec = 2 req/min * 60 min * 24 hr = ~2880 req/day
setInterval(async () => {
  const { workOrders } = await client.getWorkOrders({ status: 'OPEN' });
  await syncToLocalDb(workOrders);
}, 30_000);

// After: Webhook-driven (near zero cost)
app.post('/webhooks/maintainx', async (req, res) => {
  const { event, data } = req.body;
  if (event === 'workorder.updated' || event === 'workorder.created') {
    await upsertWorkOrder(data);  // Only sync what changed
  }
  res.status(200).json({ ok: true });
});
```

**Cost savings**: From thousands of daily polling requests to ~50 req/day (webhook-driven deltas only).

### Step 4: Smart Polling with Conditional Requests

When webhooks are not available, reduce unnecessary fetches:

```typescript
// Only fetch if data has changed since last check
async function smartPoll(client: MaintainXClient, state: { lastModified?: string }) {
  const response = await client.getWorkOrders({
    updatedAtGte: state.lastModified || new Date(0).toISOString(),
    limit: 100,
  });

  if (response.workOrders.length === 0) {
    console.log('No changes since last poll');
    return [];
  }

  state.lastModified = new Date().toISOString();
  return response.workOrders;
}
```

### Step 5: Request Deduplication

```typescript
// Deduplicate concurrent identical requests
const inFlight = new Map<string, Promise<any>>();

async function deduplicatedGet(client: MaintainXClient, endpoint: string): Promise<any> {
  if (inFlight.has(endpoint)) {
    return inFlight.get(endpoint)!;
  }

  const promise = client.request('GET', endpoint);
  inFlight.set(endpoint, promise);

  try {
    return await promise;
  } finally {
    inFlight.delete(endpoint);
  }
}
```

## Output
- API usage tracking with per-endpoint request counts
- Response caching with resource-specific TTLs
- Webhook-driven sync replacing expensive polling loops
- Smart polling with `updatedAtGte` filter for change detection
- Request deduplication preventing concurrent identical calls

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Stale cache data | TTL too long for volatile resources | Reduce TTL for `/workorders` to 15-30s |
| Webhook delivery failures | Endpoint down or unreachable | Fall back to polling with longer interval |
| Cache memory growth | No eviction policy | Set max cache size, use LRU eviction |
| Duplicate webhook events | MaintainX retries | Deduplicate by event ID (see webhooks skill) |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [MaintainX Pricing](https://www.getmaintainx.com/pricing)
- [node-cache](https://github.com/node-cache/node-cache) -- In-memory caching for Node.js

## Next Steps
For architecture patterns, see `maintainx-reference-architecture`.

## Examples

**Redis-based cache for production**:

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function cachedGet(key: string, ttlSec: number, fetcher: () => Promise<any>) {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const data = await fetcher();
  await redis.setex(key, ttlSec, JSON.stringify(data));
  return data;
}

// Usage
const workOrders = await cachedGet(
  'maintainx:workorders:open',
  30,
  () => client.getWorkOrders({ status: 'OPEN' }),
);
```
