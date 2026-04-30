---
name: onenote-rate-limits
description: 'Implement proper rate limit handling for OneNote Graph API with queue-based
  throttling.

  Use when building high-throughput OneNote integrations or debugging 429 errors.

  Trigger with "onenote rate limit", "onenote 429", "onenote throttling", "graph api
  throttle".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote — Rate Limit Handling & Request Throttling

## Overview

Microsoft Graph rate limits OneNote at **600 requests per 60 seconds per user** and **10,000 requests per 10 minutes per app/tenant**. When you exceed either limit, the API returns `429 Too Many Requests` with a `Retry-After` header specifying how many seconds to wait. Most implementations either ignore this header entirely (retrying immediately, making things worse) or use a fixed backoff that wastes capacity.

This skill implements a token bucket rate limiter, queue-based request throttling, and proper `Retry-After` header parsing. For multi-user apps, it tracks per-user and per-tenant budgets independently.

Key pain points addressed:
- The `Retry-After` header value is in seconds (not milliseconds) — many implementations parse this wrong
- The per-user limit (600/60s) is separate from the per-tenant limit (10,000/10min) — you can hit one without the other
- Batch requests (`$batch`) count as one request toward the limit, regardless of how many operations are inside
- After a 429, subsequent requests to ANY OneNote endpoint are throttled — not just the endpoint that triggered it

## Prerequisites

- Azure app registration with delegated permissions: `Notes.ReadWrite`
- App-only auth deprecated March 31, 2025 — use delegated auth only
- Python: `pip install msgraph-sdk azure-identity`
- Node/TypeScript: `npm install @microsoft/microsoft-graph-client @azure/identity @azure/msal-node`
- Optional: `npm install p-queue` for production queue management

## Instructions

### Step 1 — Understand the Rate Limit Structure

| Limit | Scope | Window | Threshold |
|-------|-------|--------|-----------|
| Per-user | Single user's delegated token | 60 seconds (rolling) | 600 requests |
| Per-tenant | All users + all apps in the tenant | 10 minutes (rolling) | 10,000 requests |

When either limit is hit:
- Response status: `429 Too Many Requests`
- Response header: `Retry-After: <seconds>` (integer, not milliseconds)
- All subsequent OneNote requests for that scope are blocked until the window resets
- Non-OneNote Graph endpoints (Outlook, OneDrive) are **not** affected

### Step 2 — Token Bucket Rate Limiter (TypeScript)

A token bucket preemptively throttles requests to stay below the limit, avoiding 429s entirely:

```typescript
class TokenBucket {
  private tokens: number;
  private lastRefill: number;
  private readonly maxTokens: number;
  private readonly refillRate: number; // tokens per millisecond

  constructor(maxTokens: number, refillWindowMs: number) {
    this.maxTokens = maxTokens;
    this.tokens = maxTokens;
    this.lastRefill = Date.now();
    this.refillRate = maxTokens / refillWindowMs;
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens >= 1) {
      this.tokens -= 1;
      return;
    }
    // Wait until a token is available
    const waitMs = Math.ceil((1 - this.tokens) / this.refillRate);
    await new Promise((resolve) => setTimeout(resolve, waitMs));
    this.tokens -= 1;
  }

  get available(): number {
    this.refill();
    return Math.floor(this.tokens);
  }
}

// Per-user bucket: 600 requests per 60 seconds
const userBucket = new TokenBucket(600, 60_000);

// Use with a safety margin (80% of limit)
const safeUserBucket = new TokenBucket(480, 60_000);
```

### Step 3 — Queue-Based Request Throttling

Wrap all OneNote API calls through a throttled queue that respects both the token bucket and `Retry-After` headers:

