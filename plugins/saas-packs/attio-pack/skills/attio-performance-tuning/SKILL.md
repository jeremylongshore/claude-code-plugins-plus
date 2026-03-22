---
name: attio-performance-tuning
description: |
  Optimize Attio API performance -- caching, batch queries, pagination
  strategies, connection pooling, and latency reduction.
  Trigger: "attio performance", "optimize attio", "attio slow",
  "attio latency", "attio caching", "attio batch requests".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Performance Tuning

## Overview

Attio's REST API returns JSON over HTTPS. Performance optimization focuses on reducing request count (batching, caching), maximizing throughput (connection reuse, pagination), and minimizing latency (selective field fetching, parallel queries).

## Key Performance Facts

| Factor | Detail |
|--------|--------|
| Rate limit | Sliding 10-second window, shared across all tokens |
| Pagination default | `limit: 500` (max per page) |
| API base | `https://api.attio.com/v2` |
| Auth overhead | Bearer token in header (minimal) |
| Response format | JSON only (no binary/protobuf) |

## Instructions

### Strategy 1: Response Caching with LRU

Cache read-heavy data (object schemas, attribute definitions) that rarely change:

```typescript
import { LRUCache } from "lru-cache";

const cache = new LRUCache<string, unknown>({
  max: 500,              // Max entries
  ttl: 5 * 60 * 1000,   // 5 minutes for schema data
});

async function cachedGet<T>(
  client: AttioClient,
  path: string,
  ttlMs?: number
): Promise<T> {
  const cached = cache.get(path) as T | undefined;
  if (cached) return cached;

  const result = await client.get<T>(path);
  cache.set(path, result, { ttl: ttlMs });
  return result;
}

// Schema data: cache for 30 minutes (rarely changes)
const objects = await cachedGet(client, "/objects", 30 * 60 * 1000);
const attrs = await cachedGet(client, "/objects/people/attributes", 30 * 60 * 1000);

// Record data: cache for 1-5 minutes (changes more often)
const person = await cachedGet(client, `/objects/people/records/${id}`, 60 * 1000);
```

### Strategy 2: Batch Queries Instead of N+1

```typescript
// BAD: N+1 pattern -- one request per email lookup
const people = [];
for (const email of customerEmails) {
  const res = await client.post("/objects/people/records/query", {
    filter: { email_addresses: email },
    limit: 1,
  });
  people.push(res.data[0]);
}
// Cost: N requests

// GOOD: Single query with $in operator
const allPeople = await client.post<{ data: AttioRecord[] }>(
  "/objects/people/records/query",
  {
    filter: {
      email_addresses: {
        email_address: { $in: customerEmails },
      },
    },
    limit: customerEmails.length,
  }
);
// Cost: 1 request
```

### Strategy 3: Parallel Independent Queries

```typescript
// Fetch multiple object types in parallel
const [people, companies, deals] = await Promise.all([
  client.post<{ data: AttioRecord[] }>(
    "/objects/people/records/query",
    { limit: 100 }
  ),
  client.post<{ data: AttioRecord[] }>(
    "/objects/companies/records/query",
    { limit: 100 }
  ),
  client.post<{ data: AttioRecord[] }>(
    "/objects/deals/records/query",
    { limit: 100 }
  ),
]);
```

### Strategy 4: Efficient Pagination

```typescript
// Use maximum page size (500) to minimize round trips
async function fetchAllRecords(
  client: AttioClient,
  objectSlug: string,
  filter?: Record<string, unknown>
): Promise<AttioRecord[]> {
  const PAGE_SIZE = 500; // Attio's maximum
  const allRecords: AttioRecord[] = [];
  let offset = 0;

  while (true) {
    const page = await client.post<{ data: AttioRecord[] }>(
      `/objects/${objectSlug}/records/query`,
      {
        ...(filter ? { filter } : {}),
        limit: PAGE_SIZE,
        offset,
      }
    );

    allRecords.push(...page.data);

    // If we got fewer than PAGE_SIZE, we've reached the end
    if (page.data.length < PAGE_SIZE) break;
    offset += PAGE_SIZE;
  }

  return allRecords;
}
```

