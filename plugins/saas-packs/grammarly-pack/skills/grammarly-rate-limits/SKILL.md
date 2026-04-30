---
name: grammarly-rate-limits
description: 'Implement Grammarly rate limiting, backoff, and idempotency patterns.

  Use when handling rate limit errors, implementing retry logic,

  or optimizing API request throughput for Grammarly.

  Trigger with phrases like "grammarly rate limit", "grammarly throttling",

  "grammarly 429", "grammarly retry", "grammarly backoff".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- grammarly
- writing
compatibility: Designed for Claude Code
---
# Grammarly Rate Limits

## Overview

Grammarly's Text API enforces plan-dependent rate limits across its writing score, AI detection, and plagiarism endpoints. The plagiarism checker is asynchronous and requires polling, which adds complexity to rate management. Token endpoints are separately throttled at roughly 10 requests per hour, so credential rotation during high-throughput batch processing of documents (e.g., scanning an entire content library) requires careful token lifecycle management to avoid auth-layer 429s on top of API-layer throttling.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| Writing score | 100 req (Business) | 1 minute | Per API key |
| AI content detection | 60 req (Business) | 1 minute | Per API key |
| Plagiarism check (submit) | 30 req | 1 minute | Per API key |
| Plagiarism check (poll) | 120 req | 1 minute | Per API key |
| Token refresh | 10 req | 1 hour | Per client credentials |

## Rate Limiter Implementation

```typescript
class GrammarlyRateLimiter {
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

const scoreLimiter = new GrammarlyRateLimiter(90);
const plagiarismLimiter = new GrammarlyRateLimiter(25);
```

## Retry Strategy

```typescript
async function grammarlyRetry<T>(
  limiter: GrammarlyRateLimiter, fn: () => Promise<Response>, maxRetries = 3
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
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1500));
      continue;
    }
    throw new Error(`Grammarly API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function batchScoreDocuments(documents: string[], batchSize = 8) {
  const results: any[] = [];
  for (let i = 0; i < documents.length; i += batchSize) {
    const batch = documents.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(text => grammarlyRetry(scoreLimiter, () =>
        fetch("https://api.grammarly.com/ecosystem/api/v2/scores", {
          method: "POST", headers,
          body: JSON.stringify({ text }),
        })
      ))
    );
    results.push(...batchResults);
    if (i + batchSize < documents.length) await new Promise(r => setTimeout(r, 5000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 on writing score | Exceeded plan-tier per-minute cap | Reduce concurrency, use Retry-After |
| 429 on token refresh | More than 10 refreshes/hour | Cache token, refresh only on 401 |
| Plagiarism poll timeout | Result not ready after 60s | Increase poll interval to 10s, max 5 min |
| 413 on large document | Text exceeds 100K character limit | Split into sections, score individually |
| Empty score response | Text too short for analysis | Validate minimum 50 characters before submission |

## Resources

- [Grammarly Developer API](https://developer.grammarly.com/)

## Next Steps

See `grammarly-performance-tuning`.
