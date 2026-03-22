---
name: notion-cost-tuning
description: |
  Optimize Notion API usage and reduce request volume.
  Use when analyzing Notion API usage patterns, reducing unnecessary requests,
  or implementing efficient data access strategies.
  Trigger with phrases like "notion cost", "notion API usage",
  "reduce notion requests", "notion optimization", "notion efficient".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Cost Tuning

## Overview
Optimize Notion API request volume through caching, batching, webhook-driven updates, and efficient query patterns. Notion does not charge per API request, but rate limits (3 req/s) make efficiency critical for performance.

## Prerequisites
- Understanding of your integration's request patterns
- Access to request logging or monitoring
- `@notionhq/client` installed

## Instructions

### Step 1: Audit Current Usage

```typescript
// Instrument the client to track request volume
let requestCount = 0;
const requestLog: { method: string; endpoint: string; timestamp: number }[] = [];

// Wrap notion calls with tracking
async function trackedCall<T>(method: string, fn: () => Promise<T>): Promise<T> {
  requestCount++;
  requestLog.push({ method, endpoint: method, timestamp: Date.now() });
  return fn();
}

// Periodic report
setInterval(() => {
  const last60s = requestLog.filter(r => r.timestamp > Date.now() - 60_000);
  console.log({
    totalRequests: requestCount,
    lastMinute: last60s.length,
    reqPerSecond: (last60s.length / 60).toFixed(1),
    breakdown: Object.groupBy(last60s, r => r.method),
  });
}, 60_000);
```

### Step 2: Eliminate Redundant Reads

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// BAD: Fetching full page when you only need the status
const page = await notion.pages.retrieve({ page_id: pageId });       // 1 request
const blocks = await notion.blocks.children.list({ block_id: pageId }); // 1 request
// 2 requests when you might only need properties

// GOOD: Properties are already in the database query result
const { results } = await notion.databases.query({
  database_id: dbId,
  filter: { property: 'Assignee', people: { contains: userId } },
});
// 1 request, all properties included — no separate retrieve needed
```

### Step 3: Use Filters to Reduce Page Size

```typescript
// BAD: Fetch all pages then filter in code
const all = await getAllPages(dbId); // May need 10+ paginated requests
const active = all.filter(p => getSelect(p, 'Status') === 'Active');

// GOOD: Filter server-side
const active = await notion.databases.query({
  database_id: dbId,
  filter: { property: 'Status', select: { equals: 'Active' } },
  page_size: 100,
});
// Typically 1 request instead of 10+
```

### Step 4: Use Timestamps to Fetch Only Changes

```typescript
// Instead of re-fetching everything, use last_edited_time filter
async function getRecentlyModified(dbId: string, sinceISO: string) {
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

// Usage: only fetch changes since last sync
let lastSync = new Date().toISOString();
setInterval(async () => {
  const changes = await getRecentlyModified(dbId, lastSync);
  if (changes.results.length > 0) {
    console.log(`${changes.results.length} pages changed since last sync`);
    await processChanges(changes.results);
    lastSync = new Date().toISOString();
  }
}, 60_000); // Check every minute instead of re-fetching everything
```

### Step 5: Replace Polling with Webhooks

```typescript
// BAD: Polling every 10 seconds (360 requests/hour for ONE database)
setInterval(async () => {
  const pages = await notion.databases.query({ database_id: dbId });
  await processPages(pages.results);
}, 10_000);

// GOOD: Webhook-driven (0 requests for monitoring, only on-demand reads)
app.post('/webhooks/notion', express.json(), async (req, res) => {
  res.status(200).json({ ok: true });

  if (req.body.type === 'page.properties_updated') {
    // Only fetch the specific page that changed
    const page = await notion.pages.retrieve({ page_id: req.body.data.id });
    await processPage(page);
  }
});
```

### Step 6: Batch Write Operations

```typescript
// BAD: Create pages one at a time
for (const task of tasks) {
  await notion.pages.create({
    parent: { database_id: dbId },
    properties: taskToProperties(task),
  });
} // 100 tasks = 100 requests

// BETTER: Throttle with p-queue but still one at a time
import PQueue from 'p-queue';
const queue = new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 });

await Promise.all(
  tasks.map(task =>
    queue.add(() => notion.pages.create({
      parent: { database_id: dbId },
      properties: taskToProperties(task),
    }))
  )
); // Same 100 requests but completes 3x faster

// BEST: Batch blocks into single append calls
const blocks = tasks.map(task => ({
  paragraph: { rich_text: [{ text: { content: task.description } }] },
}));
// 100 blocks in 1 request (max 100 per call)
await notion.blocks.children.append({
  block_id: parentPageId,
  children: blocks,
});
```

## Output
- Request volume analyzed and baseline established
- Redundant reads eliminated
- Server-side filtering replacing client-side filtering
- Polling replaced with webhooks where possible
- Write operations batched

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited despite optimization | Shared token across services | Use separate integrations |
| Stale data from caching | TTL too long | Reduce TTL or use webhook invalidation |
| Webhook not triggering | Integration not shared with page | Add via Connections menu |
| Large result sets | No filter applied | Always filter server-side |

## Examples

### Request Reduction Calculator
```typescript
function estimateRequestSavings(config: {
  databases: number;
  avgPagesPerDb: number;
  pollIntervalSeconds: number;
  hoursPerDay: number;
}) {
  const pollsPerHour = 3600 / config.pollIntervalSeconds;
  const beforePerHour = config.databases * pollsPerHour *
    Math.ceil(config.avgPagesPerDb / 100); // pagination
  const afterPerHour = 0; // webhooks = 0 polling requests

  console.log(`Before: ${beforePerHour} requests/hour`);
  console.log(`After: ${afterPerHour} requests/hour (webhook-driven)`);
  console.log(`Savings: ${beforePerHour * config.hoursPerDay}/day`);
}
```

## Resources
- [Request Limits](https://developers.notion.com/reference/request-limits)
- [Filter Database Entries](https://developers.notion.com/reference/post-database-query-filter)
- [Notion Webhooks](https://developers.notion.com/reference/webhooks)

## Next Steps
For architecture patterns, see `notion-reference-architecture`.
