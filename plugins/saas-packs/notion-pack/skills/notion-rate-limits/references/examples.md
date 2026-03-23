# Notion Rate Limits — Examples

## TypeScript — Rate-Limited Database Sync

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';
import PQueue from 'p-queue';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

const queue = new PQueue({
  concurrency: 3,
  interval: 1000,
  intervalCap: 3,
  carryoverConcurrencyCount: true,
});

async function syncDatabases(sourceDbId: string, targetDbId: string) {
  // Fetch all source pages with optimized pagination
  const sourcePages = [];
  let cursor: string | undefined;

  do {
    const response = await queue.add(() =>
      notion.databases.query({
        database_id: sourceDbId,
        page_size: 100,
        start_cursor: cursor,
      })
    );
    sourcePages.push(...response!.results);
    cursor = response!.has_more ? response!.next_cursor ?? undefined : undefined;
  } while (cursor);

  console.log(`Fetched ${sourcePages.length} source pages`);

  // Create pages in target DB with throttled queue
  let success = 0;
  let failed = 0;

  await Promise.all(
    sourcePages.map((page: any) =>
      queue.add(async () => {
        try {
          await notion.pages.create({
            parent: { database_id: targetDbId },
            properties: page.properties,
          });
          success++;
        } catch (error) {
          if (isNotionClientError(error) && error.code === APIErrorCode.RateLimited) {
            await queue.add(() =>
              notion.pages.create({
                parent: { database_id: targetDbId },
                properties: page.properties,
              })
            );
            success++;
          } else {
            failed++;
            console.error(`Failed: ${(error as Error).message}`);
          }
        }
      })
    )
  );

  console.log(`Sync complete: ${success} created, ${failed} failed`);
}
```

## Python — Rate-Limited Bulk Export

```python
import os
import time
import json
from notion_client import Client, APIResponseError

notion = Client(auth=os.environ["NOTION_TOKEN"])

def export_database(database_id: str, output_path: str):
    """Export all pages from a database with rate limit handling."""
    pages = []
    cursor = None
    request_count = 0

    while True:
        try:
            response = notion.databases.query(
                database_id=database_id,
                page_size=100,
                start_cursor=cursor,
            )
            request_count += 1
        except APIResponseError as e:
            if e.status == 429:
                retry_after = float(e.headers.get("retry-after", "1"))
                print(f"Rate limited after {request_count} requests. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue
            raise

        pages.extend(response["results"])
        print(f"Fetched {len(pages)} pages ({request_count} API calls)")

        if not response["has_more"]:
            break
        cursor = response["next_cursor"]
        time.sleep(0.35)  # Proactive delay: stay under 3 req/s

    with open(output_path, "w") as f:
        json.dump(pages, f, indent=2, default=str)

    print(f"Exported {len(pages)} pages to {output_path}")
    return pages
```

## Python — Exponential Backoff

```python
import time
import random
from notion_client import Client, APIResponseError

notion = Client(auth=os.environ["NOTION_TOKEN"])

def with_backoff(fn, max_retries=5, base_delay=1.0, max_delay=32.0):
    """Execute fn() with exponential backoff on rate limits and server errors."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except APIResponseError as e:
            if attempt == max_retries:
                raise
            if e.status == 429:
                retry_after = float(e.headers.get("retry-after", "1"))
                print(f"Rate limited. Waiting {retry_after}s (attempt {attempt + 1})")
                time.sleep(retry_after)
                continue
            if 400 <= e.status < 500:
                raise  # Don't retry client errors
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 0.5), max_delay)
            print(f"Server error ({e.status}). Retrying in {delay:.1f}s...")
            time.sleep(delay)
```

## Python — Asyncio Rate Limiter

```python
import asyncio
from notion_client import AsyncClient

notion = AsyncClient(auth=os.environ["NOTION_TOKEN"])

class RateLimiter:
    """Token-bucket rate limiter for Notion's 3 req/s limit."""

    def __init__(self, rate: float = 3.0, period: float = 1.0):
        self.semaphore = asyncio.Semaphore(int(rate))
        self.period = period / rate

    async def acquire(self):
        await self.semaphore.acquire()
        asyncio.get_event_loop().call_later(self.period, self.semaphore.release)

    async def execute(self, coro):
        await self.acquire()
        return await coro

limiter = RateLimiter(rate=3.0)

# Fetch 50 pages, throttled to 3/s
results = await asyncio.gather(*[
    limiter.execute(notion.pages.retrieve(page_id=pid))
    for pid in page_ids
])
```

## Rate Limit Monitoring and Alerting

```typescript
import { isNotionClientError, APIErrorCode } from '@notionhq/client';

class RateLimitMonitor {
  private events: { timestamp: number; endpoint: string }[] = [];
  private readonly windowMs = 60_000;

  record(endpoint: string): void {
    this.events.push({ timestamp: Date.now(), endpoint });
    this.cleanup();
  }

  cleanup(): void {
    const cutoff = Date.now() - this.windowMs;
    this.events = this.events.filter((e) => e.timestamp > cutoff);
  }

  report(): { total: number; byEndpoint: Record<string, number> } {
    this.cleanup();
    const byEndpoint: Record<string, number> = {};
    for (const e of this.events) {
      byEndpoint[e.endpoint] = (byEndpoint[e.endpoint] ?? 0) + 1;
    }
    return { total: this.events.length, byEndpoint };
  }
}

const monitor = new RateLimitMonitor();

async function monitoredCall<T>(endpoint: string, fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (isNotionClientError(error) && error.code === APIErrorCode.RateLimited) {
      monitor.record(endpoint);
      const { total, byEndpoint } = monitor.report();
      console.warn(`Rate limits in last 60s: ${total}`, byEndpoint);
      if (total > 10) {
        console.error('ALERT: Excessive rate limiting detected');
      }
    }
    throw error;
  }
}
```
