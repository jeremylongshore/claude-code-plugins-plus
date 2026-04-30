---
name: lucidchart-rate-limits
description: 'Rate Limits for Lucidchart.

  Trigger: "lucidchart rate limits".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lucidchart
- diagramming
compatibility: Designed for Claude Code
---
# Lucidchart Rate Limits

## Overview

Lucidchart's API enforces per-OAuth-token rate limits, with document mutation operations (creating shapes, updating pages, modifying text) throttled more aggressively than read-only document listing. Automations that programmatically generate architecture diagrams or org charts from external data sources can easily exceed write limits when placing dozens of shapes and connectors in a single batch. Image export endpoints carry additional latency due to server-side rendering, making export-heavy workflows the most common throttling bottleneck.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| List documents | 120 req | 1 minute | Per OAuth token |
| Get document / pages | 60 req | 1 minute | Per OAuth token |
| Create/update shapes | 30 req | 1 minute | Per OAuth token |
| Export to PNG/PDF | 10 req | 1 minute | Per OAuth token |
| Create document | 15 req | 1 minute | Per OAuth token |

## Rate Limiter Implementation

```typescript
class LucidRateLimiter {
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

const writeLimiter = new LucidRateLimiter(25);
const exportLimiter = new LucidRateLimiter(8);
```

## Retry Strategy

```typescript
async function lucidRetry<T>(
  limiter: LucidRateLimiter, fn: () => Promise<Response>, maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    await limiter.acquire();
    const res = await fn();
    if (res.ok) return res.json();
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "20", 10);
      const jitter = Math.random() * 2000;
      await new Promise(r => setTimeout(r, retryAfter * 1000 + jitter));
      continue;
    }
    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 2000));
      continue;
    }
    throw new Error(`Lucidchart API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function batchCreateShapes(docId: string, pageId: string, shapes: any[], batchSize = 5) {
  const results: any[] = [];
  for (let i = 0; i < shapes.length; i += batchSize) {
    const batch = shapes.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(shape => lucidRetry(writeLimiter, () =>
        fetch(`${LUCID_BASE}/documents/${docId}/pages/${pageId}/shapes`, {
          method: "POST", headers,
          body: JSON.stringify(shape),
        })
      ))
    );
    results.push(...batchResults);
    if (i + batchSize < shapes.length) await new Promise(r => setTimeout(r, 8000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 on shape creation | Exceeded 30 writes/min token limit | Batch shapes, space 3s apart |
| 429 on PNG export | Export limit (10/min) is very low | Queue exports with 8s spacing |
| 408 on large document | Export rendering timeout | Request single page, not full doc |
| 401 token expired | OAuth token TTL exceeded | Refresh token before batch operations |
| 409 concurrent edit | Another user editing same page | Retry after 5s with fresh page version |

## Resources

- [Lucid Developer Portal](https://developer.lucid.co/reference/overview)

## Next Steps

See `lucidchart-performance-tuning`.
