---
name: figma-rate-limits
description: |
  Handle Figma REST API rate limits with exponential backoff and request queuing.
  Use when encountering 429 errors, implementing retry logic,
  or optimizing API request throughput for Figma.
  Trigger with phrases like "figma rate limit", "figma throttling",
  "figma 429", "figma retry", "figma backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Rate Limits

## Overview
Figma uses a leaky bucket algorithm for rate limiting. When the bucket is full, the API returns 429 with a `Retry-After` header. Limits vary by plan tier, seat type, and endpoint tier.

## Prerequisites
- Figma REST API integration working
- Understanding of async/await patterns

## Instructions

### Step 1: Understand the Rate Limit Model

**Endpoint tiers** (limits are per-user, per-minute):

| Tier | Endpoints | Typical Limit |
|------|-----------|--------------|
| Tier 1 | `GET /v1/files`, `GET /v1/images` | Higher quota |
| Tier 2 | `GET /v1/files/:key/comments`, `GET /v1/files/:key/variables/local` | Moderate quota |
| Tier 3 | `GET /v1/teams/:id/components`, `GET /v1/teams/:id/styles` | Lower quota |

**429 response headers:**

| Header | Type | Meaning |
|--------|------|---------|
| `Retry-After` | Integer (seconds) | Wait this long before retrying |
| `X-Figma-Plan-Tier` | String | Your Figma plan level |
| `X-Figma-Rate-Limit-Type` | String | `"low"` or `"high"` rate limit |
| `X-Figma-Upgrade-Link` | String | URL to upgrade for higher limits |

### Step 2: Implement Exponential Backoff
```typescript
async function figmaFetchWithRetry(
  path: string,
  token: string,
  maxRetries = 5
): Promise<any> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const res = await fetch(`https://api.figma.com${path}`, {
      headers: { 'X-Figma-Token': token },
    });

    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
      const limitType = res.headers.get('X-Figma-Rate-Limit-Type') || 'unknown';

      if (attempt === maxRetries) {
        throw new Error(`Rate limited after ${maxRetries} retries (${limitType})`);
      }

      // Use the Retry-After header -- Figma tells you exactly how long to wait
      const jitter = Math.random() * 1000;
      const delay = retryAfter * 1000 + jitter;
      console.warn(`429 (${limitType}). Waiting ${(delay/1000).toFixed(1)}s (attempt ${attempt + 1})`);
      await new Promise(r => setTimeout(r, delay));
      continue;
    }

    if (res.status >= 500 && attempt < maxRetries) {
      // Server errors: exponential backoff without Retry-After
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
      await new Promise(r => setTimeout(r, delay));
      continue;
    }

    if (!res.ok) {
      throw new Error(`Figma API error: ${res.status} ${await res.text()}`);
    }

    return res.json();
  }
}
```

### Step 3: Request Queue with Concurrency Control
```typescript
import PQueue from 'p-queue';

// Limit concurrent requests to avoid bursting the bucket
const figmaQueue = new PQueue({
  concurrency: 3,       // max 3 parallel requests
  interval: 1000,       // per second
  intervalCap: 5,       // max 5 requests per second
});

async function queuedFigmaRequest<T>(
  path: string,
  token: string
): Promise<T> {
  return figmaQueue.add(() => figmaFetchWithRetry(path, token));
}

// Usage -- all requests are automatically queued and throttled
const [file, comments, images] = await Promise.all([
  queuedFigmaRequest(`/v1/files/${fileKey}`, token),
  queuedFigmaRequest(`/v1/files/${fileKey}/comments`, token),
  queuedFigmaRequest(`/v1/images/${fileKey}?ids=0:1&format=svg`, token),
]);
```

### Step 4: Rate Limit Monitor
```typescript
class FigmaRateLimitMonitor {
  private requestLog: number[] = [];
  private windowMs = 60_000; // 1 minute window

  recordRequest() {
    this.requestLog.push(Date.now());
    // Trim old entries
    const cutoff = Date.now() - this.windowMs;
    this.requestLog = this.requestLog.filter(t => t > cutoff);
  }

  getRequestsInWindow(): number {
    const cutoff = Date.now() - this.windowMs;
    return this.requestLog.filter(t => t > cutoff).length;
  }

  shouldThrottle(safetyMargin = 0.8): boolean {
    // If we've used 80% of a conservative estimate, slow down
    const estimatedLimit = 30; // Conservative estimate
    return this.getRequestsInWindow() > estimatedLimit * safetyMargin;
  }
}

const monitor = new FigmaRateLimitMonitor();

// Wrap every request
async function monitoredFigmaFetch(path: string, token: string) {
  if (monitor.shouldThrottle()) {
    console.warn('Approaching rate limit, adding delay');
    await new Promise(r => setTimeout(r, 2000));
  }
  monitor.recordRequest();
  return figmaFetchWithRetry(path, token);
}
```

### Step 5: Batch Node Requests
```typescript
// Instead of N individual /v1/files/:key/nodes requests,
// batch node IDs into fewer requests
async function batchFetchNodes(
  fileKey: string,
  nodeIds: string[],
  batchSize = 50,
  token: string
) {
  const results: Record<string, any> = {};

  for (let i = 0; i < nodeIds.length; i += batchSize) {
    const batch = nodeIds.slice(i, i + batchSize);
    const ids = encodeURIComponent(batch.join(','));
    const data = await queuedFigmaRequest(
      `/v1/files/${fileKey}/nodes?ids=${ids}`,
      token
    );
    Object.assign(results, data.nodes);
  }

  return results;
}
```

## Output
- Automatic retry with `Retry-After` header compliance
- Request queue preventing burst overload
- Rate limit monitoring with proactive throttling
- Batch operations reducing total request count

## Error Handling
| Scenario | Detection | Response |
|----------|-----------|----------|
| Single 429 | `Retry-After` header | Wait exactly that duration |
| Repeated 429s | Multiple retries exhausted | Log, alert, back off longer |
| `low` rate limit type | `X-Figma-Rate-Limit-Type: low` | Consider upgrading Figma plan |
| Batch too large | 400 Bad Request | Reduce batch size to 50 IDs |

## Resources
- [Figma Rate Limits Documentation](https://developers.figma.com/docs/rest-api/rate-limits/)
- [What if I'm rate-limited?](https://help.figma.com/hc/en-us/articles/34963238552855)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps
For security configuration, see `figma-security-basics`.