### Strategy 5: Streaming Pagination with AsyncGenerator

For processing large datasets without loading everything into memory:

```typescript
async function* streamRecords(
  client: AttioClient,
  objectSlug: string,
  filter?: Record<string, unknown>
): AsyncGenerator<AttioRecord> {
  const PAGE_SIZE = 500;
  let offset = 0;
  let hasMore = true;

  while (hasMore) {
    const page = await client.post<{ data: AttioRecord[] }>(
      `/objects/${objectSlug}/records/query`,
      { ...(filter ? { filter } : {}), limit: PAGE_SIZE, offset }
    );

    for (const record of page.data) {
      yield record;
    }

    hasMore = page.data.length === PAGE_SIZE;
    offset += PAGE_SIZE;
  }
}

// Process without loading all records into memory
let count = 0;
for await (const record of streamRecords(client, "people")) {
  await processRecord(record);
  count++;
}
console.log(`Processed ${count} records`);
```

### Strategy 6: Connection Keep-Alive

```typescript
import { Agent } from "https";

// Reuse TCP connections across requests
const keepAliveAgent = new Agent({
  keepAlive: true,
  maxSockets: 10,
  maxFreeSockets: 5,
  timeout: 30_000,
});

// Use with node-fetch or undici
import { fetch as undiciFetch, Agent as UndiciAgent } from "undici";

const dispatcher = new UndiciAgent({
  keepAliveTimeout: 30_000,
  keepAliveMaxTimeout: 60_000,
  connections: 10,
});

const res = await undiciFetch("https://api.attio.com/v2/objects", {
  headers: { Authorization: `Bearer ${process.env.ATTIO_API_KEY}` },
  dispatcher,
});
```

### Strategy 7: Webhook-Driven Cache Invalidation

Instead of polling for changes, use webhooks to invalidate cached data:

```typescript
const recordCache = new LRUCache<string, AttioRecord>({ max: 5000, ttl: 300_000 });

// On webhook event
async function handleCacheInvalidation(event: AttioWebhookEvent): Promise<void> {
  switch (event.event_type) {
    case "record.updated":
    case "record.deleted":
    case "record.merged":
      recordCache.delete(event.record?.id?.record_id || "");
      break;
  }
}
```

### Strategy 8: Request Timing and Monitoring

```typescript
async function timedRequest<T>(
  name: string,
  operation: () => Promise<T>
): Promise<T> {
  const start = performance.now();
  try {
    const result = await operation();
    const duration = performance.now() - start;
    console.log(JSON.stringify({
      metric: "attio_api_duration_ms",
      operation: name,
      duration: Math.round(duration),
      status: "success",
    }));
    return result;
  } catch (err) {
    const duration = performance.now() - start;
    console.error(JSON.stringify({
      metric: "attio_api_duration_ms",
      operation: name,
      duration: Math.round(duration),
      status: "error",
      error: (err as Error).message,
    }));
    throw err;
  }
}

// Usage
const people = await timedRequest("query_people", () =>
  client.post("/objects/people/records/query", { limit: 100 })
);
```

## Error Handling

| Performance issue | Symptom | Solution |
|------------------|---------|----------|
| N+1 queries | Slow bulk operations | Use `$in` filter in single query |
| Cache miss storm | Burst of identical requests | Use stale-while-revalidate or mutex |
| Memory pressure | Large dataset pagination | Use AsyncGenerator streaming |
| Connection overhead | High latency per request | Enable keep-alive agent |
| Stale cached data | Showing outdated records | Add webhook-driven invalidation |

## Resources

- [Attio Pagination Guide](https://docs.attio.com/rest-api/guides/pagination)
- [Attio Filtering and Sorting](https://docs.attio.com/rest-api/how-to/filtering-and-sorting)
- [Attio Rate Limiting](https://docs.attio.com/rest-api/guides/rate-limiting)
- [LRU Cache Documentation](https://github.com/isaacs/node-lru-cache)

## Next Steps

For cost optimization, see `attio-cost-tuning`.
