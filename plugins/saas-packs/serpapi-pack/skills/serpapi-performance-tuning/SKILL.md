---
name: serpapi-performance-tuning
description: |
  Optimize SerpApi performance with caching, async searches, and result filtering.
  Use when reducing latency, minimizing credit consumption,
  or optimizing search throughput.
  Trigger: "serpapi performance", "optimize serpapi", "serpapi caching", "serpapi slow".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Performance Tuning

## Overview

SerpApi typical latency: 2-5 seconds per search (real-time scraping). Main optimization: aggressive caching since search results change slowly. Secondary: use Google Light API for faster responses, reduce `num` parameter, and parallelize independent searches.

## Instructions

### Step 1: Multi-Layer Caching

```typescript
import { LRUCache } from 'lru-cache';
import { Redis } from 'ioredis';
import { getJson } from 'serpapi';

// L1: In-memory (fastest, per-instance)
const l1 = new LRUCache<string, any>({ max: 1000, ttl: 600_000 }); // 10 min

// L2: Redis (shared across instances)
const redis = new Redis(process.env.REDIS_URL!);

async function cachedSearch(params: Record<string, any>): Promise<any> {
  const key = `serpapi:${JSON.stringify(params)}`;

  // L1 check
  const l1Hit = l1.get(key);
  if (l1Hit) return l1Hit;

  // L2 check
  const l2Hit = await redis.get(key);
  if (l2Hit) {
    const parsed = JSON.parse(l2Hit);
    l1.set(key, parsed);
    return parsed;
  }

  // Cache miss: real API call
  const result = await getJson({ ...params, api_key: process.env.SERPAPI_API_KEY });
  l1.set(key, result);
  await redis.setex(key, 3600, JSON.stringify(result)); // 1 hour in Redis
  return result;
}
```

### Step 2: Google Light API (Faster)

```python
# Google Light API: ~1s instead of 2-5s, limited result fields
result = client.search(engine="google_light", q="fast query", num=5)
# Returns: organic_results with title, link, snippet only
# No knowledge_graph, answer_box, or rich snippets
```

### Step 3: Reduce Response Size

```python
# Only get the fields you need
result = client.search(
    engine="google", q="query",
    num=5,         # Fewer results = faster
    no_cache=False, # Use SerpApi's server-side cache (default)
)

# Strip metadata to reduce memory/storage
clean = {
    "organic_results": result.get("organic_results", []),
    "answer_box": result.get("answer_box"),
    "search_id": result["search_metadata"]["id"],
}
```

### Step 4: Parallel Search

```typescript
import PQueue from 'p-queue';

const queue = new PQueue({ concurrency: 5, interval: 1000, intervalCap: 5 });

async function batchSearch(queries: string[]): Promise<any[]> {
  return Promise.all(
    queries.map(q =>
      queue.add(() => cachedSearch({ engine: 'google', q, num: 5 }))
    )
  );
}

// 10 queries, 5 parallel, rate limited: ~4 seconds total
const results = await batchSearch(['query1', 'query2', /* ... */]);
```

## Latency Benchmarks

| Method | Typical Latency | Credits |
|--------|----------------|---------|
| Google Search (uncached) | 2-5s | 1 |
| Google Light | 1-2s | 1 |
| L1 cache hit | < 1ms | 0 |
| Redis cache hit | 1-5ms | 0 |
| Archive retrieval | 500ms | 0 |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cache stampede | TTL expiry under load | Stale-while-revalidate |
| High latency | Complex queries | Use Google Light API |
| Memory pressure | Large cache | Limit LRU max entries |

## Resources

- [Google Light API](https://serpapi.com/google-light-api)
- [SerpApi Caching](https://serpapi.com/search-api#api-parameters-serpapi-parameters-no-cache)

## Next Steps

For cost optimization, see `serpapi-cost-tuning`.
