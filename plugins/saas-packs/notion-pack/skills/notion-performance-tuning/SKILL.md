---
name: notion-performance-tuning
description: |
  Optimize Notion API performance with caching, batching, parallel requests, and incremental sync.
  Use when experiencing slow API responses, implementing caching strategies,
  reducing API call volume, or tuning request patterns for Notion integrations.
  Trigger with phrases like "notion performance", "optimize notion api",
  "notion latency", "notion caching", "notion slow", "notion batch requests",
  "notion incremental sync", "notion reduce api calls".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Performance Tuning

## Overview
Optimize Notion API performance by minimizing API calls, caching responses with TTL-based invalidation, batching block appends, parallelizing requests within rate limits, selecting only needed properties, and implementing incremental sync patterns. Target latency benchmarks: Database Query p50=150ms, Page Create p50=200ms, Search p50=300ms.

## Prerequisites
- `@notionhq/client` installed (`npm install @notionhq/client`)
- `p-queue` for rate-limited parallelism (`npm install p-queue`)
- `lru-cache` for TTL-based caching (`npm install lru-cache`)
- Understanding of your access patterns (read-heavy vs write-heavy)
- Optional: Redis or `ioredis` for distributed caching across instances

## Instructions

### Step 1: Minimize API Calls and Reduce Payload

Avoid N+1 query patterns. Use `page_size: 100` (the maximum) to reduce pagination requests. Select only the properties you need in database queries to shrink response payloads.

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// BAD: N+1 pattern — fetching content for every page individually
async function fetchAllBad(dbId: string) {
  const pages = await notion.databases.query({ database_id: dbId });
  for (const page of pages.results) {
    // Each iteration is a separate API call — O(n) requests
    const content = await notion.blocks.children.list({ block_id: page.id });
  }
}

// GOOD: Use filter_properties to select only needed fields
async function fetchAllGood(dbId: string) {
  const pages = await notion.databases.query({
    database_id: dbId,
    page_size: 100, // Maximum — reduces total pagination requests
    filter: {
      property: 'Status',
      select: { equals: 'Active' },
    },
    // Select only the properties you need by property ID
    // Find IDs via: notion.databases.retrieve({ database_id: dbId })
    filter_properties: ['title', 'Status', 'Priority'],
  });

  // Properties are already in the response — no extra retrieve calls
  for (const page of pages.results) {
    if ('properties' in page) {
      const title = page.properties.Name?.type === 'title'
        ? page.properties.Name.title.map(t => t.plain_text).join('')
        : '';
      const status = page.properties.Status?.type === 'select'
        ? page.properties.Status.select?.name
        : undefined;
      // Use properties directly — zero additional API calls
    }
  }
  return pages;
}

// Batch block appends — up to 100 blocks per request
async function appendBlocks(pageId: string, items: string[]) {
  const blocks = items.map(item => ({
    object: 'block' as const,
    type: 'paragraph' as const,
    paragraph: {
      rich_text: [{ type: 'text' as const, text: { content: item } }],
    },
  }));

  // BAD: one call per block = N API calls
  // for (const block of blocks) {
  //   await notion.blocks.children.append({ block_id: pageId, children: [block] });
  // }

  // GOOD: batch in chunks of 100 (API maximum)
  for (let i = 0; i < blocks.length; i += 100) {
    await notion.blocks.children.append({
      block_id: pageId,
      children: blocks.slice(i, i + 100),
    });
  }
}

// Avoid recursive block fetching unless you actually need nested content
async function getTopLevelBlocks(pageId: string) {
  const blocks = await notion.blocks.children.list({
    block_id: pageId,
    page_size: 100,
  });
  // Only recurse into blocks that have children AND you need them
  const expandable = blocks.results.filter(
    (b) => 'has_children' in b && b.has_children && needsExpansion(b)
  );
  // Fetch children only for blocks that matter
  return { topLevel: blocks.results, expandable };
}

