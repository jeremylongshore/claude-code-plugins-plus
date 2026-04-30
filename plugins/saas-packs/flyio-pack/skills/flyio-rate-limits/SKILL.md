---
name: flyio-rate-limits
description: 'Handle Fly.io Machines API rate limits with backoff, concurrency control,

  and request batching for machine management operations.

  Trigger: "fly.io rate limit", "fly.io 429", "fly.io throttling", "machines API limit".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- edge-compute
- flyio
compatibility: Designed for Claude Code
---
# Fly.io Rate Limits

## Overview

The Fly.io Machines API rate-limits per organization, with write operations (create, delete, update) throttled much more aggressively than reads. Deploying fleets of edge machines across multiple regions can easily trigger 429s, especially during rolling deployments or auto-scaling events. The API returns a `Retry-After` header on rate-limited responses, and organizations running 50+ machines should implement client-side token bucket limiting to avoid cascading failures during high-churn operations.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| Machine create/delete | 10 req | 1 minute | Per org |
| Machine start/stop | 30 req | 1 minute | Per org |
| Machine list/get | 120 req | 1 minute | Per org |
| App create/delete | 5 req | 1 minute | Per org |
| Volume operations | 15 req | 1 minute | Per org |

## Rate Limiter Implementation

```typescript
class FlyRateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly max: number;
  private readonly refillRate: number;
  private queue: Array<{ resolve: () => void }> = [];

  constructor(maxPerMinute: number) {
    this.max = maxPerMinute;
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
    this.tokens = Math.min(this.max, this.tokens + (now - this.lastRefill) * this.refillRate);
    this.lastRefill = now;
    while (this.tokens >= 1 && this.queue.length) {
      this.tokens -= 1;
      this.queue.shift()!.resolve();
    }
  }
}

const writeLimiter = new FlyRateLimiter(8);  // leave headroom under 10/min
const readLimiter = new FlyRateLimiter(100);
```

## Retry Strategy

```typescript
async function flyRetry<T>(fn: () => Promise<Response>, maxRetries = 4): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
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
    throw new Error(`Fly API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function rollingDeployMachines(appId: string, configs: any[], batchSize = 3) {
  const results: any[] = [];
  for (let i = 0; i < configs.length; i += batchSize) {
    const batch = configs.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(async cfg => {
        await writeLimiter.acquire();
        return flyRetry(() =>
          fetch(`https://api.machines.dev/v1/apps/${appId}/machines`, {
            method: "POST", headers, body: JSON.stringify(cfg),
          })
        );
      })
    );
    results.push(...batchResults);
    if (i + batchSize < configs.length) await new Promise(r => setTimeout(r, 10_000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 on machine create | Exceeded 10 writes/min org limit | Use Retry-After header, batch deploys |
| 429 on fleet list | Monitoring polling too fast | Cache responses, poll every 30s max |
| Timeout on volume attach | Volume in another region | Verify region match before attach |
| 503 during region outage | Specific edge region down | Fail over to secondary region |
| 409 on machine update | Concurrent config change | Re-fetch machine state, retry with latest version |

## Resources

- [Fly.io Machines API](https://fly.io/docs/machines/api/)

## Next Steps

See `flyio-performance-tuning`.
