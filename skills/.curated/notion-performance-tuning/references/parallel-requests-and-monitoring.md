# Parallel Requests with Rate-Limited Queue and Latency Monitoring

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
