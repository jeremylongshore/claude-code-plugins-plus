---
name: notion-rate-limits
description: |
  Manage Notion API rate limits with exponential backoff, queue-based throttling,
  and batch optimization. Use when hitting 429 errors, implementing retry logic,
  or optimizing API request throughput for Notion integrations.
  Trigger with "notion rate limit", "notion 429", "notion retry", "notion backoff",
  "notion throttling", "notion too many requests", "notion queue".
allowed-tools: Read, Write, Edit, Bash(npm:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion, rate-limiting, api, resilience]
compatible-with: claude-code
---

# Notion Rate Limits

## Overview

The Notion API enforces **3 requests per second per integration token** across all endpoints and tiers. Exceeding this returns HTTP 429 with a `Retry-After` header. Detect with `isNotionClientError()` + `APIErrorCode.RateLimited`, implement exponential backoff with jitter, and use queue-based throttling for high-throughput workloads.

## Prerequisites

- `@notionhq/client` v2.x (TypeScript) or `notion-client` (Python)
- Integration token in `NOTION_TOKEN` from [notion.so/my-integrations](https://www.notion.so/my-integrations)
- For queue patterns: `p-queue` v8+ (`npm install p-queue`)

## Instructions

### Step 1 — Detect Rate Limits and Apply Exponential Backoff

| Aspect | Value |
|--------|-------|
| Rate limit | 3 req/s per integration token (all tiers) |
| Throttle response | HTTP 429 + `Retry-After` header (seconds) |
| Scope | Per token, not per user or workspace |
| Max block children | 1,000 per `blocks.children.append` |
| Max page size | 100 results per paginated request |

The SDK retries 429 automatically (2 retries, 3 total attempts). For heavier workloads, use custom backoff that honors `Retry-After` and adds jitter to prevent thundering herd:

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function withBackoff<T>(
  fn: () => Promise<T>,
  maxRetries = 5, baseMs = 1000, maxMs = 32_000
): Promise<T> {
  for (let i = 0; i <= maxRetries; i++) {
    try { return await fn(); }
    catch (err) {
      if (i === maxRetries) throw err;
      if (isNotionClientError(err) && err.code === APIErrorCode.RateLimited) {
        const wait = parseInt((err as any).headers?.['retry-after'] ?? '1', 10);
        await new Promise(r => setTimeout(r, wait * 1000));
        continue;
      }
      if (isNotionClientError(err) && err.status && err.status < 500) throw err;
      const delay = Math.min(baseMs * 2 ** i + Math.random() * 500, maxMs);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Exhausted retries');
}
```

### Step 2 — Throttle with Queue-Based Request Management

Enforce the 3 req/s limit at the application level instead of relying on 429 responses:

```typescript
import PQueue from 'p-queue';

const queue = new PQueue({
  concurrency: 3, interval: 1000, intervalCap: 3,
  carryoverConcurrencyCount: true,
});

async function throttled<T>(fn: () => Promise<T>): Promise<T> {
  return queue.add(fn, { throwOnTimeout: true }) as Promise<T>;
}

// Fetch 50 pages — automatically throttled to 3/s
const pages = await Promise.all(
  pageIds.map(id => throttled(() => notion.pages.retrieve({ page_id: id })))
);
```

### Step 3 — Optimize Batch Operations to Minimize API Calls

Set `page_size: 100` on every paginated query. Batch block appends into chunks of 100 instead of one-per-block. See [batch patterns](references/batch-patterns.md) for full implementations with progress tracking.

```typescript
// Paginate with max page size
async function queryAll(dbId: string, filter?: any) {
  const results = [];
  let cursor: string | undefined;
  do {
    const resp = await throttled(() => notion.databases.query({
      database_id: dbId, page_size: 100, start_cursor: cursor, filter,
    }));
    results.push(...resp.results);
    cursor = resp.has_more ? resp.next_cursor ?? undefined : undefined;
  } while (cursor);
  return results;
}
```

## Output

- 429 errors retried automatically using `Retry-After` headers with jitter
- Queue-based throttling keeps requests at 3/s proactively
- Batch operations reduce total API calls via chunking and max `page_size`

## Error Handling

| Scenario | Strategy |
|----------|----------|
| Single 429 | Honor `Retry-After`, retry once |
| Repeated 429s | Exponential backoff + reduce concurrency |
| Bulk ops (50+ items) | Queue with `p-queue` at 3 req/s |
| Server error (5xx) | Backoff + retry up to 5 attempts |
| Client error (4xx) | Do not retry — fix the request |

## Examples

See [full TypeScript and Python examples](references/examples.md) for database sync, bulk export, and rate limit monitoring patterns.

## Resources

- [Notion Request Limits](https://developers.notion.com/reference/request-limits) — Official rate limit docs
- [Notion Status Codes](https://developers.notion.com/reference/status-codes) — 429 and error responses
- [@notionhq/client](https://www.npmjs.com/package/@notionhq/client) — SDK with built-in retry
- [p-queue](https://www.npmjs.com/package/p-queue) — Promise queue with rate limiting

## Next Steps

- See `notion-common-errors` for 401/403/404 troubleshooting alongside rate limits
- See `notion-sdk-patterns` for query patterns that work with these strategies
- See `notion-search-retrieve` for optimizing search to reduce API call volume
