---
name: glean-rate-limits
description: |
  Glean Indexing API: ~100 requests/min per token.
  Trigger: "glean rate limits", "rate-limits".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Rate Limits

## Overview

Glean's APIs split into two tiers: the Indexing API for pushing documents into the search corpus, and the Client API for executing searches. The Indexing API handles bulk document ingestion at approximately 100 requests per minute, while search queries are capped at 60 per minute per token. Organizations indexing large knowledge bases (100K+ documents from Confluence, Notion, or internal wikis) must implement careful batching to avoid 429 responses that can stall multi-hour ingestion pipelines.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| Indexing - single document | 100 req | 1 minute | Per API token |
| Indexing - bulk (100 docs/req) | 20 req | 1 minute | Per API token |
| Search queries | 60 req | 1 minute | Per API token |
| People search | 30 req | 1 minute | Per API token |
| Entity extraction | 40 req | 1 minute | Per API token |

## Rate Limiter Implementation

```typescript
class GleanRateLimiter {
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

const indexLimiter = new GleanRateLimiter(18);  // buffer under 20 bulk/min
const searchLimiter = new GleanRateLimiter(50);
```

## Retry Strategy

```typescript
async function gleanRetry<T>(
  limiter: GleanRateLimiter, fn: () => Promise<Response>, maxRetries = 4
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    await limiter.acquire();
    const res = await fn();
    if (res.ok) return res.json();
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "30", 10);
      const jitter = Math.random() * 5000;
      await new Promise(r => setTimeout(r, retryAfter * 1000 + jitter));
      continue;
    }
    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 2000));
      continue;
    }
    throw new Error(`Glean API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function bulkIndexDocuments(docs: any[], batchSize = 100) {
  const results: any[] = [];
  for (let i = 0; i < docs.length; i += batchSize) {
    const batch = docs.slice(i, i + batchSize);
    const result = await gleanRetry(indexLimiter, () =>
      fetch(`${GLEAN_BASE}/api/index/v1/bulkindexdocuments`, {
        method: "POST", headers,
        body: JSON.stringify({ uploadId: `batch-${i}`, documents: batch }),
      })
    );
    results.push(result);
    if (i + batchSize < docs.length) await new Promise(r => setTimeout(r, 4000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 on bulk index | Exceeded 20 bulk req/min | Space batches 4s apart, use Retry-After |
| 413 Payload Too Large | Batch > 100 docs or > 10MB | Split into smaller batches |
| Search 429 | Monitoring dashboard polling too fast | Cache search results for 30s |
| Partial index failure | Some docs rejected in bulk | Check response `failedDocuments` array, retry those |
| 401 token expired | Rotating API credentials | Refresh token before long ingestion runs |

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps

See `glean-performance-tuning`.
