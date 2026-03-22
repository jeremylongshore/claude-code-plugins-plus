---
name: miro-performance-tuning
description: |
  Optimize Miro REST API v2 performance with caching, cursor pagination,
  request batching, and connection pooling for high-throughput integrations.
  Trigger with phrases like "miro performance", "optimize miro",
  "miro latency", "miro caching", "miro slow", "miro batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, performance, caching]
compatible-with: claude-code
---

# Miro Performance Tuning

## Overview

Optimize Miro REST API v2 throughput and latency. Key levers: minimize API calls with cursor pagination, cache board/item data, batch writes with controlled concurrency, and use connection pooling.

## Latency Benchmarks

Typical latencies for `api.miro.com` (US region):

| Operation | Endpoint | P50 | P95 | Credits |
|-----------|----------|-----|-----|---------|
| Get board | `GET /v2/boards/{id}` | 80ms | 200ms | Level 1 |
| List items (50) | `GET /v2/boards/{id}/items?limit=50` | 120ms | 350ms | Level 1 |
| Create sticky note | `POST /v2/boards/{id}/sticky_notes` | 150ms | 400ms | Level 2 |
| Create connector | `POST /v2/boards/{id}/connectors` | 160ms | 420ms | Level 2 |
| Update item | `PATCH /v2/boards/{id}/items/{id}` | 130ms | 350ms | Level 2 |
| Delete item | `DELETE /v2/boards/{id}/items/{id}` | 100ms | 280ms | Level 2 |

## Cursor Pagination (Eliminate Over-Fetching)

Miro v2 uses cursor-based pagination. Fetch only what you need.

```typescript
// Efficient paginated iterator
async function* paginateItems(
  boardId: string,
  options: { type?: string; limit?: number } = {}
): AsyncGenerator<MiroBoardItem> {
  const limit = options.limit ?? 50;  // Max 50 per page
  let cursor: string | undefined;

  do {
    const params = new URLSearchParams({ limit: String(limit) });
    if (options.type) params.set('type', options.type);
    if (cursor) params.set('cursor', cursor);

    const response = await fetch(
      `https://api.miro.com/v2/boards/${boardId}/items?${params}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );

    const page = await response.json();
    for (const item of page.data) {
      yield item;
    }

    cursor = page.cursor;  // undefined when no more pages
  } while (cursor);
}

// Usage: process items without loading entire board into memory
for await (const item of paginateItems(boardId, { type: 'sticky_note' })) {
  await processItem(item);
}
```

## Caching Strategy

### In-Memory Cache (Single Instance)

```typescript
import { LRUCache } from 'lru-cache';

const boardCache = new LRUCache<string, unknown>({
  max: 500,                    // Max 500 cached entries
  ttl: 60_000,                 // 1 minute TTL
  updateAgeOnGet: true,        // Extend TTL on access
  updateAgeOnHas: false,
});

async function getCachedBoard(boardId: string): Promise<MiroBoard> {
  const cacheKey = `board:${boardId}`;
  const cached = boardCache.get(cacheKey);
  if (cached) return cached as MiroBoard;

  const board = await miroFetch(`/v2/boards/${boardId}`);
  boardCache.set(cacheKey, board);
  return board;
}

// Invalidate on webhook events
function onBoardEvent(event: MiroBoardEvent) {
  boardCache.delete(`board:${event.boardId}`);
  boardCache.delete(`items:${event.boardId}`);
}
```

### Redis Cache (Distributed)

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function getCachedItems(boardId: string): Promise<MiroBoardItem[]> {
  const key = `miro:items:${boardId}`;
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  // Fetch all items
  const items: MiroBoardItem[] = [];
  for await (const item of paginateItems(boardId)) {
    items.push(item);
  }

  // Cache for 2 minutes (boards with active editing should use shorter TTL)
  await redis.setex(key, 120, JSON.stringify(items));
  return items;
}

// Webhook-driven cache invalidation
async function invalidateOnEvent(event: MiroBoardEvent) {
  const keys = [
    `miro:items:${event.boardId}`,
    `miro:board:${event.boardId}`,
  ];
  await redis.del(...keys);
}
```