function needsExpansion(block: any): boolean {
  // Only expand toggles and nested content — skip paragraphs, headings, etc.
  return ['toggle', 'child_page', 'child_database', 'column_list'].includes(block.type);
}
```

### Step 2: Cache Responses with TTL-Based Invalidation

Implement in-memory caching with LRU eviction and TTL expiration. Invalidate cache entries on writes to maintain consistency.

```typescript
import { LRUCache } from 'lru-cache';
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Tiered TTL cache — different durations for different data volatility
const cache = new LRUCache<string, any>({
  max: 1000,             // max entries
  ttl: 60_000,           // default 1-minute TTL
  updateAgeOnGet: false, // don't extend TTL on reads (ensures freshness)
  allowStale: false,     // never return expired entries
});

// Cache configuration per operation type
const TTL = {
  DATABASE_SCHEMA: 300_000,  // 5 min — schemas rarely change
  DATABASE_QUERY:  60_000,   // 1 min — data changes frequently
  PAGE_RETRIEVE:   120_000,  // 2 min — pages change occasionally
  SEARCH:          30_000,   // 30s — search results are volatile
  BLOCK_CHILDREN:  60_000,   // 1 min — content updates moderately
} as const;

async function cachedDatabaseQuery(dbId: string, filter?: any, sorts?: any) {
  const cacheKey = `db:${dbId}:${JSON.stringify({ filter, sorts })}`;
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  const allPages: any[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: dbId,
      filter,
      sorts,
      page_size: 100,
      start_cursor: cursor,
    });
    allPages.push(...response.results);
    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);

  const result = { results: allPages, count: allPages.length };
  cache.set(cacheKey, result, { ttl: TTL.DATABASE_QUERY });
  return result;
}

async function cachedPageRetrieve(pageId: string) {
  const cacheKey = `page:${pageId}`;
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  const page = await notion.pages.retrieve({ page_id: pageId });
  cache.set(cacheKey, page, { ttl: TTL.PAGE_RETRIEVE });
  return page;
}

// Invalidate on writes — consistency over speed
async function createPageInvalidating(dbId: string, properties: any) {
  const page = await notion.pages.create({
    parent: { database_id: dbId },
    properties,
  });

  // Invalidate all cached queries for this database
  for (const key of cache.keys()) {
    if (key.startsWith(`db:${dbId}:`)) cache.delete(key);
  }

  return page;
}

async function updatePageInvalidating(pageId: string, properties: any) {
  const page = await notion.pages.update({ page_id: pageId, properties });

  // Invalidate specific page cache and parent database queries
  cache.delete(`page:${pageId}`);
  // If you know the parent DB, invalidate its queries too:
  // for (const key of cache.keys()) {
  //   if (key.startsWith(`db:${parentDbId}:`)) cache.delete(key);
  // }

  return page;
}

// Cache stats for monitoring
function getCacheStats() {
  return {
    size: cache.size,
    maxSize: cache.max,
    hitRate: cache.size > 0 ? 'check cache.get return values' : 'empty',
  };
}
```

### Step 3: Parallel Requests with Rate-Limited Queue and Latency Monitoring

Use `p-queue` to parallelize requests within Notion's 3 req/sec rate limit. Implement latency tracking to monitor performance against target benchmarks.

```typescript
import PQueue from 'p-queue';
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Rate-limited queue: 3 concurrent requests, 3 per second
const queue = new PQueue({
  concurrency: 3,
  interval: 1000,
  intervalCap: 3,
  carryoverConcurrencyCount: true,
});

// Latency tracking
interface LatencyMetrics {
  operation: string;
  count: number;
  totalMs: number;
  minMs: number;
  maxMs: number;
  samples: number[];
}

const metrics = new Map<string, LatencyMetrics>();

async function trackedCall<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  const start = performance.now();
  try {
    const result = await queue.add(fn, { throwOnTimeout: true });
    return result as T;
  } finally {
    const elapsed = performance.now() - start;
    const existing = metrics.get(operation) ?? {
      operation,
      count: 0,
      totalMs: 0,
      minMs: Infinity,
      maxMs: 0,
      samples: [],
    };
    existing.count++;
    existing.totalMs += elapsed;
    existing.minMs = Math.min(existing.minMs, elapsed);
    existing.maxMs = Math.max(existing.maxMs, elapsed);
    existing.samples.push(elapsed);
    metrics.set(operation, existing);
  }
}

