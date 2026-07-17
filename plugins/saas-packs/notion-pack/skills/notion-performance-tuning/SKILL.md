---
name: notion-performance-tuning
description: 'Optimize Notion API performance with caching, batching, parallel requests,
  and incremental sync.

  Use when experiencing slow API responses, implementing caching strategies,

  reducing API call volume, or tuning request patterns for Notion integrations.

  Trigger with phrases like "notion performance", "optimize notion api",

  "notion latency", "notion caching", "notion slow", "notion batch requests",

  "notion incremental sync", "notion reduce api calls".

  '
allowed-tools: Read, Write, Edit
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Performance Tuning

## Overview

Optimize Notion API performance by minimizing API calls, caching responses with TTL-based invalidation, batching block appends, parallelizing requests within rate limits, selecting only needed properties, and implementing incremental sync patterns. Target latency benchmarks: Database Query p50=150ms, Page Create p50=200ms, Search p50=300ms.

## Prerequisites

- `@notionhq/client` installed (`npm install @notionhq/client`)
- `p-queue` for rate-limited parallelism (`npm install p-queue`)
- `lru-cache` for TTL-based caching (`npm install lru-cache`)
- Authentication: a Notion integration token in `NOTION_TOKEN` (internal integration secret from <https://www.notion.so/my-integrations>), passed as `new Client({ auth: process.env.NOTION_TOKEN })`
- Understanding of your access patterns (read-heavy vs write-heavy)
- Optional: Redis or `ioredis` for distributed caching across instances

## Instructions

Apply the three techniques in order — each builds on the previous one. The lean
skeletons below are enough to follow the workflow; drill into the linked
reference files for the complete, copy-paste-ready code.

### Step 1: Minimize API Calls and Reduce Payload

Avoid N+1 patterns, page with `page_size: 100` (the maximum), select only the properties you need with `filter_properties`, and batch block appends in chunks of 100.

```typescript
// Batch block appends — up to 100 blocks per request (API maximum)
for (let i = 0; i < blocks.length; i += 100) {
  await notion.blocks.children.append({
    block_id: pageId,
    children: blocks.slice(i, i + 100),
  });
}
```

See [full implementation walkthrough](references/implementation.md) for the N+1-vs-batched query comparison, `filter_properties` usage, and selective block-tree expansion.

### Step 2: Cache Responses with TTL-Based Invalidation

Use an LRU cache with per-operation TTLs (short for volatile data like search, longer for stable data like schemas) and invalidate entries on every write to keep reads consistent.

```typescript
import { LRUCache } from 'lru-cache';
const cache = new LRUCache<string, any>({ max: 1000, ttl: 60_000, allowStale: false });
// Invalidate on write: for (const key of cache.keys())
//   if (key.startsWith(`db:${dbId}:`)) cache.delete(key);
```

See [full implementation walkthrough](references/implementation.md) for tiered TTL configuration, cursor-based cached pagination, write-through invalidation, and cache-stats monitoring.

### Step 3: Parallel Requests with Rate-Limited Queue and Latency Monitoring

See [parallel requests and latency monitoring](references/parallel-requests-and-monitoring.md) for `p-queue` rate-limited parallelism, latency tracking with p50/p95 benchmarks, incremental sync, and memory-efficient streaming via async generators.

## Output

- Reduced API call count through property selection, filtering, and batched block appends
- TTL-based caching with write-through invalidation for data consistency
- Parallel requests within Notion's 3 req/sec rate limit using `p-queue`
- Incremental sync fetching only changed pages since last sync timestamp
- Latency monitoring with p50/p95 tracking against target benchmarks
- Memory-efficient streaming for large datasets via async generators

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| Stale cache data | TTL too long for volatile data | Use shorter TTL (30s for search, 60s for queries) |
| Rate limit despite queue | Other code paths making unqueued calls | Use a single shared `p-queue` instance across your app |
| Memory pressure from cache | Too many entries or large payloads | Set `max` on LRU cache; use `filter_properties` to shrink payloads |
| Pagination never ends | Circular cursor or API bug | Add max-iteration guard (`if (requestCount > 50) break`) |
| Incremental sync misses | Clock skew between client and API | Subtract a 5-second buffer from `lastSyncTime` |
| p50 latency above target | Cold cache or large responses | Pre-fetch critical pages; use `filter_properties` to reduce response size |

## Examples

A complete `NotionPerf` class combining caching, rate limiting, and incremental
sync, plus a before/after latency benchmark, lives in
[the examples reference](references/examples.md). The essential surface:

```typescript
const perf = new NotionPerf(process.env.NOTION_TOKEN!);
const results = await perf.query('db-id-here');  // cached + rate-limited
const updates = await perf.sync('db-id-here');   // fetches only changed pages
```

See [the examples reference](references/examples.md) for the full class definition and the latency-comparison harness.

## Resources

- [Query a Database](https://developers.notion.com/reference/post-database-query) — filtering, sorting, pagination
- [Append Block Children](https://developers.notion.com/reference/patch-block-children) — batch up to 100 blocks
- [Request Limits](https://developers.notion.com/reference/request-limits) — 3 req/sec per integration
- [Notion SDK (notion-sdk-js)](https://github.com/makenotion/notion-sdk-js) — `@notionhq/client` source
- [p-queue](https://github.com/sindresorhus/p-queue) — promise-based rate-limited queue
- [LRU Cache](https://github.com/isaacs/node-lru-cache) — TTL-based in-memory cache

## Next Steps

After tuning request patterns, wire up event-driven invalidation instead of relying purely on TTL expiry: the `notion-webhooks-events` skill covers receiving Notion webhook events and invalidating exactly the cache keys that changed, which keeps caches fresh without shortening TTLs.
