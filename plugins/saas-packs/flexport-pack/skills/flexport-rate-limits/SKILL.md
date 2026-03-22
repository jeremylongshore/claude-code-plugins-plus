---
name: flexport-rate-limits
description: |
  Handle Flexport API rate limits with exponential backoff, queue-based throttling,
  and response header monitoring for logistics API calls.
  Trigger: "flexport rate limit", "flexport 429", "flexport throttling", "flexport backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Rate Limits

## Overview

The Flexport API v2 enforces rate limits per API key. When exceeded, you get a `429 Too Many Requests` with `Retry-After` and `X-RateLimit-*` headers. Key limits to know: the API returns headers on every response telling you remaining quota.

## Rate Limit Headers

| Header | Description | Example |
|--------|-------------|---------|
| `X-RateLimit-Limit` | Max requests per window | `100` |
| `X-RateLimit-Remaining` | Remaining in current window | `47` |
| `X-RateLimit-Reset` | Unix timestamp when window resets | `1711234567` |
| `Retry-After` | Seconds to wait (only on 429) | `30` |

## Instructions

### Step 1: Monitor Rate Limit Headers

```typescript
class RateLimitTracker {
  remaining = Infinity;
  resetAt = 0;

  update(headers: Headers) {
    this.remaining = parseInt(headers.get('X-RateLimit-Remaining') || '100');
    this.resetAt = parseInt(headers.get('X-RateLimit-Reset') || '0') * 1000;
  }

  async waitIfNeeded() {
    if (this.remaining <= 2 && Date.now() < this.resetAt) {
      const wait = this.resetAt - Date.now() + 100;
      console.log(`Rate limit near. Waiting ${wait}ms`);
      await new Promise(r => setTimeout(r, wait));
    }
  }
}
```

### Step 2: Exponential Backoff with Jitter

```typescript
async function flexportWithRetry<T>(
  fn: () => Promise<Response>,
  maxRetries = 4
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const res = await fn();

    if (res.ok) return res.json();

    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
      const jitter = Math.random() * 2000;
      const delay = retryAfter * 1000 + jitter;
      console.log(`429 rate limited. Retry in ${(delay / 1000).toFixed(1)}s`);
      await new Promise(r => setTimeout(r, delay));
      continue;
    }

    if (res.status >= 500 && attempt < maxRetries) {
      const delay = Math.pow(2, attempt) * 1000 + Math.random() * 1000;
      await new Promise(r => setTimeout(r, delay));
      continue;
    }

    throw new Error(`Flexport ${res.status}: ${await res.text()}`);
  }
  throw new Error('Max retries exceeded');
}
```

### Step 3: Queue-Based Throttling

```typescript
import PQueue from 'p-queue';

// Limit to 10 requests per second with max 3 concurrent
const flexportQueue = new PQueue({
  concurrency: 3,
  interval: 1000,
  intervalCap: 10,
});

async function throttledRequest(path: string): Promise<any> {
  return flexportQueue.add(() =>
    fetch(`https://api.flexport.com${path}`, {
      headers: {
        'Authorization': `Bearer ${process.env.FLEXPORT_API_KEY}`,
        'Flexport-Version': '2',
      },
    }).then(r => r.json())
  );
}

// Bulk operations stay within limits
const shipmentIds = ['shp_001', 'shp_002', 'shp_003', /* ... */];
const results = await Promise.all(
  shipmentIds.map(id => throttledRequest(`/shipments/${id}`))
);
```

## Error Handling

| Scenario | Strategy |
|----------|----------|
| Single 429 | Honor `Retry-After` header |
| Repeated 429s | Increase backoff, reduce concurrency |
| Bulk import | Use `p-queue` with `intervalCap` |
| Batch reads | Paginate with `per=100` to minimize calls |

## Resources

- [Flexport API Reference](https://apidocs.flexport.com/)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `flexport-security-basics`.