// Target latency benchmarks (p50 values in milliseconds)
const LATENCY_TARGETS = {
  'database.query': 150,
  'pages.create':   200,
  'search':         300,
  'pages.retrieve': 100,
  'blocks.children.list': 120,
  'blocks.children.append': 180,
} as const;

function getPercentile(samples: number[], pct: number): number {
  const sorted = [...samples].sort((a, b) => a - b);
  const idx = Math.ceil(sorted.length * (pct / 100)) - 1;
  return sorted[Math.max(0, idx)];
}

function reportLatency() {
  console.log('\n--- Notion API Latency Report ---');
  for (const [op, m] of metrics) {
    const p50 = getPercentile(m.samples, 50);
    const p95 = getPercentile(m.samples, 95);
    const avg = m.totalMs / m.count;
    const target = LATENCY_TARGETS[op as keyof typeof LATENCY_TARGETS];
    const status = target && p50 <= target ? 'OK' : 'SLOW';
    console.log(
      `${op}: p50=${p50.toFixed(0)}ms p95=${p95.toFixed(0)}ms avg=${avg.toFixed(0)}ms ` +
      `(${m.count} calls) ${target ? `[target: ${target}ms → ${status}]` : ''}`
    );
  }
}

// Parallelized multi-page retrieval with rate limiting
async function getMultiplePages(pageIds: string[]) {
  return Promise.all(
    pageIds.map(id =>
      trackedCall('pages.retrieve', () =>
        notion.pages.retrieve({ page_id: id })
      )
    )
  );
}

// Parallelized database queries across multiple databases
async function queryMultipleDatabases(dbIds: string[], filter?: any) {
  return Promise.all(
    dbIds.map(dbId =>
      trackedCall('database.query', () =>
        notion.databases.query({
          database_id: dbId,
          filter,
          page_size: 100,
        })
      )
    )
  );
}

// Pre-fetch and warm cache for known pages
async function prefetchPages(pageIds: string[]) {
  console.log(`Pre-fetching ${pageIds.length} pages...`);
  const pages = await getMultiplePages(pageIds);
  // Pages are now in the rate-limited queue's pipeline
  // Combine with caching (Step 2) for full benefit
  return pages;
}

// Incremental sync — only fetch pages modified since last sync
async function incrementalSync(
  dbId: string,
  lastSyncTime: string // ISO 8601 timestamp
) {
  const changedPages = await trackedCall('database.query', () =>
    notion.databases.query({
      database_id: dbId,
      filter: {
        timestamp: 'last_edited_time',
        last_edited_time: { after: lastSyncTime },
      },
      sorts: [{ timestamp: 'last_edited_time', direction: 'descending' }],
      page_size: 100,
    })
  );

  console.log(
    `Incremental sync: ${changedPages.results.length} pages changed since ${lastSyncTime}`
  );

  // Only fetch block content for pages that actually changed
  const contentUpdates = await Promise.all(
    changedPages.results.map(page =>
      trackedCall('blocks.children.list', () =>
        notion.blocks.children.list({
          block_id: page.id,
          page_size: 100,
        })
      )
    )
  );

  return {
    pages: changedPages.results,
    content: contentUpdates,
    syncTimestamp: new Date().toISOString(),
  };
}

// Memory-efficient streaming with rate limiting
async function* streamPagesThrottled(dbId: string, filter?: any) {
  let cursor: string | undefined;
  do {
    const response = await trackedCall('database.query', () =>
      notion.databases.query({
        database_id: dbId,
        filter,
        page_size: 100,
        start_cursor: cursor,
      })
    );
    for (const page of response.results) {
      yield page;
    }
    cursor = response.has_more ? response.next_cursor ?? undefined : undefined;
  } while (cursor);
}

