---
name: klaviyo-rate-limits
description: |
  Implement Klaviyo rate limiting, backoff, and request queuing patterns.
  Use when handling 429 errors, implementing retry logic,
  or optimizing API request throughput for Klaviyo.
  Trigger with phrases like "klaviyo rate limit", "klaviyo throttling",
  "klaviyo 429", "klaviyo retry", "klaviyo backoff", "klaviyo Retry-After".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Rate Limits

## Overview

Handle Klaviyo's per-account fixed-window rate limits with proper `Retry-After` header handling, exponential backoff, and request queuing.

## Prerequisites

- `klaviyo-api` SDK installed
- Understanding of Klaviyo's dual-window rate limiting

## Klaviyo Rate Limit Architecture

Klaviyo uses **per-account fixed-window rate limiting** with two distinct windows:

| Window | Duration | Limit | Description |
|--------|----------|-------|-------------|
| **Burst** | 1 second | 75 requests | Short spike protection |
| **Steady** | 1 minute | 700 requests | Sustained throughput cap |

Both windows apply simultaneously. Exceeding either triggers a `429 Too Many Requests`.

### Rate Limit Headers

**On successful requests:**
| Header | Description |
|--------|-------------|
| `RateLimit-Limit` | Max requests for the window |
| `RateLimit-Remaining` | Remaining requests in window |
| `RateLimit-Reset` | Seconds until window resets |

**On 429 responses (different headers!):**
| Header | Description |
|--------|-------------|
| `Retry-After` | Integer seconds to wait before retrying |

> **Critical:** When you hit a 429, `RateLimit-*` headers are NOT returned. Only `Retry-After` is present.

## Instructions

### Step 1: Retry-After Aware Backoff

```typescript
// src/klaviyo/rate-limiter.ts

export async function withRateLimitRetry<T>(
  operation: () => Promise<T>,
  options = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 60000 }
): Promise<T> {
  for (let attempt = 0; attempt <= options.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === options.maxRetries) throw error;

      const status = error.status;

      // Only retry on 429 (rate limit) and 5xx (server errors)
      if (status !== 429 && (status < 500 || status >= 600)) throw error;

      let delayMs: number;

      if (status === 429) {
        // ALWAYS honor Klaviyo's Retry-After header
        const retryAfter = error.headers?.['retry-after'];
        delayMs = retryAfter
          ? parseInt(retryAfter) * 1000
          : options.baseDelayMs * Math.pow(2, attempt);
      } else {
        // 5xx: exponential backoff with jitter
        const exponential = options.baseDelayMs * Math.pow(2, attempt);
        const jitter = Math.random() * options.baseDelayMs;
        delayMs = Math.min(exponential + jitter, options.maxDelayMs);
      }

      console.log(`[Klaviyo] ${status} on attempt ${attempt + 1}. Retrying in ${delayMs}ms...`);
      await new Promise(r => setTimeout(r, delayMs));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 2: Request Queue (Sustained Throughput)

```typescript
// src/klaviyo/queue.ts
import PQueue from 'p-queue';

// Respect Klaviyo's 75 req/s burst limit
// Leave headroom: target 60 req/s to avoid hitting the wall
const klaviyoQueue = new PQueue({
  concurrency: 10,        // Max parallel requests
  interval: 1000,         // Per second
  intervalCap: 60,        // 60 requests per second (safe margin)
});

export async function queuedKlaviyoCall<T>(
  operation: () => Promise<T>
): Promise<T> {
  return klaviyoQueue.add(() => withRateLimitRetry(operation));
}

// Monitor queue health
klaviyoQueue.on('idle', () => console.log('[Klaviyo] Queue drained'));
console.log(`[Klaviyo] Queue: pending=${klaviyoQueue.pending} size=${klaviyoQueue.size}`);
```

### Step 3: Rate Limit Monitor

```typescript
// src/klaviyo/monitor.ts

class RateLimitMonitor {
  private burstRemaining = 75;
  private steadyRemaining = 700;
  private burstResetAt = Date.now();
  private steadyResetAt = Date.now();

  updateFromHeaders(headers: Record<string, string>): void {
    const remaining = headers['ratelimit-remaining'];
    const reset = headers['ratelimit-reset'];

    if (remaining !== undefined) {
      this.burstRemaining = parseInt(remaining);
    }
    if (reset !== undefined) {
      this.burstResetAt = Date.now() + parseInt(reset) * 1000;
    }
  }

  shouldThrottle(): boolean {
    return this.burstRemaining < 10 && Date.now() < this.burstResetAt;
  }

  getWaitMs(): number {
    if (!this.shouldThrottle()) return 0;
    return Math.max(0, this.burstResetAt - Date.now());
  }

  getStatus(): { burstRemaining: number; shouldThrottle: boolean } {
    return {
      burstRemaining: this.burstRemaining,
      shouldThrottle: this.shouldThrottle(),
    };
  }
}

export const rateLimitMonitor = new RateLimitMonitor();
```

### Step 4: Bulk Operations with Rate Awareness

```typescript
// Process large datasets without hitting rate limits
export async function bulkProfileSync(
  profiles: Array<{ email: string; firstName?: string; properties?: Record<string, any> }>,
  batchSize = 50,    // Profiles per batch
  delayMs = 1000     // Delay between batches
): Promise<{ success: number; failed: number }> {
  let success = 0;
  let failed = 0;

  for (let i = 0; i < profiles.length; i += batchSize) {
    const batch = profiles.slice(i, i + batchSize);

    const results = await Promise.allSettled(
      batch.map(p =>
        queuedKlaviyoCall(() =>
          profilesApi.createOrUpdateProfile({
            data: {
              type: 'profile' as any,
              attributes: {
                email: p.email,
                firstName: p.firstName,
                properties: p.properties,
              },
            },
          })
        )
      )
    );

    success += results.filter(r => r.status === 'fulfilled').length;
    failed += results.filter(r => r.status === 'rejected').length;

    console.log(`[Klaviyo] Batch ${Math.floor(i / batchSize) + 1}: ${success} ok, ${failed} failed`);

    // Pace between batches
    if (i + batchSize < profiles.length) {
      await new Promise(r => setTimeout(r, delayMs));
    }
  }

  return { success, failed };
}
```

## Rate Limit Quick Reference

| Endpoint Category | Burst (1s) | Steady (1m) |
|-------------------|-----------|-------------|
| Most endpoints | 75 | 700 |
| Create Event | 75 | 700 |
| Bulk Subscribe | 75 | 700 |
| Reporting | Lower (varies) | Lower (varies) |

## Error Handling

| Scenario | Detection | Solution |
|----------|-----------|----------|
| Burst exceeded | 429 + short Retry-After | Wait Retry-After seconds |
| Steady exceeded | 429 + longer Retry-After | Queue requests, reduce concurrency |
| Thundering herd | Multiple 429s after resume | Add random jitter to retry delays |
| Stuck at 429 | Retry-After keeps growing | Reduce request volume; check for runaway loops |

## Resources

- [Klaviyo Rate Limits & Error Handling](https://developers.klaviyo.com/en/docs/rate_limits_and_error_handling)
- [API Overview](https://developers.klaviyo.com/en/reference/api_overview)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `klaviyo-security-basics`.
