# Examples

Complete, copy-paste-ready examples that combine every technique in this skill.

## Full Performance-Tuned Client

A production-ready `NotionPerf` class that wraps caching, rate limiting, and
incremental sync behind a simple `query` / `sync` surface.

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

## Latency Comparison Before/After

Measure the improvement from caching + batching using the `trackedCall` /
`reportLatency` helpers from
[parallel requests and latency monitoring](parallel-requests-and-monitoring.md).

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
