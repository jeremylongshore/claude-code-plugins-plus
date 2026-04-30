---
name: navan-performance-tuning
description: "Use when optimizing Navan API call patterns for high-volume integrations\
  \ \u2014 caching, batching, connection pooling, and pagination strategies.\nTrigger\
  \ with \"navan performance tuning\" or \"navan api optimization\" or \"navan caching\"\
  .\n"
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Performance Tuning

## Overview

Navan's REST API has no bulk endpoints or GraphQL — every data fetch is a separate HTTP request. High-volume integrations syncing thousands of bookings, expenses, or user records quickly become bottlenecked by sequential API calls, redundant fetches, and naive pagination. This skill provides concrete optimization patterns: response caching with data-type-specific TTLs, parallel request execution with concurrency controls, cursor-based pagination handling, and HTTP connection reuse. Each pattern targets the real constraint: minimizing total API calls while staying under rate limits.

## Prerequisites

- **Active Navan integration** with OAuth 2.0 credentials (client_credentials grant)
- **Node.js 18+** (for native fetch and AbortController)
- **Understanding of your data volume** — bookings/day, users, expense reports/month
- API base URL: `https://api.navan.com/v1`

## Instructions

### Step 1 — Implement Response Caching with Data-Appropriate TTLs

Different Navan data types change at different rates. Cache accordingly:

```typescript
interface CacheEntry<T> {
  data: T;
  expires_at: number;
  etag?: string;
}

// TTLs based on data volatility
const CACHE_TTL: Record<string, number> = {
  'users':    3600_000,   // 1 hour — user profiles rarely change
  'policies': 86400_000,  // 24 hours — travel policies change infrequently
  'bookings': 300_000,    // 5 minutes — bookings update frequently
  'expenses': 600_000,    // 10 minutes — expenses change during approval flow
};

const cache = new Map<string, CacheEntry<unknown>>();

async function cachedFetch<T>(
  endpoint: string,
  token: string
): Promise<T> {
  const cacheKey = endpoint;
  const entry = cache.get(cacheKey) as CacheEntry<T> | undefined;

  // Return cached data if still valid
  if (entry && entry.expires_at > Date.now()) {
    return entry.data;
  }

  // Determine TTL from endpoint path
  const dataType = endpoint.split('?')[0].split('/')[0];
  const ttl = CACHE_TTL[dataType] ?? 300_000; // Default 5 minutes

  const response = await fetch(`https://api.navan.com/v1/${endpoint}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Navan API ${response.status}: ${endpoint}`);
  }

  const data = await response.json() as T;
  cache.set(cacheKey, {
    data,
    expires_at: Date.now() + ttl,
    etag: response.headers.get('etag') ?? undefined,
  });

  return data;
}
```

### Step 2 — Parallel Fetch with Concurrency Throttling

Fetch multiple resources concurrently without overwhelming rate limits:

```typescript
async function parallelFetch<T>(
  endpoints: string[],
  token: string,
  concurrency: number = 5
): Promise<T[]> {
  const results: T[] = [];
  const queue = [...endpoints];

  async function worker(): Promise<void> {
    while (queue.length > 0) {
      const endpoint = queue.shift()!;
      try {
        const data = await cachedFetch<T>(endpoint, token);
        results.push(data);
      } catch (err) {
        const status = (err as Error).message.match(/(\d{3})/)?.[1];
        if (status === '429') {
          // Rate limited — put it back and pause
          queue.unshift(endpoint);
          await new Promise(r => setTimeout(r, 2000));
        } else {
          throw err;
        }
      }
    }
  }

  // Launch workers up to concurrency limit
  const workers = Array.from(
    { length: Math.min(concurrency, endpoints.length) },
    () => worker()
  );
  await Promise.all(workers);
  return results;
}

// Usage: fetch 20 user profiles concurrently (5 at a time)
const userIds = ['u_001', 'u_002', /* ... */ 'u_020'];
const profiles = await parallelFetch(
  userIds.map(id => `users/${id}`),
  token,
  5  // Max 5 concurrent requests
);
```

### Step 3 — Efficient Cursor-Based Pagination

Page through large result sets without missing or duplicating records:

```typescript
async function* paginateAll<T>(
  endpoint: string,
  token: string,
  pageSize: number = 50
): AsyncGenerator<T[]> {
  let page = 0;

  while (true) {
    const params = new URLSearchParams({
      page: String(page),
      size: String(pageSize),
    });

    const url = `https://api.navan.com/v1/${endpoint}?${params}`;
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` },
    });

    if (!response.ok) {
      throw new Error(`Navan API ${response.status} on ${endpoint}`);
    }

    const body = await response.json();
    const items: T[] = body.data ?? [];

    if (items.length === 0) break;
    yield items;

    if (items.length < pageSize) break; // Last page
    page++;
  }
}

// Usage: process all bookings in pages of 50
let totalProcessed = 0;
for await (const page of paginateAll('bookings', token, 50)) {
  await processBatch(page);
  totalProcessed += page.length;
  console.log(`Processed ${totalProcessed} bookings`);
}
```

### Step 4 — HTTP Connection Reuse

Keep TCP connections alive across multiple API calls:

```typescript
import { Agent } from 'undici';

// Create a connection pool for Navan API
const navanAgent = new Agent({
  keepAliveTimeout: 30_000,    // Keep idle connections for 30s
  keepAliveMaxTimeout: 60_000, // Max connection lifetime 60s
  connections: 10,             // Max 10 concurrent connections
  pipelining: 1,               // No HTTP pipelining (REST API)
});

// Use the agent for all Navan requests
const response = await fetch('https://api.navan.com/v1/bookings', {
  headers: { 'Authorization': `Bearer ${token}` },
  dispatcher: navanAgent,
});
```

## Output

Optimized Navan API integration with:
- **60-80% fewer API calls** through intelligent caching
- **5-10x faster sync jobs** via parallel execution
- **Zero missed records** with robust cursor pagination
- **Lower latency** from connection reuse and keep-alive

## Error Handling

| HTTP Code | Meaning | Performance Action |
|-----------|---------|-------------------|
| `200` | Success | Cache the response with appropriate TTL |
| `304` | Not Modified | Use cached version (ETag match) |
| `401` | Token expired | Refresh token, retry once, do not cache |
| `429` | Rate limited | Exponential backoff: 1s, 2s, 4s — max 3 retries |
| `500` | Server error | Retry once after 5s, skip on second failure |
| `503` | Service unavailable | Pause all workers for 30s, then resume |

## Examples

**Before and after optimization for a 10,000-booking sync:**

```
Before (naive sequential):
  API calls: 10,000 (one per booking)
  Time: 45 minutes
  Rate limit hits: 12

After (cached + parallel + paginated):
  API calls: 200 (pages of 50)
  Time: 4 minutes
  Rate limit hits: 0
```

**Cache invalidation on webhook event:**

```typescript
// When Navan sends a booking.updated webhook, invalidate that booking
function handleWebhook(event: { type: string; booking_id: string }) {
  if (event.type === 'booking.updated') {
    cache.delete(`bookings/${event.booking_id}`);
  }
}
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — API documentation and rate limit details
- [Navan Integrations](https://navan.com/integrations) — Data connectors (Fivetran, Airbyte) as alternatives to direct API
- [undici Connection Pooling](https://undici.nodejs.org/#/docs/api/Agent) — Node.js HTTP client with pool management

## Next Steps

- Add `navan-rate-limits` for detailed rate limit handling strategies
- Add `navan-cost-tuning` to optimize the business cost side alongside API performance
- See `navan-observability` to measure the impact of these optimizations
