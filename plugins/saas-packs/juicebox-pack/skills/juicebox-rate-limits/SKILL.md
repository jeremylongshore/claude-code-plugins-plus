---
name: juicebox-rate-limits
description: |
  Implement Juicebox rate limiting.
  Trigger: "juicebox rate limit", "juicebox 429", "juicebox throttle".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Rate Limits

## Overview

Juicebox's AI-powered data analysis API enforces plan-tiered rate limits across dataset uploads, analysis triggers, and result retrieval. Heavy analytical workloads like running comparative analyses across multiple datasets or batch-processing survey results hit the analysis trigger limit first. The enrichment endpoints for augmenting datasets with external data sources have separate, lower caps, making it essential to prioritize enrichment calls and batch analysis runs during off-peak windows.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| Dataset upload | 20 req | 1 minute | Per API key |
| Analysis trigger | 30 req | 1 minute | Per API key |
| Result retrieval | 120 req | 1 minute | Per API key |
| Data enrichment | 15 req | 1 minute | Per API key |
| Export download | 10 req | 1 minute | Per API key |

## Rate Limiter Implementation

```typescript
class JuiceboxRateLimiter {
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

const analysisLimiter = new JuiceboxRateLimiter(25);
const enrichLimiter = new JuiceboxRateLimiter(12);
```

## Retry Strategy

```typescript
async function juiceboxRetry<T>(
  limiter: JuiceboxRateLimiter, fn: () => Promise<Response>, maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    await limiter.acquire();
    const res = await fn();
    if (res.ok) return res.json();
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "15", 10);
      const jitter = Math.random() * 3000;
      await new Promise(r => setTimeout(r, retryAfter * 1000 + jitter));
      continue;
    }
    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 2000));
      continue;
    }
    throw new Error(`Juicebox API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function batchAnalyzeDatasets(datasetIds: string[], query: string, batchSize = 5) {
  const results: any[] = [];
  for (let i = 0; i < datasetIds.length; i += batchSize) {
    const batch = datasetIds.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(id => juiceboxRetry(analysisLimiter, () =>
        fetch(`${BASE}/api/v1/datasets/${id}/analyze`, {
          method: "POST", headers,
          body: JSON.stringify({ query }),
        })
      ))
    );
    results.push(...batchResults);
    if (i + batchSize < datasetIds.length) await new Promise(r => setTimeout(r, 8000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 on analysis trigger | Exceeded 30 req/min analysis cap | Queue analyses, space 3s apart |
| 429 on enrichment | Enrichment limit (15/min) is lowest | Batch enrichments separately with wider spacing |
| Upload timeout | Dataset exceeds 50MB | Compress CSV, use chunked upload endpoint |
| Analysis still processing | Complex query on large dataset | Poll status every 10s, timeout at 10 min |
| 403 on export | Plan does not include export feature | Verify plan tier supports data export |

## Resources

- [Juicebox API Documentation](https://docs.juicebox.ai/)

## Next Steps

See `juicebox-performance-tuning`.