```typescript
import { Client } from "@microsoft/microsoft-graph-client";

class ThrottledOneNoteClient {
  private bucket: TokenBucket;
  private queue: Array<{
    resolve: (value: any) => void;
    reject: (error: any) => void;
    fn: () => Promise<any>;
  }> = [];
  private processing = false;
  private retryAfterUntil: number = 0; // Timestamp when retry-after expires

  constructor(
    private client: Client,
    maxRequestsPerMinute: number = 480 // 80% safety margin
  ) {
    this.bucket = new TokenBucket(maxRequestsPerMinute, 60_000);
  }

  async request<T>(fn: (client: Client) => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({ resolve, reject, fn: () => fn(this.client) });
      this.processQueue();
    });
  }

  private async processQueue(): Promise<void> {
    if (this.processing) return;
    this.processing = true;

    while (this.queue.length > 0) {
      // Respect Retry-After if we've been throttled
      const now = Date.now();
      if (this.retryAfterUntil > now) {
        const waitMs = this.retryAfterUntil - now;
        console.warn(`Rate limited — waiting ${Math.ceil(waitMs / 1000)}s`);
        await new Promise((r) => setTimeout(r, waitMs));
      }

      await this.bucket.acquire();
      const item = this.queue.shift()!;

      try {
        const result = await item.fn();
        item.resolve(result);
      } catch (err: any) {
        if (err.statusCode === 429) {
          const retryAfter = parseInt(err.headers?.["retry-after"] ?? "30", 10);
          this.retryAfterUntil = Date.now() + retryAfter * 1000;
          // Re-queue the failed request
          this.queue.unshift(item);
          console.warn(`429 received — Retry-After: ${retryAfter}s`);
        } else {
          item.reject(err);
        }
      }
    }

    this.processing = false;
  }
}

// Usage
const throttled = new ThrottledOneNoteClient(client);
const notebooks = await throttled.request((c) =>
  c.api("/me/onenote/notebooks").get()
);
```

### Step 4 — Per-User Tracking for Multi-User Apps

Multi-user apps must track rate limits per user, not globally:

```typescript
class MultiUserRateLimiter {
  private userBuckets: Map<string, TokenBucket> = new Map();
  private tenantBucket: TokenBucket;

  constructor() {
    // Tenant-wide: 10,000 per 10 minutes
    this.tenantBucket = new TokenBucket(8_000, 600_000); // 80% safety margin
  }

  async acquire(userId: string): Promise<void> {
    // Get or create per-user bucket
    if (!this.userBuckets.has(userId)) {
      this.userBuckets.set(userId, new TokenBucket(480, 60_000));
    }
    const userBucket = this.userBuckets.get(userId)!;

    // Must acquire from BOTH buckets
    await userBucket.acquire();
    await this.tenantBucket.acquire();
  }

  getStatus(userId: string): { userRemaining: number; tenantRemaining: number } {
    const userBucket = this.userBuckets.get(userId);
    return {
      userRemaining: userBucket?.available ?? 480,
      tenantRemaining: this.tenantBucket.available,
    };
  }
}
```

### Step 5 — Exponential Backoff with Jitter

For 429 responses without a `Retry-After` header (rare but possible), use exponential backoff with jitter:

```typescript
async function withBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err.statusCode !== 429 || attempt === maxRetries) throw err;

      const retryAfter = err.headers?.["retry-after"];
      let delayMs: number;

      if (retryAfter) {
        // Prefer server-specified delay (in seconds)
        delayMs = parseInt(retryAfter, 10) * 1000;
      } else {
        // Exponential backoff: 1s, 2s, 4s, 8s, 16s + jitter
        const base = Math.pow(2, attempt) * 1000;
        const jitter = Math.random() * 1000;
        delayMs = base + jitter;
      }

      console.warn(`Retry ${attempt + 1}/${maxRetries} in ${Math.ceil(delayMs / 1000)}s`);
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw new Error("Unreachable");
}

// Usage
const pages = await withBackoff(() =>
  client.api("/me/onenote/pages").top(50).get()
);
```

### Step 6 — Batch Requests to Reduce Call Count

The Graph `$batch` endpoint lets you send up to 20 operations in a single HTTP request. The entire batch counts as **one** request toward your rate limit:

```typescript
async function batchGetPages(client: Client, pageIds: string[]): Promise<any[]> {
  const batchSize = 20; // Graph batch limit
  const allResults: any[] = [];

  for (let i = 0; i < pageIds.length; i += batchSize) {
    const chunk = pageIds.slice(i, i + batchSize);
    const batchBody = {
      requests: chunk.map((id, idx) => ({
        id: String(idx + 1),
        method: "GET",
        url: `/me/onenote/pages/${id}?$select=id,title,lastModifiedDateTime`,
      })),
    };

    const batchResponse = await client.api("/$batch").post(batchBody);
    for (const response of batchResponse.responses) {
      if (response.status === 200) {
        allResults.push(response.body);
      } else {
        console.warn(`Batch item ${response.id} failed: ${response.status}`);
      }
    }
  }
  return allResults;
}

// 100 pages = 5 HTTP requests instead of 100
const pages = await batchGetPages(client, hundredPageIds);
```

### Step 7 — Python Rate Limiter with asyncio

