---
name: apify-rate-limits
description: |
  Handle Apify API rate limits with proper backoff and request queuing.
  Use when hitting 429 errors, optimizing API request throughput,
  or implementing rate-aware client wrappers.
  Trigger: "apify rate limit", "apify throttling", "apify 429",
  "apify retry", "apify backoff", "too many requests apify".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Rate Limits

## Overview

The Apify API enforces rate limits per resource. The `apify-client` library auto-retries 429s (up to 8 times with exponential backoff), but you need to understand the limits for bulk operations and custom API calls.

## Apify Rate Limit Rules

| Scope | Limit | Notes |
|-------|-------|-------|
| Per resource (default) | 60 req/sec | Applies to each Actor, dataset, KV store independently |
| Dataset push | 60 req/sec per dataset | Batch items to reduce call count |
| Actor runs | 60 req/sec per Actor | Start runs in sequence or with delays |
| Platform-wide | Higher limit | Aggregate across all resources |

**"Per resource" means:** calls to dataset A and dataset B each get 60 req/sec independently.

Rate limit headers returned:
- `X-RateLimit-Limit` — max requests per interval
- `X-RateLimit-Remaining` — remaining requests
- `X-RateLimit-Reset` — epoch seconds when limit resets

## Instructions

### Step 1: Understand Built-in Retries

The `apify-client` package handles rate limits automatically:

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

### Step 2: Batch Operations to Reduce API Calls

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

### Step 3: Queue-Based Rate Limiting for Custom Calls

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

### Step 4: Stagger Actor Starts

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

### Step 5: Rate Limit Monitor

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

## Crawlee-Level Concurrency (Target Website Rate Limits)

Separate from API rate limits, you must also respect the target website:

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

## Error Handling

| Scenario | Detection | Response |
|----------|-----------|----------|
| API 429 | `apify-client` auto-retries | Usually transparent; increase delays if persistent |
| Target site 429 | `statusCode === 429` in handler | Reduce `maxConcurrency`, add proxy rotation |
| Burst of starts | Starting 100+ runs at once | Stagger with 200ms delays |
| Large data push | Single 50MB dataset push | Chunk into 9MB batches |

## Resources

- [Apify API Rate Limits](https://docs.apify.com/api/v2)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [Crawlee Auto-scaling](https://crawlee.dev/js/docs/guides/configuration)

## Next Steps

For security configuration, see `apify-security-basics`.
