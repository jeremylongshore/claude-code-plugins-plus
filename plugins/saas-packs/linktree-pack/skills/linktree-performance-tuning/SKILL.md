---
name: linktree-performance-tuning
description: |
  Optimize Linktree API integration performance with caching, batching, and rate limit strategies.
  Use when Linktree API calls are slow, hitting rate limits, or profile pages serve stale link data.
  Trigger with "linktree performance tuning".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Performance Tuning

## Overview

Linktree profiles are high-traffic read endpoints — a single creator's link-in-bio page can receive millions of hits during viral moments. This skill covers caching strategies tuned to Linktree's data volatility, batch link operations, and resilient rate limit handling to prevent stale data and API cost overruns.

## Instructions

1. Implement Redis caching (or in-memory Map for development) with product-specific TTLs
2. Wrap all API calls with the rate limit handler before deploying to production
3. Enable connection pooling and configure batch sizes based on your traffic volume
4. Set up monitoring metrics and verify cache hit rates exceed 80%

## Prerequisites

- Linktree API key with read/write scopes
- Redis instance (or Node.js in-memory cache for development)
- Monitoring stack (Prometheus/Grafana or equivalent)
- Node.js 18+ with native fetch support

## Caching Strategy

```typescript
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL);

// Profile data changes infrequently — cache 10 minutes
// Link lists update more often — cache 2 minutes
const TTL = { profile: 600, links: 120, analytics: 300 } as const;

async function getCachedProfile(username: string): Promise<LinktreeProfile> {
  const key = `lt:profile:${username}`;
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const profile = await linktreeApi.getProfile(username);
  await redis.setex(key, TTL.profile, JSON.stringify(profile));
  return profile;
}

async function getCachedLinks(profileId: string): Promise<LinktreeLink[]> {
  const key = `lt:links:${profileId}`;
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const links = await linktreeApi.getLinks(profileId);
  await redis.setex(key, TTL.links, JSON.stringify(links));
  return links;
}
```

## Batch Operations

```typescript
// Fetch multiple profiles in parallel with concurrency limit
import pLimit from "p-limit";

const limit = pLimit(5); // Max 5 concurrent Linktree API calls

async function batchFetchProfiles(usernames: string[]): Promise<LinktreeProfile[]> {
  return Promise.all(
    usernames.map((u) => limit(() => getCachedProfile(u)))
  );
}

// Bulk link updates — group mutations into single request windows
async function batchUpdateLinks(
  profileId: string,
  updates: LinkUpdate[]
): Promise<void> {
  const chunks = chunkArray(updates, 10); // 10 links per request
  for (const chunk of chunks) {
    await Promise.all(chunk.map((u) => limit(() => linktreeApi.updateLink(profileId, u))));
  }
}
```

## Connection Pooling

```typescript
import { Agent } from "undici";

const linktreeAgent = new Agent({
  connect: { timeout: 5_000 },
  keepAliveTimeout: 30_000,
  keepAliveMaxTimeout: 60_000,
  pipelining: 1,
  connections: 10, // Persistent pool for linktr.ee API
});

async function linktreeFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`https://api.linktr.ee/v1${path}`, {
    ...init,
    // @ts-expect-error undici dispatcher
    dispatcher: linktreeAgent,
    headers: { Authorization: `Bearer ${process.env.LINKTREE_API_KEY}`, ...init?.headers },
  });
}
```

## Rate Limit Management

```typescript
async function withRateLimit<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err.status === 429) {
        const retryAfter = parseInt(err.headers?.["retry-after"] ?? "5", 10);
        const backoff = retryAfter * 1000 * Math.pow(2, attempt);
        console.warn(`Linktree rate limited. Retrying in ${backoff}ms (attempt ${attempt + 1})`);
        await new Promise((r) => setTimeout(r, backoff));
        continue;
      }
      throw err;
    }
  }
  throw new Error("Linktree API: max retries exceeded");
}
```

## Monitoring & Metrics

```typescript
import { Counter, Histogram } from "prom-client";

const ltApiLatency = new Histogram({
  name: "linktree_api_duration_seconds",
  help: "Linktree API call latency",
  labelNames: ["endpoint", "status"],
  buckets: [0.1, 0.25, 0.5, 1, 2, 5],
});

const ltCacheHits = new Counter({
  name: "linktree_cache_hits_total",
  help: "Cache hits for Linktree profile and link data",
  labelNames: ["cache_type"], // profile | links | analytics
});

const ltRateLimits = new Counter({
  name: "linktree_rate_limits_total",
  help: "Number of 429 responses from Linktree API",
});
```

## Performance Checklist

- [ ] Cache TTLs set: profiles 10min, links 2min, analytics 5min
- [ ] Batch size optimized (10 links per request, 5 concurrent calls)
- [ ] Connection pooling via undici Agent enabled
- [ ] Rate limit retry with exponential backoff in place
- [ ] Monitoring dashboards tracking latency, cache hits, and 429s
- [ ] Cache invalidation on link create/update/delete webhooks

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Stale links shown to visitors | Cache TTL too long for active creators | Lower link cache TTL to 60s for high-traffic profiles |
| 429 during viral traffic spike | Burst of profile reads exceeds rate limit | Enable request queuing with p-limit concurrency of 3 |
| Slow profile page renders | Fetching profile + links sequentially | Parallelize with `Promise.all([getProfile, getLinks])` |
| Connection timeouts to API | No keep-alive, cold TCP for each request | Enable undici connection pooling with 10 persistent sockets |
| Analytics data gaps | Report endpoints are slow, callers timeout | Cache analytics for 5min, use background refresh pattern |

## Output

After applying these optimizations, expect:
- Profile page API latency under 200ms (cached) vs 500ms+ (uncached)
- Cache hit rate above 80% for profile and link data
- Zero 429 errors during normal traffic with graceful degradation during spikes

## Examples

```typescript
// Full optimized profile fetch — cache + rate limit + pooling
const profile = await withRateLimit(() => getCachedProfile("creator-username"));
const links = await withRateLimit(() => getCachedLinks(profile.id));

// Alternative: use in-memory Map instead of Redis for low-traffic integrations
const localCache = new Map<string, { data: any; expiry: number }>();
```

## Resources

- [Linktree API Documentation](https://linktr.ee/marketplace/developer)

## Next Steps

See `linktree-reference-architecture`.
