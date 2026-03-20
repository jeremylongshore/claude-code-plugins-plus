---
name: lokalise-rate-limits
description: |
  Implement Lokalise rate limiting, backoff, and request queuing patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Lokalise.
  Trigger with phrases like "lokalise rate limit", "lokalise throttling",
  "lokalise 429", "lokalise retry", "lokalise backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Rate Limits

## Overview

Lokalise enforces a strict **6 requests per second** rate limit across all API endpoints (`https://api.lokalise.com/api2`). Exceeding this triggers a `429 Too Many Requests` response. This skill covers request queuing with 170ms minimum spacing, exponential backoff for 429 recovery, bulk operation throttling, and proactive quota monitoring via response headers.

## Prerequisites

- `@lokalise/node-api` SDK installed (`npm install @lokalise/node-api`)
- API token configured (read or read/write scope depending on operations)
- Node.js 18+ for native `AbortController` support in timeout handling

## Instructions

### 1. Understand the Rate Limit Headers

Every Lokalise API response includes rate limit headers:

```
X-RateLimit-Limit: 6          # Max requests per second
X-RateLimit-Remaining: 4      # Requests remaining in current window
X-RateLimit-Reset: 1700000000 # Unix timestamp when the window resets
Retry-After: 1                # Seconds to wait (only on 429 responses)
```

Always read these headers. Never hardcode assumptions about the window — Lokalise may adjust limits per plan tier.

### 2. Implement a Request Queue with 170ms Spacing

Space requests at minimum 170ms apart (1000ms / 6 = ~167ms, rounded up). Use `p-queue` for concurrency control:

```typescript
import PQueue from "p-queue";

const lokaliseQueue = new PQueue({
  concurrency: 1,
  interval: 170,
  intervalCap: 1,
});

async function queuedRequest<T>(fn: () => Promise<T>): Promise<T> {
  return lokaliseQueue.add(fn, { throwOnTimeout: true });
}

// Usage with the SDK
import { LokaliseApi } from "@lokalise/node-api";
const lokalise = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN });

const keys = await queuedRequest(() =>
  lokalise.keys().list({
    project_id: "123456789.abcdefgh",
    limit: 500,
    page: 1,
  })
);
```

### 3. Add Exponential Backoff for 429 Recovery

When a 429 occurs, honor the `Retry-After` header first. If absent, use exponential backoff with jitter:

```typescript
async function withBackoff<T>(
  fn: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      if (error.code === 429 && attempt < maxRetries) {
        const retryAfter = error.headers?.["retry-after"];
        const baseDelay = retryAfter
          ? parseInt(retryAfter, 10) * 1000
          : Math.pow(2, attempt) * 1000;
        const jitter = Math.random() * 500;
        const delay = baseDelay + jitter;

        console.warn(
          `Rate limited. Attempt ${attempt + 1}/${maxRetries}. ` +
          `Waiting ${Math.round(delay)}ms...`
        );
        await new Promise((resolve) => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
  throw new Error("Max retries exceeded for Lokalise API request");
}
```

### 4. Throttle Bulk Operations

For operations that process many items (listing all keys, bulk translations), paginate with built-in throttling:

```typescript
async function paginateAll<T>(
  fetchPage: (page: number) => Promise<{ items: T[]; totalPages: number }>
): Promise<T[]> {
  const allItems: T[] = [];
  let page = 1;
  let totalPages = 1;

  do {
    const result = await queuedRequest(() => fetchPage(page));
    allItems.push(...result.items);
    totalPages = result.totalPages;
    page++;
  } while (page <= totalPages);

  return allItems;
}

// Fetch all keys across pages
const allKeys = await paginateAll(async (page) => {
  const response = await lokalise.keys().list({
    project_id: projectId,
    limit: 500, // max per page
    page,
  });
  return {
    items: response.items,
    totalPages: response.totalCount
      ? Math.ceil(response.totalCount / 500)
      : 1,
  };
});
```

For bulk key creation, batch into groups of 500 (API limit per request) and queue each batch:

