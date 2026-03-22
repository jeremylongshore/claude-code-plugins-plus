---
name: webflow-rate-limits
description: |
  Handle Webflow Data API v2 rate limits — per-key limits, Retry-After headers,
  exponential backoff, request queuing, and bulk endpoint optimization.
  Use when hitting 429 errors, implementing retry logic,
  or optimizing API request throughput.
  Trigger with phrases like "webflow rate limit", "webflow throttling",
  "webflow 429", "webflow retry", "webflow backoff", "webflow too many requests".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Rate Limits

## Overview

Handle Webflow Data API v2 rate limits using the SDK's built-in retry, manual
backoff strategies, request queuing, and bulk endpoints to maximize throughput
without hitting 429 errors.

## Prerequisites

- `webflow-api` SDK installed
- Understanding of async/await patterns
- Knowledge of your site plan's rate limits

## Webflow Rate Limit Rules

### Per-Key Rate Limits

Rate limits are applied **per API key** (not per site or per user). Each token
has its own independent rate limit counter.

| Rule | Details |
|------|---------|
| Scope | Per API key |
| Reset window | 60 seconds (Retry-After header) |
| CDN-cached requests | Do **not** count against rate limits |
| Bulk endpoints | 1 request = 1 rate limit count (up to 100 items) |
| Site publish | Max 1 successful publish per minute |
| Webhook registrations | Max 75 per `triggerType` per site |

### Rate Limit Response Headers

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Max requests allowed in the window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `Retry-After` | Seconds to wait before retrying (on 429) |

### 429 Response

```json
{
  "code": "rate_limit",
  "message": "Rate limit exceeded. Please retry after 60 seconds."
}
```

## Instructions

### Step 1: SDK Built-In Retry

The `webflow-api` SDK automatically retries 429 and 5xx errors with exponential backoff:

```typescript
import { WebflowClient } from "webflow-api";

const webflow = new WebflowClient({
  accessToken: process.env.WEBFLOW_API_TOKEN!,
  maxRetries: 3, // Default: 2. SDK uses exponential backoff.
});

// The SDK handles 429s transparently — no extra code needed
const { sites } = await webflow.sites.list();
```

### Step 2: Manual Exponential Backoff with Jitter

For operations outside the SDK or when you need custom retry logic:

```typescript
async function withBackoff<T>(
  operation: () => Promise<T>,
  config = {
    maxRetries: 5,
    baseDelayMs: 1000,
    maxDelayMs: 60000,
    jitterMs: 500,
  }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      const status = error.statusCode || error.status;

      // Only retry on 429 (rate limit) and 5xx (server errors)
      if (attempt === config.maxRetries) throw error;
      if (status !== 429 && (status < 500 || status >= 600)) throw error;

      // Honor Retry-After header if present
      const retryAfter = error.headers?.get?.("Retry-After");
      let delay: number;

      if (retryAfter) {
        delay = parseInt(retryAfter) * 1000;
      } else {
        // Exponential backoff with jitter to prevent thundering herd
        const exponential = config.baseDelayMs * Math.pow(2, attempt);
        const jitter = Math.random() * config.jitterMs;
        delay = Math.min(exponential + jitter, config.maxDelayMs);
      }

      console.log(`Rate limited (attempt ${attempt + 1}). Retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage
const items = await withBackoff(() =>
  webflow.collections.items.listItems(collectionId)
);
```

### Step 3: Request Queue with Concurrency Control

Use `p-queue` to limit concurrent requests and prevent rate limit bursts:

```typescript
import PQueue from "p-queue";

// Webflow rate limits reset every 60 seconds
// Adjust concurrency based on your plan's limit
const queue = new PQueue({
  concurrency: 5,       // Max parallel requests
  interval: 1000,       // Time window (ms)
  intervalCap: 10,      // Max requests per interval
});

async function queuedRequest<T>(operation: () => Promise<T>): Promise<T> {
  return queue.add(operation) as Promise<T>;
}

