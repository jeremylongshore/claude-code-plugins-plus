---
name: lucidchart-performance-tuning
description: |
  Optimize Lucidchart API integration performance with caching, batch shape operations, and pagination strategies.
  Use when diagram exports are slow, shape updates hit rate limits, or document list queries time out.
  Trigger with "lucidchart performance tuning".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Performance Tuning

## Overview

Lucidchart documents can contain thousands of shapes and connectors — a single enterprise diagram may hold 500+ elements across multiple pages, making bulk reads and exports the primary API bottleneck. This skill covers caching document metadata, batching shape operations, and managing Lucid's rate limits to keep integrations responsive.

## Instructions

1. Implement Redis caching (or in-memory Map for development) with document-appropriate TTLs
2. Use cursor-based pagination for all document list operations to avoid incomplete results
3. Wrap API calls with the rate limit handler, especially for bulk shape updates and exports
4. Configure connection pooling with extended timeouts for export endpoints

## Prerequisites

- Lucid OAuth2 client credentials with `lucidchart.document` scope
- Redis instance for document/shape metadata caching
- Node.js 18+ with native fetch
- Understanding of Lucid document structure (documents, pages, shapes, lines)

## Caching Strategy

```typescript
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL);

// Document metadata is stable — cache 15 minutes
// Shape data changes during active editing — cache 1 minute
const TTL = { docList: 900, docMeta: 600, shapes: 60, exports: 300 } as const;

async function getCachedDocument(docId: string): Promise<LucidDocument> {
  const key = `lucid:doc:${docId}`;
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const doc = await lucidApi.getDocument(docId);
  await redis.setex(key, TTL.docMeta, JSON.stringify(doc));
  return doc;
}

async function getCachedShapes(docId: string, pageId: string): Promise<LucidShape[]> {
  const key = `lucid:shapes:${docId}:${pageId}`;
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const shapes = await lucidApi.getShapes(docId, pageId);
  await redis.setex(key, TTL.shapes, JSON.stringify(shapes));
  return shapes;
}
```

## Batch Operations

```typescript
import pLimit from "p-limit";

const limit = pLimit(4); // Lucid API concurrency — keep conservative

// Paginate through all documents in a workspace
async function fetchAllDocuments(folderId: string): Promise<LucidDocument[]> {
  const docs: LucidDocument[] = [];
  let cursor: string | undefined;

  do {
    const page = await lucidApi.listDocuments(folderId, { cursor, limit: 100 });
    docs.push(...page.documents);
    cursor = page.nextCursor;
  } while (cursor);

  return docs;
}

// Batch shape updates — group by page to minimize API round trips
async function batchUpdateShapes(
  docId: string,
  updates: ShapeUpdate[]
): Promise<void> {
  const byPage = groupBy(updates, (u) => u.pageId);
  for (const [pageId, pageUpdates] of Object.entries(byPage)) {
    const chunks = chunkArray(pageUpdates, 25); // 25 shapes per batch
    for (const chunk of chunks) {
      await Promise.all(chunk.map((u) => limit(() => lucidApi.updateShape(docId, pageId, u))));
    }
  }
}
```

## Connection Pooling

```typescript
import { Agent } from "undici";

const lucidAgent = new Agent({
  connect: { timeout: 10_000 }, // Lucid exports can be slow
  keepAliveTimeout: 30_000,
  keepAliveMaxTimeout: 60_000,
  pipelining: 1,
  connections: 8, // Persistent pool for Lucid API
});

async function lucidFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`https://api.lucid.co/v1${path}`, {
    ...init,
    // @ts-expect-error undici dispatcher
    dispatcher: lucidAgent,
    headers: { Authorization: `Bearer ${process.env.LUCID_ACCESS_TOKEN}`, ...init?.headers },
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
        const retryAfter = parseInt(err.headers?.["x-ratelimit-reset"] ?? "10", 10);
        const backoff = retryAfter * 1000 * Math.pow(2, attempt);
        console.warn(`Lucid rate limited. Retrying in ${backoff}ms (attempt ${attempt + 1})`);
        await new Promise((r) => setTimeout(r, backoff));
        continue;
      }
      throw err;
    }
  }
  throw new Error("Lucid API: max retries exceeded");
}
```

## Monitoring & Metrics

```typescript
import { Counter, Histogram } from "prom-client";

const lucidApiLatency = new Histogram({
  name: "lucidchart_api_duration_seconds",
  help: "Lucid API call latency",
  labelNames: ["endpoint", "status"],
  buckets: [0.1, 0.5, 1, 2, 5, 10], // Exports can take 5-10s
});

const lucidCacheHits = new Counter({
  name: "lucidchart_cache_hits_total",
  help: "Cache hits for Lucid document and shape data",
  labelNames: ["cache_type"], // docList | docMeta | shapes | exports
});

const lucidRateLimits = new Counter({
  name: "lucidchart_rate_limits_total",
  help: "Number of 429 responses from Lucid API",
});
```

## Performance Checklist

- [ ] Cache TTLs set: doc list 15min, doc metadata 10min, shapes 1min, exports 5min
- [ ] Batch size optimized (25 shapes per request, 4 concurrent calls)
- [ ] Cursor-based pagination for document lists (100 per page)
- [ ] Connection pooling via undici Agent with 10s timeout for exports
- [ ] Rate limit retry with exponential backoff and x-ratelimit-reset parsing
- [ ] Monitoring dashboards tracking latency, cache hits, and 429s

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Timeouts on large diagram exports | PDF/PNG export of 500+ shape documents | Increase timeout to 30s, use async export with polling |
| Stale shape positions after edits | Shape cache served during collaborative editing | Lower shape TTL to 30s or invalidate on webhook |
| Pagination loops never complete | Missing cursor termination check | Always check `nextCursor` is defined before continuing |
| Slow document list in large workspaces | Fetching all docs without folder scoping | Filter by folder ID and use pagination with limit=100 |
| 429 during bulk diagram migration | Parallel shape creates exceed rate limit | Reduce p-limit concurrency to 2 and add 200ms delay between batches |

## Output

After applying these optimizations, expect:
- Document metadata reads under 100ms (cached) vs 400ms+ (uncached)
- Shape batch updates completing 5x faster than sequential calls
- Export operations handled gracefully with async polling instead of timeout failures

## Examples

```typescript
// Full optimized document read — cache + rate limit + pooling
const doc = await withRateLimit(() => getCachedDocument("doc-abc123"));
const shapes = await withRateLimit(() => getCachedShapes(doc.id, doc.pages[0].id));

// Alternative: use async export polling for large diagrams instead of synchronous fetch
const exportJob = await lucidApi.startExport(docId, { format: "png" });
const result = await pollUntilComplete(exportJob.id, { maxWait: 30_000 });
```

## Resources

- [Lucid Developer Documentation](https://developer.lucid.co/reference/overview)

## Next Steps

See `lucidchart-reference-architecture`.
