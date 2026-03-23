---
name: notion-cost-tuning
description: |
  Optimize Notion API usage to minimize rate-limit pressure, reduce engineering
  overhead, and maximize throughput. Use when auditing request volume, eliminating
  redundant API calls, implementing caching, or restructuring queries for efficiency.
  Trigger with "notion cost", "notion optimize", "notion API usage", "reduce notion
  requests", "notion rate limit budget", "notion efficient", "notion caching".
allowed-tools: Read, Write, Edit, Bash(npm:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion, optimization, caching, cost]
compatible-with: claude-code
---

# Notion Cost Tuning

## Overview

The Notion API is **free with every workspace plan** — there is no per-call pricing. The real "cost" is the **3 requests/second rate limit** (per integration token) and engineering time wasted on inefficient patterns. Apply six strategies below to reduce request volume by 80-95%.

**Notion workspace pricing (for context — API access is included at every tier):**

| Plan | Price | API Access | Rate Limit |
|------|-------|------------|------------|
| Free | $0 | Full API | 3 req/sec |
| Plus | $12/user/mo | Full API | 3 req/sec |
| Business | $28/user/mo | Full API | 3 req/sec |
| Enterprise | Custom | Full API | 3 req/sec |

The rate limit is identical across all plans. Optimization is about staying within 3 req/sec, not reducing a bill.

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- Integration token from [notion.so/my-integrations](https://www.notion.so/my-integrations)
- Token shared with target pages/databases via the **Connections** menu in Notion
- For queue patterns: `p-queue` v8+ (`npm install p-queue`)
- For caching: `node-cache` or `lru-cache` (`npm install lru-cache`)

## Instructions

### Step 1: Audit Current Request Volume

Before optimizing, measure your baseline. Instrument the Notion client to track every API call by method, endpoint, and timestamp.

```typescript
import { Client } from '@notionhq/client';

interface RequestEntry {
  method: string;
  endpoint: string;
  timestamp: number;
  durationMs: number;
}

const requestLog: RequestEntry[] = [];
const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Wrap any Notion call with tracking
async function tracked<T>(
  method: string,
  endpoint: string,
  fn: () => Promise<T>,
): Promise<T> {
  const start = Date.now();
  try {
    return await fn();
  } finally {
    requestLog.push({
      method,
      endpoint,
      timestamp: start,
      durationMs: Date.now() - start,
    });
  }
}

// Generate audit report
function auditReport() {
  const last60s = requestLog.filter(r => r.timestamp > Date.now() - 60_000);
  const byMethod = Object.groupBy(last60s, r => r.method);

  console.table({
    totalAllTime: requestLog.length,
    lastMinute: last60s.length,
    reqPerSecond: (last60s.length / 60).toFixed(2),
    avgLatencyMs: (
      last60s.reduce((sum, r) => sum + r.durationMs, 0) / last60s.length
    ).toFixed(0),
  });

  // Show hotspots — which methods consume the most budget
  for (const [method, entries] of Object.entries(byMethod)) {
    console.log(`  ${method}: ${entries!.length} calls (${((entries!.length / last60s.length) * 100).toFixed(0)}%)`);
  }
}

// Example: track a database query
const results = await tracked('databases.query', `/databases/${dbId}/query`, () =>
  notion.databases.query({ database_id: dbId }),
);

// Run report every 60 seconds
setInterval(auditReport, 60_000);
```

**Target:** identify which operations consume > 50% of your request budget. Common culprits are polling loops, page retrieves that duplicate database query data, and unfiltered full-table scans.

### Step 2: Eliminate Redundant Reads and Reduce Payload Size

Three high-impact patterns to cut reads immediately:

**Pattern A: Stop retrieving pages you already have from database queries.** Database query results include all properties — a separate `pages.retrieve` is redundant unless you need blocks.

```typescript
// WASTEFUL: 2 requests per page (query + retrieve)
const { results } = await notion.databases.query({ database_id: dbId });
for (const page of results) {
  const full = await notion.pages.retrieve({ page_id: page.id }); // redundant!
  processPage(full);
}

// EFFICIENT: 1 request total — properties are already in query results
const { results } = await notion.databases.query({ database_id: dbId });
for (const page of results) {
  processPage(page); // same properties, no extra request
}
```

**Pattern B: Use `filter_properties` to reduce response size.** When you only need specific properties, pass their IDs to shrink the payload by 60-90%.

```typescript
// First, discover property IDs (one-time setup)
const db = await notion.databases.retrieve({ database_id: dbId });
console.log(
  Object.entries(db.properties).map(([name, prop]) => `${name}: ${prop.id}`),
);
// Output: ["Status: abc1", "Assignee: def2", "Due Date: ghi3", ...]

// Then query with only the properties you need
const { results } = await notion.databases.query({
  database_id: dbId,
  filter_properties: ['abc1', 'def2'], // Only Status and Assignee
});
// Response is 60-90% smaller — faster network, faster parsing
```

**Pattern C: Use `last_edited_time` to fetch only changes since last sync.**

```typescript
async function getChangesSince(dbId: string, sinceISO: string) {
  return notion.databases.query({
    database_id: dbId,
    filter: {
      timestamp: 'last_edited_time',
      last_edited_time: { after: sinceISO },
    },
    sorts: [{ timestamp: 'last_edited_time', direction: 'descending' }],
    page_size: 100,
  });
}

// Incremental sync: only fetch what changed
let lastSync = new Date().toISOString();

async function syncLoop() {
  const changes = await getChangesSince(dbId, lastSync);
  if (changes.results.length > 0) {
    console.log(`${changes.results.length} pages modified since ${lastSync}`);
    await processChanges(changes.results);
    lastSync = new Date().toISOString();
  }
}
// 1-5 requests/minute instead of re-fetching entire database each time
```

### Step 3: Cache, Batch, and Replace Polling

**Caching:** Most Notion data is read-heavy. Cache database query results and page content with TTL-based invalidation.

```typescript
import { LRUCache } from 'lru-cache';

const pageCache = new LRUCache<string, any>({
  max: 500,
  ttl: 5 * 60 * 1000, // 5-minute TTL
});

async function getCachedPage(pageId: string) {
  const cached = pageCache.get(pageId);
  if (cached) return cached; // 0 API requests

  const page = await notion.pages.retrieve({ page_id: pageId });
  pageCache.set(pageId, page);
  return page;
}

// Cache database queries by filter hash
const queryCache = new LRUCache<string, any>({
  max: 100,
  ttl: 2 * 60 * 1000, // 2-minute TTL for queries
});

async function cachedQuery(dbId: string, filter: any) {
  const key = `${dbId}:${JSON.stringify(filter)}`;
  const cached = queryCache.get(key);
  if (cached) return cached;

  const result = await notion.databases.query({
    database_id: dbId,
    filter,
    page_size: 100,
  });
  queryCache.set(key, result);
  return result;
}
```

**Batching writes:** The Notion API has no true batch endpoint, but `blocks.children.append` accepts up to 100 blocks per call.

```typescript
import PQueue from 'p-queue';

// Rate-limited queue: respects 3 req/sec
const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });

// BAD: 100 page creates = 100 sequential requests (~34 seconds at 3/sec)
for (const item of items) {
  await notion.pages.create({
    parent: { database_id: dbId },
    properties: toProperties(item),
  });
}

// BETTER: 100 page creates via queue = 100 requests but 3x faster (~34 sec → 34 sec but concurrent)
await Promise.all(
  items.map(item =>
    queue.add(() =>
      notion.pages.create({
        parent: { database_id: dbId },
        properties: toProperties(item),
      }),
    ),
  ),
);

// BEST for content: batch blocks into single append calls (100 blocks = 1 request)
const blocks = items.map(item => ({
  type: 'paragraph' as const,
  paragraph: {
    rich_text: [{ type: 'text' as const, text: { content: item.text } }],
  },
}));

// Chunk into groups of 100 (API limit per call)
for (let i = 0; i < blocks.length; i += 100) {
  await queue.add(() =>
    notion.blocks.children.append({
      block_id: parentPageId,
      children: blocks.slice(i, i + 100),
    }),
  );
}
```

**Replace polling with webhooks:** Polling a single database every 10 seconds costs 360 requests/hour (3600s / 10s interval). Webhooks cost zero.

```typescript
import express from 'express';

// POLLING (wasteful): 360 requests/hour per database (3600s / 10s = 360)
setInterval(async () => {
  const pages = await notion.databases.query({ database_id: dbId });
  await processPages(pages.results);
}, 10_000);

// WEBHOOK (efficient): 0 polling requests, fetch only on change
const app = express();
app.post('/webhooks/notion', express.json(), async (req, res) => {
  // Acknowledge immediately (Notion expects 200 within 3 seconds)
  res.status(200).json({ ok: true });

  const { type, data } = req.body;
  if (type === 'page.properties_updated' || type === 'page.content_updated') {
    // Invalidate cache, then fetch only the changed page
    pageCache.delete(data.id);
    const page = await notion.pages.retrieve({ page_id: data.id });
    await processPage(page);
  }
});
```

## Output

After applying these optimizations:

- **Audit report** showing request volume baseline and hotspots
- **Redundant reads eliminated** — no duplicate `pages.retrieve` after `databases.query`
- **Payload sizes reduced** 60-90% via `filter_properties`
- **Incremental sync** via `last_edited_time` filter replacing full-table scans
- **Cache layer** with TTL-based invalidation for reads
- **Write throughput maximized** via queue-based throttling and block batching
- **Polling eliminated** where webhooks are available (360 req/hr per database saved)

**Typical impact:** integrations drop from 500+ requests/hour to under 200 requests/hour (80-95% reduction), staying well within the 3 req/sec limit even with multiple databases.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 429 Too Many Requests despite optimization | Shared token across multiple services | Use separate integration tokens per service; each gets its own 3 req/sec budget |
| Stale cached data causing bugs | Cache TTL too long for the use case | Shorten TTL to 30-60s for volatile data, or use webhook-based cache invalidation |
| Webhook not triggering | Integration not connected to the page/database | Share via **Connections** menu in Notion; verify webhook URL is publicly accessible |
| `filter_properties` returning empty results | Using property names instead of IDs | Run `databases.retrieve` to get property IDs (short strings like `abc1`), not display names |
| Incremental sync missing updates | Clock skew between client and Notion server | Subtract 5-second buffer from `lastSync` timestamp to create overlap window |
| `blocks.children.append` failing with 400 | More than 100 children in single call | Chunk arrays into groups of 100 before appending |

## Examples

### Request Reduction Calculator

Estimate savings before implementing changes:

```typescript
function estimateRequestSavings(config: {
  databases: number;
  avgPagesPerDb: number;
  pollIntervalSeconds: number;
  hoursPerDay: number;
  retrievePerPage: number; // extra retrieve calls per page (0 = none)
}) {
  const pollsPerHour = 3600 / config.pollIntervalSeconds;
  const paginationCalls = Math.ceil(config.avgPagesPerDb / 100);

  // Before: polling + pagination + redundant retrieves
  const beforePerHour =
    config.databases * pollsPerHour * paginationCalls +
    config.databases * pollsPerHour * config.avgPagesPerDb * config.retrievePerPage;

  // After: webhook-driven (0 polling) + no redundant retrieves
  // Estimate ~5% of pages change per hour, triggering on-demand reads
  const changedPagesPerHour = config.databases * config.avgPagesPerDb * 0.05;
  const afterPerHour = changedPagesPerHour; // 1 request per changed page

  const dailySavings = (beforePerHour - afterPerHour) * config.hoursPerDay;

  console.log(`=== Request Budget Analysis ===`);
  console.log(`Before: ${beforePerHour.toFixed(0)} requests/hour`);
  console.log(`After:  ${afterPerHour.toFixed(0)} requests/hour`);
  console.log(`Savings: ${dailySavings.toFixed(0)} requests/day (${((1 - afterPerHour / beforePerHour) * 100).toFixed(0)}% reduction)`);
  console.log(`Rate limit headroom: ${((3 * 3600 - afterPerHour) / (3 * 3600) * 100).toFixed(0)}% of 3 req/sec budget unused`);
}

// Example: 5 databases, 200 pages each, polling every 30 seconds, 12 hours/day
estimateRequestSavings({
  databases: 5,
  avgPagesPerDb: 200,
  pollIntervalSeconds: 30,
  hoursPerDay: 12,
  retrievePerPage: 1,
});
// Before: 121,200 requests/hour
// After:  50 requests/hour
// Savings: 1,453,800 requests/day (99% reduction)
```

### Full Optimization Wrapper

Drop-in wrapper that adds caching, tracking, and queue management to the Notion client:

```typescript
import { Client } from '@notionhq/client';
import { LRUCache } from 'lru-cache';
import PQueue from 'p-queue';

export function createOptimizedClient(token: string) {
  const notion = new Client({ auth: token });
  const cache = new LRUCache<string, any>({ max: 1000, ttl: 5 * 60 * 1000 });
  const writeQueue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });
  let requestCount = 0;

  return {
    // Cached page retrieve
    async getPage(pageId: string) {
      const cached = cache.get(`page:${pageId}`);
      if (cached) return cached;
      requestCount++;
      const page = await notion.pages.retrieve({ page_id: pageId });
      cache.set(`page:${pageId}`, page);
      return page;
    },

    // Cached + filtered database query
    async queryDatabase(dbId: string, filter?: any, filterProps?: string[]) {
      const key = `query:${dbId}:${JSON.stringify(filter)}:${filterProps?.join(',')}`;
      const cached = cache.get(key);
      if (cached) return cached;
      requestCount++;
      const result = await notion.databases.query({
        database_id: dbId,
        ...(filter && { filter }),
        ...(filterProps && { filter_properties: filterProps }),
        page_size: 100,
      });
      cache.set(key, result);
      return result;
    },

    // Queued page create (respects rate limit)
    async createPage(dbId: string, properties: any) {
      return writeQueue.add(() => {
        requestCount++;
        return notion.pages.create({
          parent: { database_id: dbId },
          properties,
        });
      });
    },

    // Invalidate cache for a specific page or database
    invalidate(id: string) {
      for (const key of cache.keys()) {
        if (key.includes(id)) cache.delete(key);
      }
    },

    // Stats
    get stats() {
      return { requestCount, cacheSize: cache.size, queuePending: writeQueue.pending };
    },
  };
}
```

## Resources

- [Notion API Rate Limits](https://developers.notion.com/reference/request-limits) — 3 req/sec per token, `Retry-After` header on 429
- [Database Query Filter](https://developers.notion.com/reference/post-database-query-filter) — push filtering server-side
- [Filter Properties Parameter](https://developers.notion.com/reference/retrieve-a-page#filter-properties) — reduce response payload size
- [Notion Webhooks](https://developers.notion.com/reference/webhooks) — event-driven updates replacing polling
- [Block Children Append](https://developers.notion.com/reference/patch-block-children) — batch up to 100 blocks per call
- [Notion Pricing](https://www.notion.so/pricing) — API included at all tiers, no per-call charges

## Next Steps

For rate-limit retry patterns, see `notion-rate-limits`. For query and search patterns, see `notion-search-retrieve`. For overall architecture guidance, see `notion-reference-architecture`.
