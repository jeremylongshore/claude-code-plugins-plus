---
name: apollo-rate-limits
description: |
  Implement Apollo.io rate limiting and backoff.
  Use when handling rate limits, implementing retry logic,
  or optimizing API request throughput.
  Trigger with phrases like "apollo rate limit", "apollo 429",
  "apollo throttling", "apollo backoff", "apollo request limits".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Rate Limits

## Overview
Implement robust rate limiting and backoff strategies for the Apollo.io API (`https://api.apollo.io/v1`). Apollo enforces hourly request quotas that vary by plan. Exceeding them returns HTTP 429 with a `Retry-After` header.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Understand Apollo Rate Limits
```
Plan          | Requests/Hour | Enrichment Credits/Month
--------------+---------------+-------------------------
Free          | 100           | 50
Basic         | 300           | 1,200
Professional  | 600           | 6,000
Enterprise    | Custom        | Custom
```

The API returns these headers on every response:
- `X-Rate-Limit-Limit` — requests allowed per window
- `X-Rate-Limit-Remaining` — requests remaining
- `Retry-After` — seconds to wait (on 429 responses)

### Step 2: Build a Token-Bucket Rate Limiter
```typescript
// src/apollo/rate-limiter.ts
export class TokenBucketLimiter {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private maxTokens: number = 300,        // match your plan
    private refillIntervalMs: number = 3_600_000,  // 1 hour
  ) {
    this.tokens = maxTokens;
    this.lastRefill = Date.now();
  }

  private refill() {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    const newTokens = Math.floor(
      (elapsed / this.refillIntervalMs) * this.maxTokens,
    );
    if (newTokens > 0) {
      this.tokens = Math.min(this.maxTokens, this.tokens + newTokens);
      this.lastRefill = now;
    }
  }

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens <= 0) {
      const waitMs = this.refillIntervalMs / this.maxTokens;
      await new Promise((r) => setTimeout(r, waitMs));
      this.refill();
    }
    this.tokens--;
  }

  get remaining(): number {
    this.refill();
    return this.tokens;
  }
}
```

### Step 3: Add Exponential Backoff with Jitter
```typescript
// src/apollo/backoff.ts
export async function withBackoff<T>(
  fn: () => Promise<T>,
  opts: { maxRetries?: number; baseMs?: number; maxMs?: number } = {},
): Promise<T> {
  const { maxRetries = 5, baseMs = 1000, maxMs = 60_000 } = opts;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      const status = err.response?.status;
      if (status !== 429 && status < 500) throw err;
      if (attempt === maxRetries) throw err;

      // Use Retry-After header if present, otherwise exponential backoff
      const retryAfter = err.response?.headers?.['retry-after'];
      const delayMs = retryAfter
        ? parseInt(retryAfter, 10) * 1000
        : Math.min(baseMs * 2 ** attempt + Math.random() * 500, maxMs);

      console.warn(
        `[Apollo] ${status} on attempt ${attempt + 1}/${maxRetries + 1}, ` +
        `retrying in ${Math.round(delayMs / 1000)}s`,
      );
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Create a Request Queue with Concurrency Control
```typescript
// src/apollo/queue.ts
import PQueue from 'p-queue';
import { TokenBucketLimiter } from './rate-limiter';

const limiter = new TokenBucketLimiter(300);  // adjust per plan

export const apolloQueue = new PQueue({
  concurrency: 5,            // max parallel requests
  intervalCap: 50,           // max requests per interval
  interval: 60_000,          // 1-minute sliding window
});

// Wrap every API call through the queue
export async function queuedRequest<T>(
  fn: () => Promise<T>,
  priority: number = 0,      // lower = higher priority
): Promise<T> {
  await limiter.acquire();
  return apolloQueue.add(() => fn(), { priority }) as Promise<T>;
}

// Usage:
// const data = await queuedRequest(
//   () => client.post('/people/search', searchParams),
//   0,  // high priority
// );
```

### Step 5: Monitor Rate Limit Usage
```typescript
// src/apollo/rate-monitor.ts
import { AxiosResponse } from 'axios';

interface RateLimitStatus {
  limit: number;
  remaining: number;
  usedPercent: number;
}

export function extractRateLimitInfo(response: AxiosResponse): RateLimitStatus {
  const limit = parseInt(response.headers['x-rate-limit-limit'] ?? '300', 10);
  const remaining = parseInt(response.headers['x-rate-limit-remaining'] ?? '300', 10);

  return {
    limit,
    remaining,
    usedPercent: Math.round(((limit - remaining) / limit) * 100),
  };
}

// Attach as axios interceptor
client.interceptors.response.use((response) => {
  const info = extractRateLimitInfo(response);
  if (info.usedPercent >= 80) {
    console.warn(`[Apollo] Rate limit ${info.usedPercent}% used (${info.remaining} remaining)`);
  }
  return response;
});
```

## Output
- `TokenBucketLimiter` class matching your Apollo plan quota
- Exponential backoff respecting `Retry-After` headers
- `PQueue`-based request queue with concurrency and interval caps
- Rate limit monitoring via axios response interceptor
- Console warnings at 80% quota usage

## Error Handling
| Scenario | Strategy |
|----------|----------|
| 429 with `Retry-After` | Wait the specified seconds, then retry |
| 429 without header | Exponential backoff (1s, 2s, 4s, ...) up to 60s |
| Burst of requests | Queue with `intervalCap` to smooth traffic |
| Approaching quota | Log warning at 80%, pause non-critical work at 95% |

## Examples

### Bulk Search with Rate Limiting
```typescript
import { queuedRequest } from './apollo/queue';
import { withBackoff } from './apollo/backoff';

const domains = ['stripe.com', 'notion.so', 'linear.app', /* ... 100 more */];

const results = await Promise.all(
  domains.map((domain) =>
    queuedRequest(() =>
      withBackoff(() =>
        client.post('/people/search', {
          q_organization_domains: [domain],
          per_page: 10,
        }),
      ),
    ),
  ),
);
console.log(`Searched ${results.length} domains within rate limits`);
```

## Resources
- [Apollo Rate Limits](https://apolloio.github.io/apollo-api-docs/#rate-limits)
- [p-queue Library](https://github.com/sindresorhus/p-queue)
- [Google Cloud Exponential Backoff](https://cloud.google.com/storage/docs/exponential-backoff)

## Next Steps
Proceed to `apollo-security-basics` for API security best practices.
