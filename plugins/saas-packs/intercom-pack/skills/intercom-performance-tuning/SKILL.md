---
name: intercom-performance-tuning
description: |
  Optimize Intercom API performance with caching, search optimization, and pagination.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Intercom integrations.
  Trigger with phrases like "intercom performance", "optimize intercom",
  "intercom latency", "intercom caching", "intercom slow", "intercom pagination".
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Performance Tuning

## Overview

Optimize Intercom API performance through response caching, efficient search queries, cursor-based pagination, connection pooling, and request batching.

## Prerequisites

- `intercom-client` SDK installed
- Understanding of Intercom data model
- Redis or in-memory cache available (optional)

## Authentication

All requests authenticate with an Intercom access token passed as a bearer token. Store it as `INTERCOM_ACCESS_TOKEN` in the environment and let the SDK read it — never hardcode it:

```typescript
const client = new IntercomClient({ token: process.env.INTERCOM_ACCESS_TOKEN! });
```

For raw `fetch` calls, send `Authorization: Bearer ${token}`.

## Intercom API Latency Baselines

| Operation | Typical P50 | Typical P95 | Notes |
|-----------|-------------|-------------|-------|
| `GET /me` (health check) | 50ms | 150ms | Lightest endpoint |
| `GET /contacts/:id` | 80ms | 200ms | Single lookup |
| `POST /contacts/search` | 120ms | 400ms | Depends on query complexity |
| `GET /conversations/:id` | 100ms | 300ms | Heavier with parts (up to 500) |
| `POST /contacts` (create) | 150ms | 400ms | Write operation |
| `GET /contacts` (list) | 100ms | 350ms | Paginated, 50 per page |
| `POST /messages` | 200ms | 500ms | Triggers delivery pipeline |

## Instructions

Apply these six techniques in order of impact. Each has a complete, copy-pasteable implementation in [references/implementation.md](references/implementation.md); the summaries and the caching skeleton below are enough to follow the workflow at a high level.

1. **Response caching** — wrap contact/conversation reads in an `LRUCache` (read-through), and invalidate on update or via webhook so cached data never goes stale. This is the single biggest win for read-heavy integrations.
2. **Efficient search queries** — push predicates into the `AND`-combined `query` and request only the `per_page` you need (max 150), rather than fetching broadly and filtering client-side.
3. **Optimized pagination** — stream large result sets with an async generator over cursor pagination (`startingAfter`) to keep memory flat, and process in fixed-size batches.
4. **Connection pooling** — reuse TCP connections with an `https.Agent` (`keepAlive: true`) so you pay the TLS handshake cost once, not per request.
5. **Parallel requests with rate awareness** — fan out concurrent lookups through a `p-queue` bounded by `concurrency` + `intervalCap` so batches stay under the rate limit.
6. **Performance monitoring** — wrap every call in a `measuredCall` helper that emits a structured latency metric, so you can chart real P50/P95 against the baselines above.

The read-through cache skeleton (Step 1) — the foundation everything else builds on:

```typescript
import { LRUCache } from "lru-cache";
import { IntercomClient } from "intercom-client";
import { Intercom } from "intercom-client";

const contactCache = new LRUCache<string, Intercom.Contact>({
  max: 5000,
  ttl: 5 * 60 * 1000,  // 5 minutes
});

const client = new IntercomClient({ token: process.env.INTERCOM_ACCESS_TOKEN! });

async function getContact(contactId: string): Promise<Intercom.Contact> {
  const cached = contactCache.get(contactId);
  if (cached) return cached;
  const contact = await client.contacts.find({ contactId });
  contactCache.set(contactId, contact);
  return contact;
}
```

See [references/implementation.md](references/implementation.md) for the full code of all six steps, including invalidation, streaming pagination, connection pooling, the rate-aware queue, and the monitoring wrapper.

## Output

Applying these techniques produces:

- **A cached read path** — repeat contact/conversation lookups served from memory in microseconds instead of an 80–200ms round trip, with correctness preserved via update/webhook invalidation.
- **Bounded, streaming iteration** — an async generator that walks arbitrarily large contact lists at flat memory, plus a batch processor returning the total count handled.
- **Rate-safe concurrency** — parallel lookups that stay under Intercom's rate limit, returning a `Map<contactId, Contact>`.
- **Structured latency metrics** — one JSON line per call (`{"metric":"intercom.api.call","operation":...,"duration_ms":...,"status":...}`) ready to ship to your metrics pipeline and compare against the latency baselines table.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cache stampede | Many concurrent cache misses | Use mutex/lock per key |
| Memory pressure | Cache too large | Set `max` on LRUCache |
| Stale data | TTL too long | Use webhook invalidation |
| Pagination timeouts | Large data set + slow network | Reduce per_page, add delays |
| Rate limit during batch | Too many parallel requests | Lower PQueue concurrency |

## Examples

Quick reference — full runnable versions are in [references/examples.md](references/examples.md):

- **Cached single-contact lookup** — read-through cache; first call hits the API, later calls within the TTL are free.
- **Narrow search vs broad scan** — a BAD 150-row unfiltered page vs a GOOD 25-row targeted query.
- **Stream and batch-process every contact** — cursor pagination + fixed-size batch flushes over an unbounded list.
- **Parallel batch lookup** — resolve many IDs concurrently under the rate limit, cache-first.
- **Latency instrumentation** — wrap any call in `measuredCall` to emit a per-call metric line.

Minimal instrumentation example:

```typescript
const contact = await measuredCall("contacts.find", () =>
  client.contacts.find({ contactId: "abc123" })
);
// → {"metric":"intercom.api.call","operation":"contacts.find","duration_ms":84,"status":"success"}
```

## Resources

- [Full implementation (all six steps)](references/implementation.md)
- [Worked examples](references/examples.md)
- [Pagination](https://developers.intercom.com/docs/build-an-integration/learn-more/rest-apis/pagination)
- [Search Contacts](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts/searchcontacts)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For cost optimization, see the `intercom-cost-tuning` skill, which covers request-volume reduction, webhook-driven syncing instead of polling, and tiered caching to lower monthly API spend.
