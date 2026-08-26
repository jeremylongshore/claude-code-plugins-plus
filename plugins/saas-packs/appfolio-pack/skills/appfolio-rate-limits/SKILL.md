---
name: appfolio-rate-limits
description: 'Handle AppFolio API rate limits with throttling and backoff.

  Trigger: "appfolio rate limit".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio Rate Limits

## Overview

AppFolio's Stack API enforces per-partner rate limits to protect shared property management infrastructure. High-volume operations like bulk tenant imports, rent-roll syncs, and work-order batch updates can quickly exhaust quotas. Property managers running nightly portfolio syncs across hundreds of units must throttle carefully, especially during month-end when lease renewals and payment processing spike concurrently.

## Prerequisites

- A verified per-endpoint limit from the current AppFolio partner contract or
  response headers; do not rely on a generic rate value for tenant writes.
- Persisted batch cursors, idempotency keys for every write, and an operator
  policy for pausing month-end or other safety-sensitive workloads.
- A staging fixture and request-budget owner who can prove retries, `429`
  behavior, and unknown-write handling without touching production tenants.

## Instructions

1. Select the limiter ceiling for the specific endpoint and keep concurrency
   below the smallest applicable portfolio or partner limit.
2. Acquire a token before each request, honor `Retry-After`, and cap retries
   with jitter for transient provider failures.
3. Process writes from a persisted cursor with idempotency keys; never replay a
   tenant create just because the response was lost.
4. Pause and escalate batches that exhaust the retry budget, hit a maintenance
   window, or have an unknown write outcome.

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

  constructor(maxPerMinute: number) {
    this.maxTokens = maxPerMinute;
    this.tokens = maxPerMinute;
    this.lastRefill = Date.now();
    this.refillRate = maxPerMinute / 60_000;
  }

  async acquire(): Promise<void> {
    for (;;) {
      this.refill();
      if (this.tokens >= 1) {
        this.tokens -= 1;
        return;
      }
      // Wait until the next token is available; no later request is needed to
      // wake this caller.
      const waitMs = Math.max(1, Math.ceil((1 - this.tokens) / this.refillRate));
      await new Promise(resolve => setTimeout(resolve, waitMs));
    }
  }

  private refill() {
    const now = Date.now();
    this.tokens = Math.min(this.maxTokens, this.tokens + (now - this.lastRefill) * this.refillRate);
    this.lastRefill = now;
  }
}

const limiter = new AppFolioRateLimiter(25); // configure per endpoint contract
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

## Output

- A self-scheduling, endpoint-specific limiter that cannot strand queued work
- Bounded retry outcomes with `Retry-After` evidence and redacted failure data
- A persisted batch decision: completed, paused for later retry, or quarantined
  for operator reconciliation

## Examples

For a sandbox tenant-update batch, set the limiter below the documented tenant
write ceiling, process one record at a time with idempotency keys, and preserve
the cursor after each confirmed result. Induce a `429` to prove that callers
wait and resume without an additional request, then induce a lost response to
prove the record is quarantined rather than blindly replayed. If rate headers
conflict with the configured ceiling, retries exhaust, or maintenance starts,
pause the batch and hand the cursor to the owner.

## Resources

- [AppFolio Stack API](https://www.appfolio.com/stack/partners/api)

## Next Steps

See `appfolio-performance-tuning`.