// Usage — requests are automatically queued and throttled
const results = await Promise.all(
  collectionIds.map(id =>
    queuedRequest(() => webflow.collections.items.listItems(id))
  )
);
```

### Step 4: Use Bulk Endpoints to Reduce Request Count

A single bulk request counts as **one** rate limit hit but handles up to 100 items:

```typescript
// BAD: 100 individual requests = 100 rate limit counts
for (const item of items) {
  await webflow.collections.items.createItem(collectionId, { fieldData: item });
}

// GOOD: 1 bulk request = 1 rate limit count
await webflow.collections.items.createItemsBulk(collectionId, {
  items: items.slice(0, 100).map(item => ({ fieldData: item })),
});
```

Available bulk endpoints:
- `createItemsBulk` — Create up to 100 items
- `updateItemsBulk` — Update up to 100 items
- `deleteItemsBulk` — Delete up to 100 items
- `publishItem` — Publish multiple items by ID

### Step 5: Rate Limit Monitor

Track rate limit usage across your application:

```typescript
class RateLimitMonitor {
  private remaining = Infinity;
  private limit = 0;
  private resetAt: Date = new Date();

  updateFromHeaders(headers: Headers) {
    const remaining = headers.get("X-RateLimit-Remaining");
    const limit = headers.get("X-RateLimit-Limit");
    const retryAfter = headers.get("Retry-After");

    if (remaining) this.remaining = parseInt(remaining);
    if (limit) this.limit = parseInt(limit);
    if (retryAfter) {
      this.resetAt = new Date(Date.now() + parseInt(retryAfter) * 1000);
    }
  }

  shouldThrottle(): boolean {
    return this.remaining < 5 && new Date() < this.resetAt;
  }

  async waitIfNeeded(): Promise<void> {
    if (this.shouldThrottle()) {
      const waitMs = Math.max(0, this.resetAt.getTime() - Date.now());
      console.log(`Throttling: waiting ${waitMs}ms for rate limit reset`);
      await new Promise(r => setTimeout(r, waitMs));
    }
  }

  getStatus() {
    return {
      remaining: this.remaining,
      limit: this.limit,
      resetAt: this.resetAt.toISOString(),
      throttled: this.shouldThrottle(),
    };
  }
}
```

### Step 6: Batch Processing Large Datasets

For operations involving thousands of items:

```typescript
async function processLargeDataset(
  collectionId: string,
  allItems: Array<Record<string, any>>,
  batchSize = 100,
  delayBetweenBatchesMs = 1000
) {
  const results = { created: 0, failed: 0, errors: [] as any[] };

  for (let i = 0; i < allItems.length; i += batchSize) {
    const batch = allItems.slice(i, i + batchSize);
    const batchNum = Math.floor(i / batchSize) + 1;
    const totalBatches = Math.ceil(allItems.length / batchSize);

    try {
      await withBackoff(() =>
        webflow.collections.items.createItemsBulk(collectionId, {
          items: batch.map(item => ({ fieldData: item, isDraft: false })),
        })
      );
      results.created += batch.length;
      console.log(`Batch ${batchNum}/${totalBatches}: ${batch.length} items created`);
    } catch (error) {
      results.failed += batch.length;
      results.errors.push({ batch: batchNum, error });
    }

    // Delay between batches to stay within rate limits
    if (i + batchSize < allItems.length) {
      await new Promise(r => setTimeout(r, delayBetweenBatchesMs));
    }
  }

  return results;
}
```

## Output

- SDK auto-retry configured for 429 errors
- Manual backoff with Retry-After header support
- Request queue with concurrency control
- Bulk endpoints reducing request count by 100x
- Rate limit monitoring and adaptive throttling

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Persistent 429s | Too many keys sharing same plan | Reduce concurrency or upgrade plan |
| Site publish 429 | >1 publish/minute | Enforce 60s cooldown between publishes |
| Thundering herd | Multiple processes retry simultaneously | Add random jitter to backoff |
| Bulk request 400 | >100 items in batch | Cap batch size at 100 |

## Resources

- [Rate Limits Reference](https://developers.webflow.com/data/reference/rate-limits)
- [Bulk CMS Endpoints](https://developers.webflow.com/data/changelog/10232024)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `webflow-security-basics`.
