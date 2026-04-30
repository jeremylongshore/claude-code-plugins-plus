---
name: openevidence-rate-limits
description: 'Rate Limits for OpenEvidence.

  Trigger: "openevidence rate limits".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openevidence
- healthcare
compatibility: Designed for Claude Code
---
# OpenEvidence Rate Limits

## Overview

OpenEvidence's clinical decision support API enforces strict rate limits to ensure reliable evidence retrieval for healthcare applications. Clinical query endpoints are throttled per API key, with lower limits on evidence synthesis calls that involve AI-powered literature analysis. In clinical settings, rate limiting directly impacts patient care workflows, so implementations must prioritize graceful degradation over retry storms. Batch research queries during off-peak hours and cache evidence summaries aggressively since medical literature changes infrequently.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| Clinical query | 30 req | 1 minute | Per API key |
| Evidence synthesis | 10 req | 1 minute | Per API key |
| Literature search | 60 req | 1 minute | Per API key |
| Citation retrieval | 120 req | 1 minute | Per API key |
| Bulk evidence export | 5 req | 1 hour | Per API key |

## Rate Limiter Implementation

```typescript
class OpenEvidenceRateLimiter {
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

const queryLimiter = new OpenEvidenceRateLimiter(25);
const synthesisLimiter = new OpenEvidenceRateLimiter(8);
```

## Retry Strategy

```typescript
async function openEvidenceRetry<T>(
  limiter: OpenEvidenceRateLimiter, fn: () => Promise<Response>, maxRetries = 3
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
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 3000));
      continue;
    }
    throw new Error(`OpenEvidence API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function batchClinicalQueries(queries: string[], batchSize = 5) {
  const results: any[] = [];
  for (let i = 0; i < queries.length; i += batchSize) {
    const batch = queries.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(q => openEvidenceRetry(queryLimiter, () =>
        fetch(`${OE_BASE}/api/v1/clinical/query`, {
          method: "POST", headers,
          body: JSON.stringify({ question: q, includeEvidence: true }),
        })
      ))
    );
    results.push(...batchResults);
    if (i + batchSize < queries.length) await new Promise(r => setTimeout(r, 12_000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 on clinical query | Exceeded 30 req/min query cap | Queue queries, return cached if available |
| 429 on synthesis | Synthesis limit (10/min) is strict | Pre-cache common drug interaction queries |
| Synthesis timeout | Complex multi-study analysis | Set 120s timeout, poll async endpoint |
| 401 key expired | API key rotation missed | Automate key rotation with 7-day buffer |
| Stale evidence | Cached result older than 30 days | Set TTL on cache, re-query on expiry |

## Resources

- [OpenEvidence Platform](https://www.openevidence.com)

## Next Steps

See `openevidence-performance-tuning`.
