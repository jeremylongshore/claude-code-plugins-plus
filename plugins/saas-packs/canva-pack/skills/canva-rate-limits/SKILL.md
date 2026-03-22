---
name: canva-rate-limits
description: |
  Handle Canva Connect API rate limits with backoff, queuing, and monitoring.
  Use when hitting 429 errors, implementing retry logic,
  or optimizing API request throughput for Canva integrations.
  Trigger with phrases like "canva rate limit", "canva throttling",
  "canva 429", "canva retry", "canva backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Rate Limits

## Overview

The Canva Connect API enforces per-user, per-endpoint rate limits. Each endpoint has different thresholds. A 429 response means you must wait before retrying.

## Canva Connect API Rate Limits

| Endpoint | Method | Limit |
|----------|--------|-------|
| `/v1/users/me` | GET | 10 req/min |
| `/v1/users/me/profile` | GET | 10 req/min |
| `/v1/designs` | GET | 100 req/min |
| `/v1/designs` | POST | 20 req/min |
| `/v1/designs/{id}` | GET | 100 req/min |
| `/v1/exports` | POST | 75 req/5min, 500/24hr per user |
| `/v1/exports` (integration) | POST | 750 req/5min, 5000/24hr |
| `/v1/exports` (per document) | POST | 75 req/5min |
| `/v1/asset-uploads` | POST | 30 req/min |
| `/v1/autofills` | POST | 60 req/min |
| `/v1/folders` | POST | 20 req/min |
| `/v1/brand-templates` | GET | 100 req/min |

All limits are **per user** of your integration unless noted otherwise.

## Exponential Backoff with Jitter

```typescript
async function canvaRequestWithBackoff<T>(
  fn: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 60000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;

      // Only retry on 429 or 5xx
      const status = error.status || error.response?.status;
      if (status !== 429 && (status < 500 || status >= 600)) throw error;

      // Honor Retry-After header if present
      const retryAfter = error.headers?.get?.('Retry-After');
      const delay = retryAfter
        ? parseInt(retryAfter) * 1000
        : Math.min(
            config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 1000,
            config.maxDelayMs
          );

      console.warn(`Rate limited (attempt ${attempt + 1}/${config.maxRetries}). Waiting ${(delay / 1000).toFixed(1)}s`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Queue-Based Rate Limiting

```typescript
import PQueue from 'p-queue';

// Match per-user endpoint limits
const canvaQueues = {
  designs: new PQueue({ concurrency: 1, interval: 3000, intervalCap: 1 }),     // ~20/min
  exports: new PQueue({ concurrency: 1, interval: 4000, intervalCap: 1 }),     // ~15/min (conservative)
  assets:  new PQueue({ concurrency: 1, interval: 2000, intervalCap: 1 }),     // ~30/min
  reads:   new PQueue({ concurrency: 3, interval: 1000, intervalCap: 3 }),     // ~100/min (shared reads)
};

// Usage — automatically queued to stay under limits
const design = await canvaQueues.designs.add(() =>
  client.createDesign({ design_type: { type: 'custom', width: 1080, height: 1080 }, title: 'Queued' })
);

// Batch export with rate control
const designIds = ['DAV1', 'DAV2', 'DAV3', 'DAV4', 'DAV5'];
const exports = await Promise.all(
  designIds.map(id =>
    canvaQueues.exports.add(() =>
      client.createExport({ design_id: id, format: { type: 'pdf' } })
    )
  )
);
```

## Rate Limit Monitor

```typescript
class CanvaRateLimitTracker {
  private windows: Map<string, { count: number; resetAt: number }> = new Map();

  track(endpoint: string, response: Response): void {
    const remaining = response.headers.get('X-RateLimit-Remaining');
    const reset = response.headers.get('X-RateLimit-Reset');

    if (remaining !== null) {
      this.windows.set(endpoint, {
        count: parseInt(remaining),
        resetAt: reset ? parseInt(reset) * 1000 : Date.now() + 60000,
      });
    }
  }

  shouldThrottle(endpoint: string): boolean {
    const window = this.windows.get(endpoint);
    if (!window) return false;
    return window.count < 3 && Date.now() < window.resetAt;
  }

  getWaitMs(endpoint: string): number {
    const window = this.windows.get(endpoint);
    if (!window) return 0;
    return Math.max(0, window.resetAt - Date.now());
  }

  report(): Record<string, { remaining: number; resetsIn: string }> {
    const report: Record<string, any> = {};
    for (const [ep, w] of this.windows) {
      report[ep] = {
        remaining: w.count,
        resetsIn: `${Math.max(0, (w.resetAt - Date.now()) / 1000).toFixed(0)}s`,
      };
    }
    return report;
  }
}
```

## Proactive Throttling

```typescript
// Wrap the client to throttle before hitting limits
async function throttledCanvaRequest<T>(
  tracker: CanvaRateLimitTracker,
  endpoint: string,
  fn: () => Promise<T>
): Promise<T> {
  if (tracker.shouldThrottle(endpoint)) {
    const waitMs = tracker.getWaitMs(endpoint);
    console.log(`Proactively waiting ${waitMs}ms for ${endpoint}`);
    await new Promise(r => setTimeout(r, waitMs));
  }
  return fn();
}
```

## Error Handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| Single 429 | HTTP status | Wait `Retry-After` seconds, retry |
| Sustained 429s | Multiple retries fail | Reduce request rate, increase backoff |
| Export quota hit | 500/24hr per user | Queue exports, spread across hours |
| Integration quota | 5000/24hr exports | Distribute across users |

## Resources

- [API Requests & Responses](https://www.canva.dev/docs/connect/api-requests-responses/)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `canva-security-basics`.
