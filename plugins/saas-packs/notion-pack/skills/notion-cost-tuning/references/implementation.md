# Notion Cost Tuning — Full Implementation Walkthrough

This is the complete, code-level walkthrough for the three optimization steps summarized in `SKILL.md`. Each step is independent — apply them in order or cherry-pick the ones that match your bottleneck.

## Step 1: Audit Current Request Volume

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

## Step 2: Eliminate Redundant Reads and Reduce Payload Size

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

## Step 3: Cache, Batch, and Replace Polling

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
