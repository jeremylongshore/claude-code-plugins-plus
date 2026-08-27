---
name: klaviyo-rate-limits
description: 'Implement Klaviyo rate limiting, backoff, and request queuing patterns.

  Use when handling 429 errors, implementing retry logic,

  or optimizing API request throughput for Klaviyo.

  Trigger with phrases like "klaviyo rate limit", "klaviyo throttling",

  "klaviyo 429", "klaviyo retry", "klaviyo backoff", "klaviyo Retry-After".

  '
allowed-tools: Read, Write, Edit
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Rate Limits

## Overview

Handle Klaviyo's per-account fixed-window rate limits with proper `Retry-After` header handling, exponential backoff, and request queuing. This skill installs a small set of composable helpers: a retry wrapper that honors Klaviyo's `Retry-After`, a request queue that paces sustained throughput, a monitor that reads live rate-limit headers, and a rate-aware bulk import.

## Prerequisites

- The `klaviyo-api` SDK installed in the target project (`npm install klaviyo-api`).
- The `p-queue` package installed for the request queue (`npm install p-queue`).
- A working knowledge of Klaviyo's dual-window (burst + steady) rate limiting, summarized in the architecture table below.
- Write access to the project's `src/klaviyo/` directory, where the generated helper files land.

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

### Step 1: Retry-After Aware Backoff (core)

Use `Write` to create `src/klaviyo/rate-limiter.ts` with the retry wrapper below. This is the foundation every other helper builds on: it retries only on 429 and 5xx, **always** honors Klaviyo's `Retry-After` on a 429, and falls back to exponential backoff with jitter for 5xx.

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

### Steps 2–4: Queue, Monitor, and Bulk operations

Layer the sustained-throughput controls on top of the retry wrapper. Each is a
small file you `Write` into `src/klaviyo/`; the full annotated code for all three
is in [the implementation walkthrough](references/implementation.md):

- **Step 2 — Request queue** (`src/klaviyo/queue.ts`): a `p-queue` capped at 60 req/s (headroom under the 75 req/s burst wall) that wraps every call in `withRateLimitRetry`. This prevents most 429s instead of just reacting to them.
- **Step 3 — Rate limit monitor** (`src/klaviyo/monitor.ts`): reads the `RateLimit-*` response headers so throttle decisions track the account's real remaining budget — important when multiple processes share one quota.
- **Step 4 — Rate-aware bulk sync** (`bulkProfileSync`): batches large imports through the queue and paces between batches so a 100k-profile sync never trips the steady (1-minute) cap.

Read [`references/implementation.md`](references/implementation.md) for the complete source of Steps 2–4, and [`references/examples.md`](references/examples.md) for end-to-end usage.

## Output

Applying this skill produces the following in the target project:

- `src/klaviyo/rate-limiter.ts` — `withRateLimitRetry`, the `Retry-After`-honoring retry wrapper (Step 1).
- `src/klaviyo/queue.ts` — `queuedKlaviyoCall`, the paced request queue (Step 2).
- `src/klaviyo/monitor.ts` — `rateLimitMonitor`, a live header-driven throttle monitor (Step 3).
- `bulkProfileSync` — a rate-aware batch import helper (Step 4).

At runtime the helpers emit `[Klaviyo]` console logs on each retry, batch, and queue-drain event, and `bulkProfileSync` returns a `{ success, failed }` count so callers can report import results. Net effect: Klaviyo API traffic stays under both the burst and steady windows, and any 429 that does occur is absorbed by honoring `Retry-After` rather than failing the request.

## Error Handling

| Scenario | Detection | Solution |
|----------|-----------|----------|
| Burst exceeded | 429 + short Retry-After | Wait Retry-After seconds |
| Steady exceeded | 429 + longer Retry-After | Queue requests, reduce concurrency |
| Thundering herd | Multiple 429s after resume | Add random jitter to retry delays |
| Stuck at 429 | Retry-After keeps growing | Reduce request volume; check for runaway loops |

## Examples

Common wirings of the helpers — a single rate-safe call, high-volume writes
through the queue, a 100k-profile import, and proactive throttling from live
headers — are collected in [`references/examples.md`](references/examples.md).
The minimal case is one wrapped call:

```typescript
import { withRateLimitRetry } from './klaviyo/rate-limiter';

const profile = await withRateLimitRetry(() =>
  profilesApi.getProfile('01H...')
);
```

See [the worked examples](references/examples.md) for Examples 2–4.

## Resources

- [Klaviyo Rate Limits & Error Handling](https://developers.klaviyo.com/en/docs/rate_limits_and_error_handling)
- [API Overview](https://developers.klaviyo.com/en/reference/api_overview)
- [p-queue](https://github.com/sindresorhus/p-queue)
- [Full implementation walkthrough](references/implementation.md) — Steps 2–4 source
- [Worked examples](references/examples.md) — end-to-end usage patterns

## Next Steps

For security configuration, see `klaviyo-security-basics`.
