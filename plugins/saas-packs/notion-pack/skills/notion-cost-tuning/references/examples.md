# Notion Cost Tuning — Worked Examples

Two complete, copy-paste-ready examples: a calculator to estimate savings before you commit to changes, and a drop-in optimized client that bundles every technique from the walkthrough.

## Request Reduction Calculator

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

## Full Optimization Wrapper

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