// Monitor queue health
queue.on('active', () => {
  if (queue.size > 10) {
    console.warn(`Notion queue backing up: ${queue.size} pending, ${queue.pending} active`);
  }
});
```

## Output
- Reduced API call count through property selection, filtering, and batched block appends
- TTL-based caching with write-through invalidation for data consistency
- Parallel requests within Notion's 3 req/sec rate limit using `p-queue`
- Incremental sync fetching only changed pages since last sync timestamp
- Latency monitoring with p50/p95 tracking against target benchmarks
- Memory-efficient streaming for large datasets via async generators

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Stale cache data | TTL too long for volatile data | Use shorter TTL (30s for search, 60s for queries) |
| Rate limit despite queue | Other code paths making unqueued calls | Use a single shared `p-queue` instance across your app |
| Memory pressure from cache | Too many entries or large payloads | Set `max` on LRU cache; use `filter_properties` to shrink payloads |
| Pagination never ends | Circular cursor or API bug | Add max-iteration guard (`if (requestCount > 50) break`) |
| Incremental sync misses | Clock skew between client and API | Subtract a 5-second buffer from `lastSyncTime` |
| p50 latency above target | Cold cache or large responses | Pre-fetch critical pages; use `filter_properties` to reduce response size |

## Examples

### Full Performance-Tuned Client
```typescript
import { Client } from '@notionhq/client';
import { LRUCache } from 'lru-cache';
import PQueue from 'p-queue';

// Production-ready Notion client with caching + rate limiting
class NotionPerf {
  private client: Client;
  private cache: LRUCache<string, any>;
  private queue: PQueue;
  private lastSync: string;

  constructor(token: string) {
    this.client = new Client({ auth: token });
    this.cache = new LRUCache({ max: 500, ttl: 60_000 });
    this.queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });
    this.lastSync = new Date(0).toISOString();
  }

  async query(dbId: string, filter?: any) {
    const key = `q:${dbId}:${JSON.stringify(filter ?? {})}`;
    const hit = this.cache.get(key);
    if (hit) return hit;

    const result = await this.queue.add(() =>
      this.client.databases.query({ database_id: dbId, filter, page_size: 100 })
    );
    this.cache.set(key, result);
    return result;
  }

  async sync(dbId: string) {
    const changed = await this.queue.add(() =>
      this.client.databases.query({
        database_id: dbId,
        filter: {
          timestamp: 'last_edited_time',
          last_edited_time: { after: this.lastSync },
        },
        page_size: 100,
      })
    );
    this.lastSync = new Date().toISOString();
    // Invalidate affected cache entries
    for (const key of this.cache.keys()) {
      if (key.startsWith(`q:${dbId}:`)) this.cache.delete(key);
    }
    return changed;
  }
}

const perf = new NotionPerf(process.env.NOTION_TOKEN!);
const results = await perf.query('db-id-here');
const updates = await perf.sync('db-id-here');
```

### Latency Comparison Before/After
```typescript
// Measure improvement from caching + batching
async function benchmark(dbId: string, pageId: string) {
  const t = (label: string, fn: () => Promise<any>) =>
    trackedCall(label, fn);

  // Cold calls (no cache)
  await t('database.query', () =>
    notion.databases.query({ database_id: dbId, page_size: 100 })
  );

  // Warm calls (cached)
  await t('database.query', () => cachedDatabaseQuery(dbId));

  // Batch append vs individual
  const items = Array.from({ length: 50 }, (_, i) => `Item ${i}`);
  await t('blocks.children.append', () => appendBlocks(pageId, items));

  reportLatency();
}
```

## Resources
- [Query a Database](https://developers.notion.com/reference/post-database-query) — filtering, sorting, pagination
- [Append Block Children](https://developers.notion.com/reference/patch-block-children) — batch up to 100 blocks
- [Request Limits](https://developers.notion.com/reference/request-limits) — 3 req/sec per integration
- [Notion SDK (notion-sdk-js)](https://github.com/makenotion/notion-sdk-js) — `@notionhq/client` source
- [p-queue](https://github.com/sindresorhus/p-queue) — promise-based rate-limited queue
- [LRU Cache](https://github.com/isaacs/node-lru-cache) — TTL-based in-memory cache

## Next Steps
For webhook event handling, see `notion-webhooks-events`.
