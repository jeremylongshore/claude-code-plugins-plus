---
name: miro-rate-limits
description: |
  Implement Miro REST API v2 rate limiting with the credit-based system,
  exponential backoff, and request queuing.
  Trigger with phrases like "miro rate limit", "miro throttling",
  "miro 429", "miro retry", "miro backoff", "miro credits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, rate-limits, performance]
compatible-with: claude-code
---

# Miro Rate Limits

## Overview

Miro measures API usage in **credits**, not raw request counts. Each endpoint consumes a different number of credits based on complexity. The global limit is **100,000 credits per minute** per app.

## Credit System

### Rate Limit Levels

Each Miro REST API endpoint is assigned a rate limit level that determines its credit cost:

| Level | Credits per Call | Example Endpoints |
|-------|-----------------|-------------------|
| Level 1 | Lower cost | GET single board, GET single item |
| Level 2 | Medium cost | POST create sticky note, POST create shape, POST create connector |
| Level 3 | Higher cost | Batch operations, complex queries |
| Level 4 | Highest cost | Export, bulk data operations |

The exact credit cost per level is subject to change. Monitor via response headers.

### Rate Limit Response Headers

Every Miro API response includes these headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-RateLimit-Limit` | Total credits allocated per minute | `100000` |
| `X-RateLimit-Remaining` | Credits remaining in current window | `99850` |
| `X-RateLimit-Reset` | Unix timestamp when window resets | `1700000060` |

When rate limited, the response also includes:

| Header | Description | Example |
|--------|-------------|---------|
| `Retry-After` | Seconds to wait before retrying | `30` |

## Exponential Backoff with Jitter

```typescript
interface BackoffConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterMs: number;
}

const DEFAULT_BACKOFF: BackoffConfig = {
  maxRetries: 5,
  baseDelayMs: 1000,
  maxDelayMs: 32000,
  jitterMs: 500,
};

async function withBackoff<T>(
  operation: () => Promise<Response>,
  config = DEFAULT_BACKOFF
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    const response = await operation();

    if (response.ok) {
      return response.json();
    }

    // Only retry on 429 and 5xx
    if (response.status !== 429 && response.status < 500) {
      const error = await response.json().catch(() => ({}));
      throw new Error(`Miro API ${response.status}: ${error.message ?? 'Request failed'}`);
    }

    if (attempt === config.maxRetries) {
      throw new Error(`Miro API: Max retries (${config.maxRetries}) exceeded`);
    }

    // Prefer Retry-After header if available
    const retryAfter = response.headers.get('Retry-After');
    let delay: number;

    if (retryAfter) {
      delay = parseInt(retryAfter, 10) * 1000;
    } else {
      // Exponential backoff with jitter
      const exponential = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * config.jitterMs;
      delay = Math.min(exponential + jitter, config.maxDelayMs);
    }

    console.warn(
      `[Miro] ${response.status} — retry ${attempt + 1}/${config.maxRetries} in ${delay}ms`
    );
    await new Promise(r => setTimeout(r, delay));
  }

  throw new Error('Unreachable');
}

// Usage
const board = await withBackoff<MiroBoard>(() =>
  fetch('https://api.miro.com/v2/boards', {
    headers: { 'Authorization': `Bearer ${token}` },
  })
);
```

## Rate Limit Monitor

```typescript
class MiroRateLimitMonitor {
  private remaining = 100000;
  private resetAt = 0;
  private windowCreditsUsed = 0;

  /** Call after every API response */
  updateFromResponse(response: Response): void {
    const limit = response.headers.get('X-RateLimit-Limit');
    const remaining = response.headers.get('X-RateLimit-Remaining');
    const reset = response.headers.get('X-RateLimit-Reset');

    if (remaining) this.remaining = parseInt(remaining, 10);
    if (reset) this.resetAt = parseInt(reset, 10) * 1000;
    if (limit) {
      this.windowCreditsUsed = parseInt(limit, 10) - this.remaining;
    }
  }