## Controlled Concurrency for Bulk Operations

```typescript
import PQueue from 'p-queue';

// Create items in parallel with controlled concurrency
async function bulkCreateStickyNotes(
  boardId: string,
  notes: Array<{ content: string; color: string; x: number; y: number }>
): Promise<string[]> {
  const queue = new PQueue({
    concurrency: 5,       // Max 5 parallel requests
    interval: 1000,       // Per-second window
    intervalCap: 10,      // Max 10 requests per second
  });

  const ids: string[] = [];

  for (const note of notes) {
    queue.add(async () => {
      const result = await miroFetch(`/v2/boards/${boardId}/sticky_notes`, 'POST', {
        data: { content: note.content, shape: 'square' },
        style: { fillColor: note.color },
        position: { x: note.x, y: note.y },
      });
      ids.push(result.id);
    });
  }

  await queue.onIdle();  // Wait for all to complete
  return ids;
}

// Example: Create a grid of 50 sticky notes efficiently
const notes = Array.from({ length: 50 }, (_, i) => ({
  content: `Note ${i + 1}`,
  color: 'light_yellow',
  x: (i % 10) * 250,
  y: Math.floor(i / 10) * 250,
}));

const createdIds = await bulkCreateStickyNotes(boardId, notes);
console.log(`Created ${createdIds.length} sticky notes`);
```

## Connection Pooling

```typescript
import { Agent } from 'https';

// Reuse TCP connections across requests
const httpsAgent = new Agent({
  keepAlive: true,
  maxSockets: 10,        // Max 10 concurrent connections to api.miro.com
  maxFreeSockets: 5,     // Keep 5 idle connections in pool
  timeout: 30000,        // Socket timeout
});

async function miroFetchPooled(path: string, options: RequestInit = {}) {
  // Note: Node.js native fetch doesn't support custom agents directly.
  // Use undici or node-fetch for connection pooling.
  const { default: fetch } = await import('node-fetch');

  return fetch(`https://api.miro.com${path}`, {
    ...options,
    agent: httpsAgent,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
}
```

## Performance Monitoring

```typescript
async function instrumentedMiroFetch<T>(
  operation: string,
  path: string,
  method = 'GET',
  body?: unknown,
): Promise<{ data: T; metrics: RequestMetrics }> {
  const start = performance.now();
  const response = await fetch(`https://api.miro.com${path}`, {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });

  const duration = performance.now() - start;
  const metrics: RequestMetrics = {
    operation,
    path,
    method,
    status: response.status,
    durationMs: Math.round(duration),
    rateLimitRemaining: parseInt(response.headers.get('X-RateLimit-Remaining') ?? '0', 10),
    rateLimitReset: response.headers.get('X-RateLimit-Reset') ?? '',
  };

  // Log for dashboarding
  console.log('[MIRO_PERF]', JSON.stringify(metrics));

  const data = response.status !== 204 ? await response.json() : null;
  return { data: data as T, metrics };
}
```

## Optimization Checklist

| Technique | Impact | Effort | When to Use |
|-----------|--------|--------|-------------|
| Type-filtered queries | High | Low | Always — `?type=sticky_note` reduces payload |
| LRU cache | High | Low | Read-heavy workloads |
| Redis cache + webhook invalidation | Very High | Medium | Multi-instance deployments |
| Controlled concurrency | High | Low | Bulk create/update operations |
| Connection pooling | Medium | Low | High request volume |
| Cursor pagination | High | Low | Always — avoid loading full board |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cache stale data | Long TTL + frequent edits | Shorten TTL or use webhook invalidation |
| Concurrency errors | Too many parallel requests | Reduce `concurrency` in PQueue |
| Connection pool exhausted | Max sockets too low | Increase `maxSockets` |
| Pagination cursor expired | Long gap between pages | Re-start pagination from beginning |

## Resources

- [Get Items on Board](https://developers.miro.com/reference/get-items)
- [Rate Limiting](https://developers.miro.com/reference/rate-limiting)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For cost optimization, see `miro-cost-tuning`.
