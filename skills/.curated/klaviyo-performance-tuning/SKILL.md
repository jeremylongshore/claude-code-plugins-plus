---
name: klaviyo-performance-tuning
description: |
  Optimize Klaviyo API performance with caching, batching, and pagination tuning.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Klaviyo integrations.
  Trigger with phrases like "klaviyo performance", "optimize klaviyo",
  "klaviyo latency", "klaviyo caching", "klaviyo slow", "klaviyo batch".
allowed-tools: Read, Write, Edit
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Performance Tuning

## Overview

Optimize Klaviyo API performance with response caching, request batching, cursor-based pagination, sparse fieldsets, and connection pooling. This skill diagnoses where an integration is slow, then applies the right technique — payload reduction, memory caching, bounded pagination, request coalescing, or rate-limit-aware concurrency.

Read this file for the workflow and the decision guide. Full, copy-pasteable code for every step lives in [references/implementation.md](references/implementation.md); combined real-world scenarios live in [references/examples.md](references/examples.md).

## Prerequisites

- `klaviyo-api` SDK installed
- Understanding of Klaviyo's rate limits (75 req/s burst, 700 req/min)
- Redis or in-memory cache (optional)
- For batching/concurrency helpers: `dataloader`, `p-queue`, `lru-cache`

## Klaviyo API Performance Characteristics

| Operation | Typical Latency | Max Page Size |
|-----------|----------------|---------------|
| Get Profile by ID | 50-150ms | N/A |
| Get Profiles (list) | 100-300ms | 20 (default), 100 (some endpoints) |
| Create Profile | 100-200ms | N/A |
| Create Event | 50-100ms | N/A |
| Get Segment Profiles | 200-500ms | 20 |
| Campaign Operations | 200-500ms | 20 |

## Instructions

Apply the techniques in order — each is independent, so start with the one that matches your bottleneck. Every step below has a full implementation in [references/implementation.md](references/implementation.md).

### Step 1: Sparse Fieldsets (Reduce Payload Size)

Klaviyo supports JSON:API sparse fieldsets — request only the fields you need instead of the 20+ default attributes. This is the cheapest win and applies to every read.

```typescript
// GOOD: Only fetch the fields you use (much smaller payload)
const profiles = await profilesApi.getProfiles({
  fieldsProfile: ['email', 'first_name', 'created'],  // snake_case = API names
});
```

### Step 2: Response Caching

Wrap read calls in an `LRUCache` keyed by query, with per-resource TTLs (profiles 5 min, segments 15 min — they change less often). See the caching implementation in [references/implementation.md](references/implementation.md).

### Step 3: Efficient Pagination

Use a `fetchAllPages` helper that follows the `links.next` cursor with a `maxPages` ceiling so large exports terminate predictably. See the pagination implementation in [references/implementation.md](references/implementation.md).

### Step 4: Request Batching with DataLoader

Coalesce many `getProfile(id)` calls in a single tick into concurrency-controlled requests with `DataLoader` (`maxBatchSize: 10`, 50 ms window). See the batching implementation in [references/implementation.md](references/implementation.md).

### Step 5: Parallel API Calls with Concurrency Control

Drive bulk writes through a `PQueue` capped at 50 req/s — a safe margin under the 75 req/s burst limit — with progress logging. See the concurrency implementation in [references/implementation.md](references/implementation.md).

### Step 6: Performance Monitoring

Wrap calls in `measuredCall` and read a p95 summary via `getPerfSummary` to find the real bottleneck before optimizing. See the monitoring implementation in [references/implementation.md](references/implementation.md).

## Output

Applying this skill produces:

- **Sparse-fieldset read calls** with 50-80% smaller payloads on list endpoints.
- **A cache module** (`src/klaviyo/cache.ts`) that serves repeated reads from memory with per-resource TTLs.
- **A pagination helper** (`src/klaviyo/pagination.ts`) that safely walks cursor-paginated endpoints to completion under a `maxPages` guard.
- **Batching + concurrency helpers** that keep bulk operations under Klaviyo's 75 req/s burst and 700 req/min ceilings.
- **A perf-monitoring module** (`src/klaviyo/perf-monitor.ts`) emitting per-operation `avg`, `p95`, and `count` so you can verify the gains.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cache stampede | Many requests on cache miss | Use stale-while-revalidate pattern |
| Pagination timeout | Very large datasets | Set `maxPages` limit, process in chunks |
| Rate limit on bulk ops | Too much concurrency | Reduce `PQueue` concurrency/intervalCap |
| Slow filter queries | Complex filter expressions | Simplify filters, use segment IDs instead |

## Examples

Worked, end-to-end scenarios that combine the steps above are in [references/examples.md](references/examples.md):

- **Fast cached profile lookup** — sparse fieldsets + LRU caching for a repeated lookup.
- **Export a large list** — bounded cursor pagination for a multi-hundred-thousand-member list.
- **Bulk-update 10,000 profiles** — `PQueue` concurrency under the rate limit.
- **Measure where the time goes** — `measuredCall` + `getPerfSummary` to find the slow op first.

Minimal caching example (full versions in the reference):

```typescript
import { cachedKlaviyoCall } from './cache';

const profile = await cachedKlaviyoCall(
  `profile:${email}`,
  () => profilesApi.getProfiles({ filter: `equals(email,"${email}")` }),
  5 * 60 * 1000  // 5 minute TTL
);
```

## Resources

- [Klaviyo API Filtering](https://developers.klaviyo.com/en/reference/api_overview#filtering)
- [JSON:API Sparse Fieldsets](https://jsonapi.org/format/#fetching-sparse-fieldsets)
- [DataLoader](https://github.com/graphql/dataloader)
- [p-queue](https://github.com/sindresorhus/p-queue)
- [references/implementation.md](references/implementation.md) — full code for every step
- [references/examples.md](references/examples.md) — combined real-world scenarios

## Next Steps

Once reads are cached and bulk writes are rate-limit-safe, profile the workload with `getPerfSummary` (Step 6) to confirm the p95 improvement, then tune TTLs and concurrency to your traffic. For cost optimization of the same integration, see the `klaviyo-cost-tuning` skill.
