# Apify Rate Limits — Full Implementation

Complete, runnable code for every step of the rate-limit workflow. The SKILL.md
body summarizes each step and its core lever; this file carries the full detail.

## Step 1: Understand built-in retries

The `apify-client` package handles rate limits automatically — it retries 429 and
500+ responses with exponential backoff. Tune the retry envelope only when the
defaults are too aggressive (hammering a struggling endpoint) or too shallow.

```typescript
import { ApifyClient } from 'apify-client';

// Default: retries up to 8 times on 429 and 500+ errors
const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

// Customize retry behavior
const client = new ApifyClient({
  token: process.env.APIFY_TOKEN,
  maxRetries: 5,         // Default: 8
  minDelayBetweenRetriesMillis: 500,  // Default: 500
});
```

## Step 2: Batch operations to reduce API calls

The cheapest request is the one you never make. Collapse per-item loops into a
single batched call (up to a 9 MB payload), and chunk only when the dataset is
larger than one payload can carry.

```typescript
// BAD: 1000 API calls (easily rate limited)
for (const item of items) {
  await client.dataset(dsId).pushItems([item]);
}

// GOOD: 1 API call (up to 9MB payload)
await client.dataset(dsId).pushItems(items);

// GOOD: Chunked for very large datasets
function chunkArray<T>(arr: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    chunks.push(arr.slice(i, i + size));
  }
  return chunks;
}

for (const chunk of chunkArray(items, 1000)) {
  await client.dataset(dsId).pushItems(chunk);
}
```

## Step 3: Queue-based rate limiting for custom calls

When you make raw API calls outside the client's retry path (custom endpoints,
fan-out reads), gate them through a `p-queue` so you never exceed the per-resource
ceiling. `intervalCap` bounds requests per interval; `concurrency` bounds parallel
in-flight calls.

```typescript
import PQueue from 'p-queue';

// 50 requests per second with max 10 concurrent
const apiQueue = new PQueue({
  concurrency: 10,
  interval: 1000,
  intervalCap: 50,
});

// All API calls go through the queue
async function rateLimitedCall<T>(fn: () => Promise<T>): Promise<T> {
  return apiQueue.add(fn) as Promise<T>;
}

// Usage
const results = await Promise.all(
  actorIds.map(id =>
    rateLimitedCall(() => client.actor(id).get())
  )
);
```

## Step 4: Stagger Actor starts

Launching many runs at once hits the runs endpoint's 429. Insert a small delay
between starts, then wait for all runs to finish in parallel.

```typescript
import { sleep } from 'crawlee';

// Start multiple Actor runs with delays to avoid 429 on the runs endpoint
async function staggeredRuns(
  actorId: string,
  inputs: Record<string, unknown>[],
  delayMs = 200,
) {
  const runs = [];
  for (const input of inputs) {
    const run = await client.actor(actorId).start(input);
    runs.push(run);
    await sleep(delayMs);
  }

  // Wait for all to finish
  const finished = await Promise.all(
    runs.map(run => client.run(run.id).waitForFinish())
  );
  return finished;
}
```

## Step 5: Rate limit monitor

Read the `X-RateLimit-*` headers off responses to warn before you hit the wall and
to decide when to pause. Feed `updateFromHeaders` from every response, check
`shouldPause()` before a batch, and sleep `getWaitMs()` when it returns true.

```typescript
class ApifyRateLimitMonitor {
  private remaining = 60;
  private resetAt = Date.now();
  private warningThreshold: number;

  constructor(warningThreshold = 10) {
    this.warningThreshold = warningThreshold;
  }

  updateFromHeaders(headers: Record<string, string>) {
    if (headers['x-ratelimit-remaining']) {
      this.remaining = parseInt(headers['x-ratelimit-remaining']);
    }
    if (headers['x-ratelimit-reset']) {
      this.resetAt = parseInt(headers['x-ratelimit-reset']) * 1000;
    }

    if (this.remaining < this.warningThreshold) {
      const waitMs = Math.max(0, this.resetAt - Date.now());
      console.warn(
        `Rate limit warning: ${this.remaining} requests remaining. ` +
        `Resets in ${waitMs}ms.`
      );
    }
  }

  shouldPause(): boolean {
    return this.remaining <= 1 && Date.now() < this.resetAt;
  }

  getWaitMs(): number {
    return Math.max(0, this.resetAt - Date.now());
  }
}
```

## Crawlee-level concurrency (target website rate limits)

Separate from Apify API rate limits, you must also respect the target website. The
crawler's concurrency knobs cap how hard you hit the site being scraped — a
different ceiling from the platform API.

```typescript
const crawler = new CheerioCrawler({
  // Limit concurrent requests to the target site
  maxConcurrency: 10,           // Max parallel requests
  minConcurrency: 1,            // Min parallel requests
  maxRequestsPerMinute: 120,    // Hard cap per minute

  // Auto-scale based on system resources
  autoscaledPoolOptions: {
    desiredConcurrency: 5,
    maxConcurrency: 20,
  },

  // Delay between requests
  requestHandlerTimeoutSecs: 30,
});
```
