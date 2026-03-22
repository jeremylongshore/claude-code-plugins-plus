---
name: notion-rate-limits
description: |
  Handle Notion API rate limits with backoff, queuing, and throttling.
  Use when hitting 429 errors, implementing retry logic,
  or optimizing API request throughput for Notion.
  Trigger with phrases like "notion rate limit", "notion throttling",
  "notion 429", "notion retry", "notion backoff", "notion too many requests".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Rate Limits

## Overview
The Notion API enforces a rate limit averaging 3 requests per second per integration. Handle 429 responses gracefully with the `Retry-After` header, exponential backoff, and request queuing.

## Prerequisites
- `@notionhq/client` installed (has built-in retry)
- Understanding of async/await patterns

## Instructions

### Step 1: Understand Notion's Rate Limits
| Aspect | Value |
|--------|-------|
| Rate limit | Average 3 requests/second per integration |
| Burst | Some bursts above average are allowed |
| Response on limit | HTTP 429 with `Retry-After` header (seconds) |
| Applies per | Integration token (not per user or workspace) |
| Payload size limit | 1000 block children per request |
| Page size limit | 100 results per paginated request |

There are no tiered rate limits. All integrations get the same limit regardless of plan.

### Step 2: Built-in SDK Retry
The `@notionhq/client` SDK retries 429 errors automatically:

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  // Built-in retry defaults:
  // maxRetries: 2 (total 3 attempts)
  // initialRetryDelayMs: 1000
  // maxRetryDelayMs: 60000
});

// For heavier workloads, increase retries:
const notionHeavy = new Client({
  auth: process.env.NOTION_TOKEN,
  // @ts-ignore — retry config is supported but not in all type defs
  retry: {
    maxRetries: 5,
    initialRetryDelayMs: 500,
    maxRetryDelayMs: 60_000,
  },
});
```

### Step 3: Custom Backoff for Batch Operations
```typescript
import { isNotionClientError, APIErrorCode } from '@notionhq/client';

async function withBackoff<T>(
  fn: () => Promise<T>,
  opts = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 32000 }
): Promise<T> {
  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === opts.maxRetries) throw error;

      // Only retry rate limits and server errors
      if (isNotionClientError(error)) {
        if (error.code === APIErrorCode.RateLimited) {
          const retryAfter = parseInt(error.headers?.['retry-after'] ?? '1');
          console.log(`Rate limited. Waiting ${retryAfter}s (attempt ${attempt + 1})`);
          await new Promise(r => setTimeout(r, retryAfter * 1000));
          continue;
        }
        // Don't retry client errors (400, 401, 404, etc.)
        if (error.status && error.status < 500 && error.status !== 429) {
          throw error;
        }
      }

      // Exponential backoff with jitter for server errors
      const delay = Math.min(
        opts.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500,
        opts.maxDelayMs
      );
      console.log(`Server error. Retrying in ${Math.round(delay)}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Queue-Based Throttling
```typescript
import PQueue from 'p-queue';

// Enforce 3 req/s with concurrency control
const notionQueue = new PQueue({
  concurrency: 3,          // max parallel requests
  interval: 1000,          // per 1 second
  intervalCap: 3,          // max 3 per interval
  carryoverConcurrencyCount: true,
});

async function throttledNotionCall<T>(fn: () => Promise<T>): Promise<T> {
  return notionQueue.add(fn, { throwOnTimeout: true });
}

// Usage — all calls are automatically throttled
const pages = await Promise.all(
  pageIds.map(id =>
    throttledNotionCall(() => notion.pages.retrieve({ page_id: id }))
  )
);
```

### Step 5: Batch Processing Pattern
```typescript
async function processBatch<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  batchSize = 3,
  delayMs = 350 // ~3/second
): Promise<R[]> {
  const results: R[] = [];

  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    const batchResults = await Promise.all(batch.map(processor));
    results.push(...batchResults);

    // Delay between batches (skip after last batch)
    if (i + batchSize < items.length) {
      await new Promise(r => setTimeout(r, delayMs));
    }
  }

  return results;
}

// Usage: update 100 pages without hitting rate limits
const updates = await processBatch(
  pageIds,
  (id) => notion.pages.update({
    page_id: id,
    properties: { Status: { select: { name: 'Processed' } } },
  }),
  3,    // 3 concurrent
  400   // 400ms between batches
);
```

## Output
- Rate limit errors handled with automatic retry
- Request throughput optimized within API limits
- Batch operations processed without 429 errors

## Error Handling
| Scenario | Strategy |
|----------|----------|
| Single 429 | Honor `Retry-After` header |
| Repeated 429s | Exponential backoff + reduce concurrency |
| Bulk operations (50+ items) | Queue with `p-queue` at 3/s |
| Burst then steady | SDK built-in retry sufficient |

## Examples

### Monitor Queue Health
```typescript
notionQueue.on('active', () => {
  console.log(`Queue: ${notionQueue.size} pending, ${notionQueue.pending} active`);
});

notionQueue.on('idle', () => {
  console.log('Queue: all requests complete');
});
```

## Resources
- [Notion Rate Limits](https://developers.notion.com/reference/request-limits)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [@notionhq/client Retry Config](https://github.com/makenotion/notion-sdk-js)

## Next Steps
For security configuration, see `notion-security-basics`.
