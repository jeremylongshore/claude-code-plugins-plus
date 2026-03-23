---
name: notion-load-scale
description: |
  High-volume Notion operations: parallel requests within 3 req/sec,
  worker queues, database pagination at scale, incremental sync for
  large workspaces, and memory management for bulk operations.
  Trigger with phrases like "notion scale", "notion bulk operations",
  "notion high volume", "notion worker queue", "notion incremental sync".
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Load & Scale

## Overview

Patterns for high-volume Notion API usage within the 3 requests/second rate limit. Covers parallel request orchestration with `p-queue`, worker queue architecture for background processing, full database pagination at scale (100K+ records), incremental sync using `last_edited_time` filters to avoid re-fetching unchanged data, and memory management for bulk operations using streaming and chunked processing.

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- `p-queue` for rate-limited concurrency (`npm install p-queue`)
- Python: `notion-client` installed (`pip install notion-client`)
- `NOTION_TOKEN` set (each token gets its own 3 req/s limit)
- Test database in Notion (dedicated for load testing)

## Instructions

### Step 1: Parallel Requests Within Rate Limits

Notion enforces 3 requests/second per integration token. Use `p-queue` to maximize throughput without hitting 429 errors.

```typescript
import { Client } from '@notionhq/client';
import PQueue from 'p-queue';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Rate-limited queue: 3 requests per second, single concurrency
// Use intervalCap + interval instead of concurrency alone
const apiQueue = new PQueue({
  concurrency: 1,
  interval: 340,      // ~3 per second with safety margin
  intervalCap: 1,
});

// Metrics tracking
let totalRequests = 0;
let rateLimitHits = 0;
const startTime = Date.now();

function logThroughput() {
  const elapsed = (Date.now() - startTime) / 1000;
  console.log(`Throughput: ${(totalRequests / elapsed).toFixed(1)} req/s | Total: ${totalRequests} | 429s: ${rateLimitHits}`);
}

// Wrapper that tracks metrics and handles 429 automatically
async function rateLimitedCall<T>(label: string, fn: () => Promise<T>): Promise<T> {
  return apiQueue.add(async () => {
    totalRequests++;
    try {
      return await fn();
    } catch (error: any) {
      if (error.code === 'rate_limited') {
        rateLimitHits++;
        const retryAfter = parseInt(error.headers?.['retry-after'] ?? '1');
        console.warn(`[${label}] Rate limited, waiting ${retryAfter}s`);
        await new Promise(r => setTimeout(r, retryAfter * 1000));
        return fn(); // Single retry
      }
      throw error;
    }
  }) as Promise<T>;
}

// Example: query 5 databases in parallel (queued at 3/s)
const dbIds = ['db1', 'db2', 'db3', 'db4', 'db5'];
const results = await Promise.all(
  dbIds.map(id =>
    rateLimitedCall(`query-${id}`, () =>
      notion.databases.query({ database_id: id, page_size: 100 })
    )
  )
);
logThroughput();
```

```python
from notion_client import Client
import time
import threading

notion = Client(auth=os.environ["NOTION_TOKEN"])

class RateLimiter:
    """Simple token bucket rate limiter for 3 req/s."""
    def __init__(self, rate: float = 3.0):
        self.rate = rate
        self.tokens = rate
        self.last_time = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_time
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_time = now

            if self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.rate
                time.sleep(sleep_time)
                self.tokens = 0
            else:
                self.tokens -= 1

limiter = RateLimiter(rate=2.8)  # Slightly under 3/s for safety

def rate_limited_query(database_id: str, **kwargs):
    limiter.acquire()
    return notion.databases.query(database_id=database_id, **kwargs)
```

### Step 2: Worker Queue Architecture for Background Processing

For sustained high-volume operations, decouple API calls from user requests using a job queue.

