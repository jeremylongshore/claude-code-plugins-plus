---
name: notion-performance-tuning
description: |
  Optimize Notion API performance with caching, parallel fetching, and pagination.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request patterns for Notion integrations.
  Trigger with phrases like "notion performance", "optimize notion",
  "notion latency", "notion caching", "notion slow", "notion batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Performance Tuning

## Overview
Optimize Notion API performance by reducing API calls, caching responses, batching operations, and using efficient pagination patterns.

## Prerequisites
- `@notionhq/client` installed
- Understanding of your access patterns (read-heavy vs write-heavy)
- Optional: Redis for distributed caching

## Instructions

### Step 1: Minimize API Calls

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// BAD: N+1 query pattern — separate call for each page's content
const pages = await notion.databases.query({ database_id: dbId });
for (const page of pages.results) {
  const content = await notion.blocks.children.list({ block_id: page.id }); // N calls!
}

// GOOD: Only fetch content when needed, use property values from query
const pages = await notion.databases.query({
  database_id: dbId,
  filter: { property: 'Status', select: { equals: 'Active' } },
});
// Page properties are already in the query result — no extra calls needed
for (const page of pages.results) {
  if ('properties' in page) {
    const title = page.properties.Name?.type === 'title'
      ? page.properties.Name.title.map(t => t.plain_text).join('')
      : '';
    // Use title directly — no separate retrieve call needed
  }
}
```

### Step 2: Response Caching
```typescript
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, any>({
  max: 500,            // max entries
  ttl: 60_000,         // 1 minute TTL
  updateAgeOnGet: true,
});

async function cachedQuery(dbId: string, filter?: any) {
  const cacheKey = `db:${dbId}:${JSON.stringify(filter ?? {})}`;
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  const result = await notion.databases.query({
    database_id: dbId,
    filter,
    page_size: 100,
  });
  cache.set(cacheKey, result);
  return result;
}

// Invalidate on writes
async function createPageAndInvalidate(dbId: string, properties: any) {
  const page = await notion.pages.create({
    parent: { database_id: dbId },
    properties,
  });
  // Invalidate all queries for this database
  for (const key of cache.keys()) {
    if (key.startsWith(`db:${dbId}:`)) cache.delete(key);
  }
  return page;
}
```

### Step 3: Efficient Pagination
```typescript
// Fetch all pages with maximum page_size (100) to minimize requests
async function getAllPages(dbId: string, filter?: any) {
  const allPages: any[] = [];
  let cursor: string | undefined;
  let requestCount = 0;

  do {
    const response = await notion.databases.query({
      database_id: dbId,
      filter,
      page_size: 100, // Maximum — reduces total requests
      start_cursor: cursor,
    });
    allPages.push(...response.results);
    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
    requestCount++;
  } while (cursor);

  console.log(`Fetched ${allPages.length} pages in ${requestCount} requests`);
  return allPages;
}

// Async generator for memory-efficient streaming
async function* streamPages(dbId: string, filter?: any) {
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: dbId,
      filter,
      page_size: 100,
      start_cursor: cursor,
    });

    for (const page of response.results) {
      yield page;
    }

    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);
}

// Usage — process without loading everything into memory
for await (const page of streamPages(dbId)) {
  await processPage(page);
}
```

### Step 4: Parallel Fetches (Within Rate Limits)
```typescript
import PQueue from 'p-queue';

const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });

// Fetch multiple pages in parallel while respecting rate limits
async function getMultiplePages(pageIds: string[]) {
  return Promise.all(
    pageIds.map(id =>
      queue.add(() => notion.pages.retrieve({ page_id: id }))
    )
  );
}

// Fetch blocks for multiple pages in parallel
async function getMultiplePagesContent(pageIds: string[]) {
  return Promise.all(
    pageIds.map(id =>
      queue.add(() => notion.blocks.children.list({ block_id: id }))
    )
  );
}
```

### Step 5: Block Append Optimization
```typescript
// BAD: One block at a time
for (const item of items) {
  await notion.blocks.children.append({
    block_id: pageId,
    children: [{ paragraph: { rich_text: [{ text: { content: item } }] } }],
  });
}

// GOOD: Batch blocks in a single call (up to 100 blocks per request)
const blocks = items.map(item => ({
  paragraph: { rich_text: [{ text: { content: item } }] },
}));

// Chunk into batches of 100 (API limit)
for (let i = 0; i < blocks.length; i += 100) {
  await notion.blocks.children.append({
    block_id: pageId,
    children: blocks.slice(i, i + 100),
  });
}
```

### Step 6: Connection Keep-Alive
```typescript
import { Agent } from 'https';

// Reuse TCP connections
const agent = new Agent({
  keepAlive: true,
  maxSockets: 10,
  maxFreeSockets: 5,
});

const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  // The SDK uses node-fetch internally; this reduces connection overhead
});

// Using a singleton client (see notion-sdk-patterns) already handles this
```

## Output
- Reduced API call count through caching and batching
- Efficient pagination with max page_size
- Parallel fetches within rate limits
- Streaming for large datasets

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Stale cache data | Long TTL | Reduce TTL or invalidate on writes |
| Rate limit despite queue | Burst from other code | Use single shared queue |
| Memory pressure | Caching too much | Set `max` on LRU cache |
| Pagination loops | `has_more` always true | Set a max iteration guard |

## Examples

### Performance Measurement
```typescript
async function measuredCall<T>(label: string, fn: () => Promise<T>): Promise<T> {
  const start = performance.now();
  const result = await fn();
  console.log(`${label}: ${(performance.now() - start).toFixed(0)}ms`);
  return result;
}

// Compare cached vs uncached
await measuredCall('uncached', () => notion.databases.query({ database_id: dbId }));
await measuredCall('cached', () => cachedQuery(dbId));
```

## Resources
- [Query a Database](https://developers.notion.com/reference/post-database-query)
- [Append Block Children](https://developers.notion.com/reference/patch-block-children)
- [Request Limits](https://developers.notion.com/reference/request-limits)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)

## Next Steps
For cost optimization, see `notion-cost-tuning`.
