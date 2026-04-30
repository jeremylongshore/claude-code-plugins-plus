---
name: linktree-rate-limits
description: 'Rate Limits for Linktree.

  Trigger: "linktree rate limits".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- linktree
- social
compatibility: Designed for Claude Code
---
# Linktree Rate Limits

## Overview

Linktree's API enforces rate limits per OAuth token, with analytics endpoints throttled more aggressively than profile management operations. Agencies managing dozens of creator profiles need to stagger link updates and analytics pulls across accounts to avoid hitting per-token and global IP-based limits. Bulk link reordering and analytics export during campaign launches are the most common rate-limit triggers, especially when synchronizing link performance data with external dashboards on short polling intervals.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| Profile read/update | 60 req | 1 minute | Per OAuth token |
| Link create/update/delete | 30 req | 1 minute | Per OAuth token |
| Analytics summary | 20 req | 1 minute | Per OAuth token |
| Analytics detailed (per-link) | 10 req | 1 minute | Per OAuth token |
| Webhook management | 10 req | 1 minute | Per OAuth token |

## Rate Limiter Implementation

```typescript
class LinktreeRateLimiter {
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

const linkLimiter = new LinktreeRateLimiter(25);
const analyticsLimiter = new LinktreeRateLimiter(8);
```

## Retry Strategy

```typescript
async function linktreeRetry<T>(
  limiter: LinktreeRateLimiter, fn: () => Promise<Response>, maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    await limiter.acquire();
    const res = await fn();
    if (res.ok) return res.json();
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "30", 10);
      const jitter = Math.random() * 2000;
      await new Promise(r => setTimeout(r, retryAfter * 1000 + jitter));
      continue;
    }
    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1500));
      continue;
    }
    throw new Error(`Linktree API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function batchUpdateLinks(profileId: string, links: any[], batchSize = 5) {
  const results: any[] = [];
  for (let i = 0; i < links.length; i += batchSize) {
    const batch = links.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(link => linktreeRetry(linkLimiter, () =>
        fetch(`${BASE}/api/v1/profiles/${profileId}/links/${link.id}`, {
          method: "PATCH", headers,
          body: JSON.stringify({ title: link.title, url: link.url }),
        })
      ))
    );
    results.push(...batchResults);
    if (i + batchSize < links.length) await new Promise(r => setTimeout(r, 10_000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 on link updates | Exceeded 30 writes/min per token | Reduce batch concurrency to 3 |
| 429 on analytics | Polling per-link stats too frequently | Cache analytics, refresh every 5 min |
| 401 token expired | OAuth token TTL exceeded | Refresh token before batch operations |
| 404 on link delete | Link already removed or archived | Skip gracefully, log warning |
| IP-level 429 | Multiple tokens from same IP | Spread requests across proxy endpoints |

## Resources

- [Linktree Developer Documentation](https://linktr.ee/marketplace/developer)

## Next Steps

See `linktree-performance-tuning`.