```typescript
import { Client, isNotionClientError } from '@notionhq/client';
import PQueue from 'p-queue';

interface NotionJob {
  id: string;
  type: 'create' | 'update' | 'query' | 'append';
  payload: any;
  priority: number; // 0 = highest
  retries: number;
  maxRetries: number;
  createdAt: Date;
}

class NotionWorkerQueue {
  private notion: Client;
  private queue: PQueue;
  private deadLetter: NotionJob[] = [];
  private processed = 0;
  private failed = 0;

  constructor(token: string) {
    this.notion = new Client({ auth: token });
    this.queue = new PQueue({
      concurrency: 1,
      interval: 340,
      intervalCap: 1,
    });
  }

  async enqueue(job: Omit<NotionJob, 'id' | 'retries' | 'createdAt'>): Promise<string> {
    const fullJob: NotionJob = {
      ...job,
      id: crypto.randomUUID(),
      retries: 0,
      createdAt: new Date(),
    };

    this.queue.add(() => this.processJob(fullJob), { priority: job.priority });
    return fullJob.id;
  }

  private async processJob(job: NotionJob): Promise<void> {
    try {
      switch (job.type) {
        case 'create':
          await this.notion.pages.create(job.payload);
          break;
        case 'update':
          await this.notion.pages.update(job.payload);
          break;
        case 'query':
          await this.notion.databases.query(job.payload);
          break;
        case 'append':
          await this.notion.blocks.children.append(job.payload);
          break;
      }
      this.processed++;
    } catch (error) {
      job.retries++;
      if (isNotionClientError(error) && error.code === 'rate_limited') {
        const delay = Math.pow(2, job.retries) * 1000;
        await new Promise(r => setTimeout(r, delay));
        if (job.retries < job.maxRetries) {
          this.queue.add(() => this.processJob(job), { priority: job.priority });
          return;
        }
      }
      if (job.retries >= job.maxRetries) {
        this.deadLetter.push(job);
        this.failed++;
      } else {
        this.queue.add(() => this.processJob(job), { priority: job.priority });
      }
    }
  }

  getStats() {
    return {
      pending: this.queue.size,
      processed: this.processed,
      failed: this.failed,
      deadLetter: this.deadLetter.length,
    };
  }
}

// Usage: bulk create 500 pages in background
const worker = new NotionWorkerQueue(process.env.NOTION_TOKEN!);
const DB_ID = process.env.NOTION_DB_ID!;

for (let i = 0; i < 500; i++) {
  await worker.enqueue({
    type: 'create',
    priority: 1,
    maxRetries: 3,
    payload: {
      parent: { database_id: DB_ID },
      properties: {
        Name: { title: [{ text: { content: `Item ${i + 1}` } }] },
      },
    },
  });
}
// 500 pages at ~3/s = ~170 seconds
```

### Step 3: Full Pagination at Scale with Incremental Sync and Memory Management

For databases with 100K+ records, use streaming pagination and incremental sync to avoid re-fetching unchanged data.

```typescript
// Stream results instead of loading all into memory
async function* paginateDatabase(
  databaseId: string,
  filter?: any,
  sorts?: any[]
): AsyncGenerator<any[], void, unknown> {
  let cursor: string | undefined;
  let pageNum = 0;

  do {
    const response = await rateLimitedCall(`page-${pageNum}`, () =>
      notion.databases.query({
        database_id: databaseId,
        filter,
        sorts,
        page_size: 100,
        start_cursor: cursor,
      })
    );

    yield response.results;
    pageNum++;

    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);
}

// Process in chunks without loading everything into memory
async function processLargeDatabase(databaseId: string) {
  let totalProcessed = 0;

  for await (const batch of paginateDatabase(databaseId)) {
    for (const page of batch) {
      // Process each record immediately
      totalProcessed++;
    }

    if (totalProcessed % 1000 === 0) {
      console.log(`Processed ${totalProcessed} records...`);
      logThroughput();
    }
  }

  console.log(`Done: ${totalProcessed} total records processed`);
}

// Incremental sync: only fetch records modified since last sync
async function incrementalSync(
  databaseId: string,
  lastSyncISO: string // e.g., "2026-03-20T00:00:00.000Z"
): Promise<{ records: any[]; newSyncTimestamp: string }> {
  const syncStart = new Date().toISOString();
  const records: any[] = [];

  for await (const batch of paginateDatabase(databaseId, {
    timestamp: 'last_edited_time',
    last_edited_time: { on_or_after: lastSyncISO },
  }, [
    { timestamp: 'last_edited_time', direction: 'ascending' },
  ])) {
    records.push(...batch);
  }

  console.log(`Incremental sync: ${records.length} records changed since ${lastSyncISO}`);
  return { records, newSyncTimestamp: syncStart };
}

// Persist sync state between runs
import fs from 'fs';
const SYNC_STATE_FILE = '.notion-sync-state.json';

async function runIncrementalSync(databaseId: string) {
  let lastSync = '1970-01-01T00:00:00.000Z';
  try {
    const state = JSON.parse(fs.readFileSync(SYNC_STATE_FILE, 'utf8'));
    lastSync = state.lastSyncTimestamp;
  } catch { /* First run */ }

  const { records, newSyncTimestamp } = await incrementalSync(databaseId, lastSync);

  for (const record of records) {
    // Upsert to your local DB, update cache, etc.
  }

  fs.writeFileSync(SYNC_STATE_FILE, JSON.stringify({
    lastSyncTimestamp: newSyncTimestamp,
    recordsProcessed: records.length,
  }));
}
```