  /** Check before making a request */
  shouldThrottle(): boolean {
    return this.remaining < 1000 && Date.now() < this.resetAt;
  }

  /** How long to wait before next request */
  getWaitMs(): number {
    if (!this.shouldThrottle()) return 0;
    return Math.max(0, this.resetAt - Date.now());
  }

  getStatus(): { remaining: number; usedPercent: number; resetsIn: number } {
    return {
      remaining: this.remaining,
      usedPercent: Math.round((this.windowCreditsUsed / 100000) * 100),
      resetsIn: Math.max(0, this.resetAt - Date.now()),
    };
  }
}
```

## Request Queue (p-queue)

For high-throughput integrations, queue requests to stay within limits.

```typescript
import PQueue from 'p-queue';

const monitor = new MiroRateLimitMonitor();

const miroQueue = new PQueue({
  concurrency: 5,           // Max parallel requests
  interval: 1000,           // Per second
  intervalCap: 10,          // Max 10 requests per second
  timeout: 30000,           // Per-request timeout
});

async function queuedMiroFetch(path: string, options?: RequestInit) {
  // Pre-flight throttle check
  const waitMs = monitor.getWaitMs();
  if (waitMs > 0) {
    console.warn(`[Miro] Throttling: waiting ${waitMs}ms for rate limit reset`);
    await new Promise(r => setTimeout(r, waitMs));
  }

  return miroQueue.add(async () => {
    const response = await fetch(`https://api.miro.com${path}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${process.env.MIRO_ACCESS_TOKEN}`,
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    monitor.updateFromResponse(response);

    if (!response.ok) {
      if (response.status === 429) {
        // Re-queue with backoff
        const retryAfter = parseInt(response.headers.get('Retry-After') ?? '5', 10);
        await new Promise(r => setTimeout(r, retryAfter * 1000));
        return queuedMiroFetch(path, options); // Retry
      }
      throw new Error(`Miro ${response.status}: ${await response.text()}`);
    }

    return response.json();
  });
}
```

## Batch Operations to Reduce Credit Usage

```typescript
// BAD: 50 individual GET requests = 50 credits
for (const id of itemIds) {
  const item = await miroFetch(`/v2/boards/${boardId}/items/${id}`);
}

// GOOD: 1 paginated list request, filter client-side = fewer credits
const allItems = await miroFetch(`/v2/boards/${boardId}/items?limit=50`);
const wantedItems = allItems.data.filter(item => itemIds.includes(item.id));

// GOOD: Use type filter to reduce response size
const stickyNotes = await miroFetch(`/v2/boards/${boardId}/items?type=sticky_note&limit=50`);
```

## Cost Estimation

```typescript
function estimateCreditsPerMinute(
  requestsPerMinute: number,
  avgLevel: 1 | 2 | 3 | 4
): { credits: number; percentOfLimit: number; safe: boolean } {
  // Approximate credit costs (actual values from Miro docs)
  const creditCost = { 1: 5, 2: 10, 3: 20, 4: 50 };
  const credits = requestsPerMinute * creditCost[avgLevel];
  return {
    credits,
    percentOfLimit: Math.round((credits / 100000) * 100),
    safe: credits < 80000,  // 80% safety margin
  };
}
```

## Error Handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| Approaching limit | `X-RateLimit-Remaining` < 5000 | Reduce request frequency |
| Rate limited | HTTP 429 | Backoff using `Retry-After` header |
| Sustained 429s | Multiple consecutive 429s | Pause all requests, wait for reset |
| Credit spike | Monitor shows >80% usage | Audit for unnecessary requests |

## Resources

- [Miro Rate Limiting](https://developers.miro.com/reference/rate-limiting)
- [REST API Rate Limits](https://developers.miro.com/reference/rate-limits)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `miro-security-basics`.
