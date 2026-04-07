---
name: appfolio-rate-limits
description: |
  Handle AppFolio API rate limits with throttling and backoff.
  Trigger: "appfolio rate limit".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# AppFolio Rate Limits

## Overview

AppFolio's Stack API enforces per-partner rate limits to protect shared property management infrastructure. High-volume operations like bulk tenant imports, rent-roll syncs, and work-order batch updates can quickly exhaust quotas. Property managers running nightly portfolio syncs across hundreds of units must throttle carefully, especially during month-end when lease renewals and payment processing spike concurrently.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| Properties list/get | 120 req | 1 minute | Per partner key |
| Tenant create/update | 30 req | 1 minute | Per partner key |
| Work orders | 60 req | 1 minute | Per partner key |
| Bulk data export | 5 req | 1 hour | Per partner key |
| Webhooks registration | 10 req | 1 minute | Per partner key |

## Rate Limiter Implementation

```typescript
class AppFolioRateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly maxTokens: number;
  private readonly refillRate: number; // tokens per ms
  private queue: Array<{ resolve: () => void }> = [];

  constructor(maxPerMinute: number) {
    this.maxTokens = maxPerMinute;
    this.tokens = maxPerMinute;
    this.lastRefill = Date.now();
    this.refillRate = maxPerMinute / 60_000;
  }

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens >= 1) { this.tokens -= 1; return; }
    return new Promise(resolve => this.queue.push({ resolve }));
  }

  private refill() {
    const now = Date.now();
    this.tokens = Math.min(this.maxTokens, this.tokens + (now - this.lastRefill) * this.refillRate);
    this.lastRefill = now;
    while (this.tokens >= 1 && this.queue.length) {
      this.tokens -= 1;
      this.queue.shift()!.resolve();
    }
  }
}

const limiter = new AppFolioRateLimiter(100);
```

## Retry Strategy

```typescript
async function appfolioRetry<T>(fn: () => Promise<Response>, maxRetries = 4): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    await limiter.acquire();
    const res = await fn();
    if (res.ok) return res.json();
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "10", 10);
      const delay = retryAfter * 1000 + Math.random() * 2000;
      await new Promise(r => setTimeout(r, delay));
      continue;
    }
    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
      continue;
    }
    throw new Error(`AppFolio API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function batchSyncTenants(tenants: any[], batchSize = 25) {
  const results: any[] = [];
  for (let i = 0; i < tenants.length; i += batchSize) {
    const batch = tenants.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(t => appfolioRetry(() =>
        fetch(`${BASE}/api/v1/tenants`, {
          method: "POST", headers, body: JSON.stringify(t),
        })
      ))
    );
    results.push(...batchResults);
    if (i + batchSize < tenants.length) await new Promise(r => setTimeout(r, 2000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 Too Many Requests | Exceeded partner rate limit | Backoff using Retry-After header |
| 403 on bulk export | Hourly export cap reached | Queue exports with 15-min spacing |
| Timeout on property list | Large portfolio (500+ units) | Paginate with `per_page=50` |
| 409 Conflict on tenant update | Concurrent write to same tenant | Retry with fresh ETag |
| 503 during maintenance | Scheduled nightly window (2-4 AM PT) | Skip requests, retry after window |

## Resources

- [AppFolio Stack API](https://www.appfolio.com/stack/partners/api)

## Next Steps

See `appfolio-performance-tuning`.