```python
import asyncio
import time

class RateLimiter:
    """Token bucket rate limiter for OneNote Graph API."""

    def __init__(self, max_requests: int = 480, window_seconds: int = 60):
        self.max_tokens = max_requests
        self.tokens = float(max_requests)
        self.refill_rate = max_requests / window_seconds
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens < 1:
                wait = (1 - self.tokens) / self.refill_rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1

# Usage — combines token bucket with Retry-After handling
limiter = RateLimiter(max_requests=480, window_seconds=60)

async def safe_get_pages(client, section_id: str, max_retries: int = 3):
    for attempt in range(max_retries):
        await limiter.acquire()
        try:
            return await client.me.onenote.sections.by_onenote_section_id(
                section_id
            ).pages.get()
        except Exception as e:
            # Handle 429 with Retry-After header
            if hasattr(e, "response") and e.response.status_code == 429 and attempt < max_retries - 1:
                retry_after = int(e.response.headers.get("Retry-After", "30"))
                await asyncio.sleep(retry_after)
            else:
                raise
    raise RuntimeError("Max retries exceeded for OneNote API call")
```

### Step 8 — Monitor and Adjust Preemptively

Track your 429 rate over time and adjust thresholds:

```typescript
class RateLimitMonitor {
  private requestCount = 0;
  private throttleCount = 0;
  private windowStart = Date.now();

  record(wasThrottled: boolean): void {
    this.requestCount++;
    if (wasThrottled) this.throttleCount++;
  }

  getMetrics(): { total: number; throttled: number; throttleRate: number; windowMinutes: number } {
    const windowMinutes = (Date.now() - this.windowStart) / 60_000;
    return {
      total: this.requestCount,
      throttled: this.throttleCount,
      throttleRate: this.throttleCount / Math.max(this.requestCount, 1),
      windowMinutes: Math.round(windowMinutes * 10) / 10,
    };
  }

  // Alert if throttle rate exceeds threshold
  shouldReduceRate(): boolean {
    return this.getMetrics().throttleRate > 0.05; // >5% throttled = slow down
  }
}
```

## Output

Rate limit handling produces:
- Preemptive throttling via token bucket — requests are delayed before sending, not after 429
- `Retry-After` compliance — exact server-specified delays honored
- Batch consolidation — 20 operations per HTTP request for bulk workloads
- Monitoring metrics — request count, throttle count, throttle rate percentage

## Error Handling

| Status | Cause | Fix |
|--------|-------|-----|
| 429 (with Retry-After) | Per-user or per-tenant limit exceeded | Wait exactly `Retry-After` seconds; do not retry sooner |
| 429 (no Retry-After) | Rare edge case, limit exceeded | Exponential backoff with jitter starting at 1 second |
| 503 | Service throttling under load | Treat like 429 — backoff and retry |
| 500 | Internal error during throttled state | Do not count as rate limit; retry with normal backoff |

## Examples

**Calculate request budget for polling + CRUD:**
```typescript
const BUDGET_PER_MINUTE = 600;
const SAFETY_MARGIN = 0.8; // Use 80% of limit
const safeBudget = BUDGET_PER_MINUTE * SAFETY_MARGIN; // 480

// Allocate budget
const pollingSections = 20;
const pollIntervalSec = 30;
const pollRequestsPerMin = pollingSections * (60 / pollIntervalSec); // 40/min

const remainingForCrud = safeBudget - pollRequestsPerMin; // 440/min for user operations
console.log(`Polling: ${pollRequestsPerMin}/min | CRUD: ${remainingForCrud}/min`);
```

**Production health check:**
```typescript
const monitor = new RateLimitMonitor();
// After each API call:
monitor.record(/* wasThrottled */ false);

// Periodic check
setInterval(() => {
  const metrics = monitor.getMetrics();
  if (monitor.shouldReduceRate()) {
    console.warn(`High throttle rate: ${(metrics.throttleRate * 100).toFixed(1)}%`);
    // Dynamically increase poll interval or reduce batch concurrency
  }
}, 60_000);
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [Known Issues](https://learn.microsoft.com/en-us/graph/known-issues)
- [Graph API Reference](https://learn.microsoft.com/en-us/graph/api/overview)
- [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)

## Next Steps

- See `onenote-webhooks-events` for polling patterns that consume rate budget
- See `onenote-performance-tuning` for batch operations and `$select` to reduce payload size
- See `onenote-core-workflow-a` for CRUD operations that benefit from throttled clients