```typescript
async function bulkCreateKeys(
  projectId: string,
  keys: Array<{ key_name: string; platforms: string[] }>
): Promise<void> {
  const batchSize = 500;
  for (let i = 0; i < keys.length; i += batchSize) {
    const batch = keys.slice(i, i + batchSize);
    await queuedRequest(() =>
      lokalise.keys().create({
        project_id: projectId,
        keys: batch,
      })
    );
    console.log(
      `Created keys ${i + 1}-${Math.min(i + batchSize, keys.length)} ` +
      `of ${keys.length}`
    );
  }
}
```

### 5. Monitor Quota Proactively

Track remaining quota and preemptively slow down before hitting the limit:

```typescript
let remainingRequests = 6;
let resetTimestamp = 0;

function updateQuota(headers: Record<string, string>): void {
  remainingRequests = parseInt(headers["x-ratelimit-remaining"] ?? "6", 10);
  resetTimestamp = parseInt(headers["x-ratelimit-reset"] ?? "0", 10);
}

async function throttleIfNeeded(): Promise<void> {
  if (remainingRequests <= 1) {
    const now = Math.floor(Date.now() / 1000);
    const waitSeconds = Math.max(0, resetTimestamp - now) + 0.5;
    console.warn(
      `Quota nearly exhausted (${remainingRequests} remaining). ` +
      `Pausing ${waitSeconds}s until reset.`
    );
    await new Promise((resolve) =>
      setTimeout(resolve, waitSeconds * 1000)
    );
  }
}
```

## Output

- Request queue enforcing 6 req/sec with 170ms minimum spacing between calls
- Automatic retry with exponential backoff + jitter on 429 responses
- Paginated fetching with throttling for bulk data retrieval
- Proactive throttling when `X-RateLimit-Remaining` drops to 1

## Error Handling

| Header | Description | Action |
|--------|-------------|--------|
| `X-RateLimit-Limit` | Max requests per window (always 6) | Use as concurrency ceiling |
| `X-RateLimit-Remaining` | Requests left in current window | Pause proactively when <= 1 |
| `X-RateLimit-Reset` | Unix timestamp of window reset | Sleep until this time on exhaustion |
| `Retry-After` | Seconds to wait (only on 429) | Always honor this value exactly |

If you receive a 429 without `Retry-After`, default to 1 second then exponential backoff. Never retry more than 5 times — if consistently rate-limited, your architecture needs request consolidation, not more retries.

## Examples

### Complete Rate-Limited Client

```typescript
import { LokaliseApi } from "@lokalise/node-api";
import PQueue from "p-queue";

class RateLimitedLokalise {
  private api: LokaliseApi;
  private queue: PQueue;

  constructor(apiKey: string) {
    this.api = new LokaliseApi({ apiKey });
    this.queue = new PQueue({ concurrency: 1, interval: 170, intervalCap: 1 });
  }

  async request<T>(fn: (api: LokaliseApi) => Promise<T>): Promise<T> {
    return this.queue.add(
      () => withBackoff(() => fn(this.api)),
      { throwOnTimeout: true }
    );
  }
}

// Usage
const client = new RateLimitedLokalise(process.env.LOKALISE_API_TOKEN!);
const keys = await client.request((api) =>
  api.keys().list({ project_id: "123456789.abcdefgh", limit: 500 })
);
```

### CLI with Rate Limiting

```bash
# The lokalise2 CLI respects rate limits internally, but for scripted
# loops you need manual spacing:
for project_id in $(lokalise2 project list --token $TOKEN --format json \
  | jq -r '.[].project_id'); do
  lokalise2 file download \
    --token "$LOKALISE_API_TOKEN" \
    --project-id "$project_id" \
    --format json \
    --dest ./locales/"$project_id"/
  sleep 0.2  # 200ms spacing
done
```

## Resources

- [Lokalise API Rate Limits](https://developers.lokalise.com/reference/api-rate-limits)
- [p-queue](https://github.com/sindresorhus/p-queue) — Promise-based queue with concurrency control
- [@lokalise/node-api SDK](https://github.com/lokalise/node-lokalise-api)

## Next Steps

For handling specific API errors beyond rate limits, see `lokalise-common-errors`.