```python
def paginate_database(database_id: str, filter_obj=None):
    """Generator that yields batches without loading all into memory."""
    cursor = None
    while True:
        limiter.acquire()
        kwargs = {"database_id": database_id, "page_size": 100}
        if filter_obj:
            kwargs["filter"] = filter_obj
        if cursor:
            kwargs["start_cursor"] = cursor

        response = notion.databases.query(**kwargs)
        yield response["results"]

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

def incremental_sync(database_id: str, since_iso: str):
    """Fetch only records modified since the given timestamp."""
    filter_obj = {
        "timestamp": "last_edited_time",
        "last_edited_time": {"on_or_after": since_iso},
    }
    records = []
    for batch in paginate_database(database_id, filter_obj):
        records.extend(batch)
    return records

# Multi-token scaling: each integration token gets its own 3 req/s
def create_scaled_clients(tokens: list[str]):
    """Create multiple clients for parallel processing across rate limits."""
    return [Client(auth=token) for token in tokens]
    # 2 tokens = 6 req/s, 3 tokens = 9 req/s
```

## Output

- Rate-limited parallel requests maximizing 3 req/s throughput
- Worker queue with priority, retries, and dead letter handling
- Streaming pagination for 100K+ record databases
- Incremental sync reducing API calls by 90%+ on subsequent runs
- Memory-efficient processing via async generators

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Sustained 429 errors | Exceeding 3 req/s | Reduce `intervalCap` or increase `interval` |
| Memory growing during bulk read | Loading all results into array | Use async generator streaming |
| Stale incremental sync | Clock skew between systems | Use server-returned timestamps |
| Queue growing unbounded | Write rate exceeds 3/s sustained | Add more integration tokens (each gets own limit) |
| Timeout on large queries | Notion API response time | Reduce `page_size`, add retry logic |
| Duplicate records in sync | Concurrent modifications | Deduplicate by page ID after collection |

## Examples

### Capacity Calculator

```typescript
function calculateCapacity(config: {
  readsPerMinute: number;
  writesPerMinute: number;
  cacheHitRate: number;
  integrationTokens: number;
}) {
  const effectiveReads = config.readsPerMinute * (1 - config.cacheHitRate);
  const totalPerMinute = effectiveReads + config.writesPerMinute;
  const reqPerSecond = totalPerMinute / 60;
  const capacity = config.integrationTokens * 3;

  console.log('=== Capacity Plan ===');
  console.log(`Effective req/s: ${reqPerSecond.toFixed(1)} / ${capacity} capacity`);
  console.log(`Headroom: ${((1 - reqPerSecond / capacity) * 100).toFixed(0)}%`);
  console.log(reqPerSecond > capacity ? 'OVER CAPACITY' : 'Within limits');
}
```

### Quick Throughput Benchmark

```bash
# Time 10 sequential API calls to measure baseline latency
time for i in $(seq 1 10); do
  curl -s -o /dev/null -w "%{time_total}\n" \
    https://api.notion.com/v1/users/me \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28"
  sleep 0.34
done
```

## Resources

- [Notion Request Limits](https://developers.notion.com/reference/request-limits)
- [Notion Pagination](https://developers.notion.com/reference/pagination)
- [p-queue - Promise Queue with Concurrency Control](https://github.com/sindresorhus/p-queue)
- [Notion Database Query Filter](https://developers.notion.com/reference/post-database-query-filter)

## Next Steps

For reliability patterns, see `notion-reliability-patterns`.
For architecture decisions at scale, see `notion-architecture-variants`.
