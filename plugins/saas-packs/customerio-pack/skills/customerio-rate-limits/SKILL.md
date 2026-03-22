---
name: customerio-rate-limits
description: |
  Implement Customer.io rate limiting and backoff.
  Use when handling high-volume API calls, implementing
  retry logic, or hitting 429 errors.
  Trigger: "customer.io rate limit", "customer.io throttle",
  "customer.io 429", "customer.io backoff", "customer.io too many requests".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, api, rate-limiting]

---
# Customer.io Rate Limits

## Overview

Understand Customer.io's API rate limits and implement proper throttling: token bucket limiters, exponential backoff with jitter, queue-based processing, and 429 response handling.

## Rate Limit Reference

| API | Endpoint | Limit | Scope |
|-----|----------|-------|-------|
| Track API | `identify`, `track`, `trackAnonymous` | ~100 req/sec | Per workspace |
| Track API | Batch operations | ~100 req/sec | Per workspace |
| App API | Transactional email/push | ~100 req/sec | Per workspace |
| App API | Broadcasts, queries | ~10 req/sec | Per workspace |

These are approximate. Customer.io uses sliding window rate limiting. When exceeded, you get a `429 Too Many Requests` response.

## Instructions

### Step 1: Token Bucket Rate Limiter

```typescript
// lib/rate-limiter.ts
export class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private readonly maxTokens: number = 80,  // Stay under 100/sec limit
    private readonly refillRate: number = 80   // Tokens per second
  ) {
    this.tokens = maxTokens;
    this.lastRefill = Date.now();
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
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
    const waitMs = ((1 - this.tokens) / this.refillRate) * 1000;
    await new Promise((r) => setTimeout(r, Math.ceil(waitMs)));
    this.tokens = 0;
    this.lastRefill = Date.now();
  }
}
```

### Step 2: Exponential Backoff with Jitter

```typescript
// lib/backoff.ts
interface BackoffOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitter: number;         // 0 to 1
}

const DEFAULTS: BackoffOptions = {
  maxRetries: 4,
  baseDelayMs: 1000,
  maxDelayMs: 60000,
  jitter: 0.25,
};

export async function withBackoff<T>(
  fn: () => Promise<T>,
  opts: Partial<BackoffOptions> = {}
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs, jitter } = { ...DEFAULTS, ...opts };
  let lastErr: Error | undefined;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      lastErr = err;
      const status = err.statusCode ?? err.status;

      // Don't retry 4xx errors (except 429)
      if (status >= 400 && status < 500 && status !== 429) throw err;

      if (attempt === maxRetries) break;

      // Check Retry-After header (429 responses)
      const retryAfter = err.headers?.["retry-after"];
      let delay: number;

      if (retryAfter) {
        delay = parseInt(retryAfter) * 1000;
      } else {
        delay = Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs);
      }

      // Add jitter to prevent thundering herd
      delay += delay * jitter * Math.random();
      console.warn(`CIO retry ${attempt + 1}/${maxRetries} in ${Math.round(delay)}ms`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw lastErr;
}
```

### Step 3: Rate-Limited Client

```typescript
// lib/customerio-rate-limited.ts
import { TrackClient, RegionUS } from "customerio-node";
import { TokenBucket } from "./rate-limiter";
import { withBackoff } from "./backoff";

export class RateLimitedCioClient {
  private client: TrackClient;
  private limiter: TokenBucket;

  constructor(siteId: string, apiKey: string, ratePerSec: number = 80) {
    this.client = new TrackClient(siteId, apiKey, { region: RegionUS });
    this.limiter = new TokenBucket(ratePerSec, ratePerSec);
  }

  async identify(userId: string, attrs: Record<string, any>): Promise<void> {
    await this.limiter.acquire();
    return withBackoff(() => this.client.identify(userId, attrs));
  }

  async track(userId: string, event: { name: string; data?: any }): Promise<void> {
    await this.limiter.acquire();
    return withBackoff(() => this.client.track(userId, event));
  }

  async trackAnonymous(event: {
    anonymous_id: string;
    name: string;
    data?: any;
  }): Promise<void> {
    await this.limiter.acquire();
    return withBackoff(() => this.client.trackAnonymous(event));
  }

  async suppress(userId: string): Promise<void> {
    await this.limiter.acquire();
    return withBackoff(() => this.client.suppress(userId));
  }

  async destroy(userId: string): Promise<void> {
    await this.limiter.acquire();
    return withBackoff(() => this.client.destroy(userId));
  }
}
```

### Step 4: Queue-Based Processing with p-queue

For sustained high volume, use `p-queue` for cleaner concurrency control:

```typescript
// lib/customerio-queued.ts
import PQueue from "p-queue";
import { TrackClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

// Process at most 80 requests per second with max 10 concurrent
const queue = new PQueue({
  concurrency: 10,
  interval: 1000,
  intervalCap: 80,
});

// Queue operations instead of calling directly
export function queueIdentify(userId: string, attrs: Record<string, any>) {
  return queue.add(() => cio.identify(userId, attrs));
}

export function queueTrack(userId: string, name: string, data?: any) {
  return queue.add(() => cio.track(userId, { name, data }));
}

// Monitor queue health
setInterval(() => {
  console.log(
    `CIO queue: pending=${queue.pending} size=${queue.size}`
  );
}, 10000);
```

Install: `npm install p-queue`

### Step 5: Bulk Import Strategy

For large data imports (>10K users), avoid hitting rate limits with controlled batching:

```typescript
// scripts/bulk-import.ts
import { RateLimitedCioClient } from "../lib/customerio-rate-limited";

async function bulkImport(users: { id: string; attrs: Record<string, any> }[]) {
  const client = new RateLimitedCioClient(
    process.env.CUSTOMERIO_SITE_ID!,
    process.env.CUSTOMERIO_TRACK_API_KEY!,
    50  // Conservative rate — 50/sec for imports
  );

  let processed = 0;
  let errors = 0;

  for (const user of users) {
    try {
      await client.identify(user.id, user.attrs);
      processed++;
    } catch (err: any) {
      errors++;
      console.error(`Failed user ${user.id}: ${err.message}`);
    }

    if (processed % 1000 === 0) {
      console.log(`Progress: ${processed}/${users.length} (${errors} errors)`);
    }
  }

  console.log(`Done: ${processed} processed, ${errors} errors`);
}
```

## Error Handling

| Scenario | Strategy |
|----------|----------|
| `429` received | Respect `Retry-After` header, fall back to exponential backoff |
| Burst traffic spike | Token bucket absorbs burst, queue holds overflow |
| Sustained high volume | Use p-queue with interval limiting |
| Bulk import | Use conservative rate (50/sec) with progress logging |
| Downstream timeout | Don't count as rate limit — retry normally |

## Resources

- [Track API Limits](https://docs.customer.io/integrations/api/track/)
- [App API Reference](https://docs.customer.io/integrations/api/app/)
- [p-queue npm](https://www.npmjs.com/package/p-queue)

## Next Steps

After implementing rate limits, proceed to `customerio-security-basics` for security best practices.
