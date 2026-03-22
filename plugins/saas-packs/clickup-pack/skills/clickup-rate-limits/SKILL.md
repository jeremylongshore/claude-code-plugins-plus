---
name: clickup-rate-limits
description: |
  Handle ClickUp API rate limits with backoff, queuing, and header monitoring.
  Use when hitting 429 errors, implementing retry logic, or optimizing
  API throughput against ClickUp's per-plan rate limits.
  Trigger: "clickup rate limit", "clickup 429", "clickup throttling",
  "clickup retry", "clickup backoff", "clickup request queue".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Rate Limits

## Overview

ClickUp enforces per-token, per-minute rate limits that vary by Workspace plan. When exceeded, the API returns HTTP 429 with rate limit headers.

## Rate Limit Tiers

| Workspace Plan | Requests/Min/Token | Burst Support |
|----------------|-------------------|---------------|
| Free Forever | 100 | No |
| Unlimited | 100 | No |
| Business | 100 | No |
| Business Plus | 1,000 | Yes |
| Enterprise | 10,000 | Yes |

## Rate Limit Headers

Every ClickUp API response includes these headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-RateLimit-Limit` | Max requests in window | `100` |
| `X-RateLimit-Remaining` | Requests left in window | `95` |
| `X-RateLimit-Reset` | Unix timestamp when limit resets | `1695000060` |

## Exponential Backoff with Jitter

```typescript
async function clickupRequestWithRetry<T>(
  path: string,
  options: RequestInit = {},
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 60000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    const response = await fetch(`https://api.clickup.com/api/v2${path}`, {
      ...options,
      headers: {
        'Authorization': process.env.CLICKUP_API_TOKEN!,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (response.ok) return response.json();

    if (response.status === 429) {
      // Use server-provided reset time when available
      const resetTimestamp = response.headers.get('X-RateLimit-Reset');
      let waitMs: number;

      if (resetTimestamp) {
        waitMs = Math.max(0, parseInt(resetTimestamp) * 1000 - Date.now()) + 1000;
      } else {
        // Exponential backoff with jitter
        const exponential = config.baseDelayMs * Math.pow(2, attempt);
        const jitter = Math.random() * 1000;
        waitMs = Math.min(exponential + jitter, config.maxDelayMs);
      }

      console.warn(`Rate limited. Waiting ${(waitMs / 1000).toFixed(1)}s (attempt ${attempt + 1})`);
      await new Promise(r => setTimeout(r, waitMs));
      continue;
    }

    // Non-retryable errors
    if (response.status < 500 && response.status !== 429) {
      const error = await response.json().catch(() => ({}));
      throw new Error(`ClickUp ${response.status}: ${error.err ?? 'Unknown error'}`);
    }

    // Server errors: retry with backoff
    if (attempt < config.maxRetries) {
      const delay = config.baseDelayMs * Math.pow(2, attempt);
      await new Promise(r => setTimeout(r, delay));
    }
  }

  throw new Error(`ClickUp API: max retries exceeded for ${path}`);
}
```

## Rate Limit Monitor

```typescript
class ClickUpRateLimitMonitor {
  private remaining = 100;
  private limit = 100;
  private resetAt = 0;

  updateFromResponse(response: Response): void {
    const remaining = response.headers.get('X-RateLimit-Remaining');
    const limit = response.headers.get('X-RateLimit-Limit');
    const reset = response.headers.get('X-RateLimit-Reset');

    if (remaining) this.remaining = parseInt(remaining);
    if (limit) this.limit = parseInt(limit);
    if (reset) this.resetAt = parseInt(reset) * 1000;
  }

  shouldThrottle(): boolean {
    return this.remaining < 10 && Date.now() < this.resetAt;
  }

  getWaitMs(): number {
    return Math.max(0, this.resetAt - Date.now());
  }

  getUsagePercent(): number {
    return ((this.limit - this.remaining) / this.limit) * 100;
  }
}
```

## Queue-Based Rate Limiting

```typescript
import PQueue from 'p-queue';

// Stay under 100 req/min for Free/Unlimited/Business
const clickupQueue = new PQueue({
  concurrency: 5,        // Max parallel requests
  interval: 1000,        // Per second window
  intervalCap: 1,         // 1 request per second = 60/min (safe margin)
});

async function queuedClickUpRequest<T>(path: string, options?: RequestInit): Promise<T> {
  return clickupQueue.add(() => clickupRequestWithRetry(path, options));
}

// Bulk operations stay within limits automatically
const taskIds = ['abc', 'def', 'ghi', 'jkl'];
const tasks = await Promise.all(
  taskIds.map(id => queuedClickUpRequest(`/task/${id}`))
);
```

## Pre-Flight Throttling

```typescript
// Check headers before sending burst of requests
async function preFlightCheck(): Promise<{ safe: boolean; waitMs: number }> {
  const response = await fetch('https://api.clickup.com/api/v2/user', {
    headers: { 'Authorization': process.env.CLICKUP_API_TOKEN! },
  });

  const remaining = parseInt(response.headers.get('X-RateLimit-Remaining') || '100');
  const reset = parseInt(response.headers.get('X-RateLimit-Reset') || '0') * 1000;

  if (remaining < 10) {
    return { safe: false, waitMs: Math.max(0, reset - Date.now()) };
  }
  return { safe: true, waitMs: 0 };
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Constant 429s | Exceeding plan limit | Upgrade plan or add request queuing |
| Thundering herd | All retries fire at same time | Add random jitter to backoff |
| Missing reset header | Older API version | Fall back to exponential backoff |
| Burst rejected | Too many concurrent | Reduce `concurrency` in queue |

## Resources

- [ClickUp Rate Limits](https://developer.clickup.com/docs/rate-limits)
- [p-queue Library](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `clickup-security-basics`.
