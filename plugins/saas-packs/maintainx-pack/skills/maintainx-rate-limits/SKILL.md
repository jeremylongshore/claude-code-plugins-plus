---
name: maintainx-rate-limits
description: |
  Implement MaintainX API rate limiting, pagination, and backoff patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for MaintainX.
  Trigger with phrases like "maintainx rate limit", "maintainx throttling",
  "maintainx 429", "maintainx retry", "maintainx backoff", "maintainx pagination".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Rate Limits

## Overview
Handle MaintainX API rate limits gracefully with exponential backoff, cursor-based pagination, and request queuing to maximize throughput without triggering 429 errors.

## Prerequisites
- MaintainX API access configured
- Node.js 18+ with `axios`
- Understanding of async/await patterns

## Instructions

### Step 1: Rate-Limited Client Wrapper

```typescript
// src/rate-limited-client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

export class RateLimitedClient {
  private http: AxiosInstance;
  private requestQueue: Array<() => void> = [];
  private activeRequests = 0;
  private maxConcurrent = 5;
  private minDelayMs = 100;  // 10 requests/second max

  constructor(apiKey?: string) {
    const key = apiKey || process.env.MAINTAINX_API_KEY;
    if (!key) throw new Error('MAINTAINX_API_KEY required');

    this.http = axios.create({
      baseURL: 'https://api.getmaintainx.com/v1',
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
      },
      timeout: 30_000,
    });
  }

  private async throttle(): Promise<void> {
    if (this.activeRequests >= this.maxConcurrent) {
      await new Promise<void>((resolve) => this.requestQueue.push(resolve));
    }
    this.activeRequests++;
    await new Promise((r) => setTimeout(r, this.minDelayMs));
  }

  private release() {
    this.activeRequests--;
    const next = this.requestQueue.shift();
    if (next) next();
  }

  async request<T>(method: string, url: string, data?: any, params?: any): Promise<T> {
    await this.throttle();
    try {
      const response = await this.retryWithBackoff(
        () => this.http.request<T>({ method, url, data, params }),
      );
      return response.data;
    } finally {
      this.release();
    }
  }

  private async retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxRetries = 3,
    baseDelay = 1000, // 1 second initial backoff delay
  ): Promise<T> {
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (err) {
        const axiosErr = err as AxiosError;
        const status = axiosErr.response?.status;

        if (status !== 429 && !(status && status >= 500) || attempt === maxRetries) {
          throw err;
        }

        // Honor Retry-After header
        const retryAfter = axiosErr.response?.headers?.['retry-after'];
        const delayMs = retryAfter
          ? parseInt(retryAfter) * 1000
          : baseDelay * Math.pow(2, attempt) + Math.random() * 500;

        console.warn(
          `Rate limited (HTTP ${status}). Retry ${attempt + 1}/${maxRetries} in ${Math.round(delayMs)}ms`,
        );
        await new Promise((r) => setTimeout(r, delayMs));
      }
    }
    throw new Error('Unreachable');
  }
}
```

### Step 2: Cursor-Based Pagination

MaintainX returns a `cursor` field in list responses. Pass it as a query parameter to fetch the next page.

```typescript
async function paginateAll<T>(
  client: RateLimitedClient,
  endpoint: string,
  resultKey: string,
  params?: Record<string, any>,
): Promise<T[]> {
  const allItems: T[] = [];
  let cursor: string | undefined;

  do {
    const response: any = await client.request('GET', endpoint, undefined, {
      ...params,
      limit: 100,
      cursor,
    });
    const items = response[resultKey] as T[];
    allItems.push(...items);
    cursor = response.cursor ?? undefined;

    // Log progress for long-running operations
    if (allItems.length % 500 === 0) {
      console.log(`  Fetched ${allItems.length} items so far...`);
    }
  } while (cursor);

  return allItems;
}

// Usage
const allWorkOrders = await paginateAll(client, '/workorders', 'workOrders', {
  status: 'OPEN',
});
console.log(`Total: ${allWorkOrders.length} open work orders`);
```

### Step 3: Batch Operations with p-queue

```typescript
import PQueue from 'p-queue';

// 5 concurrent requests, max 10 per second
const queue = new PQueue({
  concurrency: 5,
  interval: 1000, // 1 second window for rate cap
  intervalCap: 10,
});

async function batchUpdate(
  client: RateLimitedClient,
  updates: Array<{ id: number; data: any }>,
) {
  const results = await Promise.allSettled(
    updates.map((update) =>
      queue.add(() =>
        client.request('PATCH', `/workorders/${update.id}`, update.data),
      ),
    ),
  );

  const succeeded = results.filter((r) => r.status === 'fulfilled').length;
  const failed = results.filter((r) => r.status === 'rejected').length;
  console.log(`Batch update: ${succeeded} succeeded, ${failed} failed`);
  return results;
}

// Close 100 completed work orders
const completedOrders = await paginateAll(
  client, '/workorders', 'workOrders', { status: 'COMPLETED' },
);

await batchUpdate(
  client,
  completedOrders.map((wo: any) => ({ id: wo.id, data: { status: 'CLOSED' } })),
);
```

### Step 4: Rate Limit Monitoring

```typescript
// src/rate-monitor.ts
class RateMonitor {
  private requests: number[] = [];
  private windowMs = 60_000; // 1 minute window

  record() {
    this.requests.push(Date.now());
    this.cleanup();
  }

  cleanup() {
    const cutoff = Date.now() - this.windowMs;
    this.requests = this.requests.filter((t) => t > cutoff);
  }

  getRate(): number {
    this.cleanup();
    return this.requests.length;
  }

  report() {
    const rate = this.getRate();
    const status = rate > 50 ? 'WARNING' : 'OK';
    console.log(`[RateMonitor] ${rate} req/min - ${status}`);
    return { rate, status };
  }
}
```

## Output
- Rate-limited client wrapper with built-in throttling and retry
- Cursor-based pagination utility collecting all results
- Batch operations with controlled concurrency via `p-queue`
- Rate monitoring to track and alert on API usage

## Error Handling
| Scenario | Strategy |
|----------|----------|
| 429 Too Many Requests | Exponential backoff with jitter, honor `Retry-After` header |
| `Retry-After` header present | Wait the specified number of seconds before retrying |
| Burst of requests | Queue with `p-queue` (concurrency: 5, intervalCap: 10/sec) |
| Large data sets (1000+ items) | Paginate with `limit: 100`, delay between pages |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [p-queue](https://github.com/sindresorhus/p-queue) -- Promise queue with concurrency control
- [Exponential Backoff](https://cloud.google.com/storage/docs/exponential-backoff)

## Next Steps
For security configuration, see `maintainx-security-basics`.

## Examples

**Adaptive rate limiting based on response headers**:

```typescript
// Adjust concurrency dynamically based on remaining quota
function adaptRate(headers: Record<string, string>, queue: PQueue) {
  const remaining = parseInt(headers['x-ratelimit-remaining'] || '100');
  if (remaining < 10) {
    queue.concurrency = 1;
    console.warn('Approaching rate limit, reducing concurrency to 1');
  } else if (remaining < 50) {
    queue.concurrency = 3;
  } else {
    queue.concurrency = 5;
  }
}
```
