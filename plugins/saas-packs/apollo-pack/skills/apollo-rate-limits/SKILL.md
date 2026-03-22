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
tags: [saas, apollo, api]

---
# Apollo Rate Limits

## Overview
Implement robust rate limiting and backoff for the Apollo.io API. Apollo uses **fixed-window rate limiting** with per-endpoint limits. Unlike hourly quotas, Apollo limits are **per minute** with a burst limit per second. Exceeding them returns HTTP 429.

## Prerequisites
- Valid Apollo API key
- Node.js 18+

## Instructions

### Step 1: Understand Apollo's Rate Limit Structure
Apollo's official rate limits (as of 2025):

```
Endpoint Category           | Limit/min | Burst/sec | Notes
----------------------------+-----------+-----------+-------------------------------
People Search               | 100       | 10        | /mixed_people/api_search (free)
People Enrichment           | 100       | 10        | /people/match (1 credit each)
Bulk People Enrichment      | 10        | 2         | /people/bulk_match (up to 10/call)
Organization Search         | 100       | 10        | /mixed_companies/search
Organization Enrichment     | 100       | 10        | /organizations/enrich
Contacts CRUD               | 100       | 10        | /contacts/*
Sequences                   | 100       | 10        | /emailer_campaigns/*
Deals                       | 100       | 10        | /opportunities/*
```

Response headers on every successful call:
- `x-rate-limit-limit` — max requests per window
- `x-rate-limit-remaining` — requests remaining in current window
- `retry-after` — seconds to wait (only on 429 responses)

### Step 2: Build a Per-Endpoint Rate Limiter
```typescript
// src/apollo/rate-limiter.ts
export class SlidingWindowLimiter {
  private timestamps: number[] = [];

  constructor(
    private maxRequests: number = 100,
    private windowMs: number = 60_000,
  ) {}

  async acquire(): Promise<void> {
    const now = Date.now();
    // Remove timestamps outside the window
    this.timestamps = this.timestamps.filter((t) => now - t < this.windowMs);

    if (this.timestamps.length >= this.maxRequests) {
      const oldestInWindow = this.timestamps[0];
      const waitMs = this.windowMs - (now - oldestInWindow) + 100;
      console.warn(`[RateLimit] At capacity (${this.maxRequests}/${this.windowMs}ms). Waiting ${waitMs}ms`);
      await new Promise((r) => setTimeout(r, waitMs));
    }

    this.timestamps.push(Date.now());
  }

  get remaining(): number {
    const now = Date.now();
    this.timestamps = this.timestamps.filter((t) => now - t < this.windowMs);
    return this.maxRequests - this.timestamps.length;
  }
}

// Create limiters per endpoint category
export const limiters = {
  search: new SlidingWindowLimiter(100, 60_000),
  enrichment: new SlidingWindowLimiter(100, 60_000),
  bulkEnrichment: new SlidingWindowLimiter(10, 60_000),
  contacts: new SlidingWindowLimiter(100, 60_000),
  sequences: new SlidingWindowLimiter(100, 60_000),
};
```

### Step 3: Exponential Backoff with Retry-After
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

      // Prefer Retry-After header, fall back to exponential backoff
      const retryAfter = err.response?.headers?.['retry-after'];
      const delayMs = retryAfter
        ? parseInt(retryAfter, 10) * 1000
        : Math.min(baseMs * 2 ** attempt + Math.random() * 500, maxMs);

      console.warn(`[Apollo] ${status} attempt ${attempt + 1}/${maxRetries + 1}, retry in ${Math.round(delayMs / 1000)}s`);
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Request Queue with Concurrency Control
```typescript
// src/apollo/queue.ts
import PQueue from 'p-queue';
import { limiters } from './rate-limiter';

type EndpointCategory = keyof typeof limiters;

const queues: Record<EndpointCategory, PQueue> = {
  search: new PQueue({ concurrency: 5, intervalCap: 10, interval: 1000 }),
  enrichment: new PQueue({ concurrency: 5, intervalCap: 10, interval: 1000 }),
  bulkEnrichment: new PQueue({ concurrency: 2, intervalCap: 2, interval: 1000 }),
  contacts: new PQueue({ concurrency: 5, intervalCap: 10, interval: 1000 }),
  sequences: new PQueue({ concurrency: 3, intervalCap: 5, interval: 1000 }),
};

export async function queuedRequest<T>(
  category: EndpointCategory,
  fn: () => Promise<T>,
): Promise<T> {
  await limiters[category].acquire();
  return queues[category].add(() => fn()) as Promise<T>;
}
```

### Step 5: Monitor Rate Limit Usage via Response Headers
```typescript
// src/apollo/rate-monitor.ts
import { AxiosInstance, AxiosResponse } from 'axios';

export function attachRateMonitor(client: AxiosInstance) {
  client.interceptors.response.use((response: AxiosResponse) => {
    const limit = response.headers['x-rate-limit-limit'];
    const remaining = response.headers['x-rate-limit-remaining'];

    if (limit && remaining) {
      const pct = Math.round(((parseInt(limit) - parseInt(remaining)) / parseInt(limit)) * 100);
      if (pct >= 80) {
        console.warn(`[Apollo] Rate limit ${pct}% used (${remaining}/${limit} remaining) on ${response.config.url}`);
      }
    }
    return response;
  });
}
```

## Output
- Per-endpoint sliding window rate limiter matching Apollo's actual limits
- Exponential backoff respecting `retry-after` headers
- `PQueue`-based request queue with per-second burst control
- Response header monitoring with 80% warning threshold

## Error Handling
| Scenario | Strategy |
|----------|----------|
| 429 with `retry-after` | Wait the specified seconds, then retry |
| 429 without header | Exponential backoff: 1s, 2s, 4s, 8s, up to 60s |
| Bulk enrichment limited | Use dedicated queue with 2/sec burst limit |
| Near quota (>80%) | Log warning, defer non-critical requests |

## Examples

### Bulk Search with Rate Limiting
```typescript
import { queuedRequest } from './apollo/queue';
import { withBackoff } from './apollo/backoff';

const domains = ['stripe.com', 'notion.so', 'linear.app', /* ... */];

const results = await Promise.all(
  domains.map((domain) =>
    queuedRequest('search', () =>
      withBackoff(() =>
        client.post('/mixed_people/api_search', {
          q_organization_domains_list: [domain],
          per_page: 25,
        }),
      ),
    ),
  ),
);
console.log(`Searched ${results.length} domains within rate limits`);
```

## Resources
- [Apollo Rate Limits](https://docs.apollo.io/reference/rate-limits)
- [API Usage Stats](https://docs.apollo.io/reference/view-api-usage-stats)
- [p-queue Library](https://github.com/sindresorhus/p-queue)

## Next Steps
Proceed to `apollo-security-basics` for API security best practices.
