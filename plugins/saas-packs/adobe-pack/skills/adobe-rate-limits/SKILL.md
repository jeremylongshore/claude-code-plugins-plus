---
name: adobe-rate-limits
description: |
  Implement Adobe API rate limiting, backoff, and quota management across
  Firefly, PDF Services, Photoshop, and I/O Events APIs.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Adobe.
  Trigger with phrases like "adobe rate limit", "adobe throttling",
  "adobe 429", "adobe retry", "adobe backoff", "adobe quota".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Rate Limits

## Overview

Handle Adobe API rate limits gracefully with exponential backoff, `Retry-After` header support, and proactive quota management. Each Adobe API has different rate limits.

## Prerequisites

- Adobe SDK installed and authenticated
- Understanding of async/await patterns
- Awareness of your API tier and entitlements

## Instructions

### Step 1: Know Your Rate Limits by API

| API | Limit | Scope | Response |
|-----|-------|-------|----------|
| **Firefly API** | ~20 req/min (trial), higher on paid | Per api-key | `429` + `Retry-After` |
| **PDF Services** | 500 tx/month (free), unlimited (paid) | Per credential | `429` or `QUOTA_EXCEEDED` |
| **Photoshop API** | Varies by entitlement | Per api-key | `429` + `Retry-After` |
| **Lightroom API** | Varies by entitlement | Per api-key | `429` + `Retry-After` |
| **I/O Events Publishing** | 3,000 req/5sec | Per api-key | `429` + `Retry-After` |
| **Analytics 2.0 API** | 12 req/6sec per user (~120 req/min) | Per user | `429` + `Retry-After` |
| **IMS Token Endpoint** | ~100 req/min | Per client_id | `429` |

### Step 2: Implement Retry-After Aware Backoff

```typescript
// src/adobe/rate-limiter.ts
import { AdobeApiError } from './client';

export async function withAdobeBackoff<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 60_000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;

      // Only retry on 429 and 5xx
      const status = error.status || error.response?.status;
      if (status && status !== 429 && (status < 500 || status >= 600)) throw error;

      // Honor Adobe's Retry-After header (seconds)
      let delay: number;
      if (error.retryAfter) {
        delay = error.retryAfter * 1000;
      } else {
        // Exponential backoff with jitter
        const exponential = config.baseDelayMs * Math.pow(2, attempt);
        const jitter = Math.random() * config.baseDelayMs;
        delay = Math.min(exponential + jitter, config.maxDelayMs);
      }

      console.warn(
        `Adobe rate limited (attempt ${attempt + 1}/${config.maxRetries}). ` +
        `Waiting ${(delay / 1000).toFixed(1)}s...`
      );
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 3: Proactive Rate Tracking

```typescript
// Track remaining quota from response headers
class AdobeRateTracker {
  private remaining: number = Infinity;
  private resetAt: number = 0;

  updateFromResponse(response: Response): void {
    const remaining = response.headers.get('Retry-After');
    // Adobe primarily uses Retry-After rather than X-RateLimit-* headers
    // Some APIs (Analytics, Events) include additional rate info
    if (remaining) {
      this.remaining = 0;
      this.resetAt = Date.now() + parseInt(remaining) * 1000;
    }
  }

  async waitIfNeeded(): Promise<void> {
    if (this.remaining <= 0 && Date.now() < this.resetAt) {
      const waitMs = this.resetAt - Date.now();
      console.log(`Proactively waiting ${waitMs}ms for Adobe rate limit reset`);
      await new Promise(r => setTimeout(r, waitMs));
      this.remaining = Infinity; // Reset after wait
    }
  }
}
```

### Step 4: Queue-Based Rate Limiting for Batch Operations

```typescript
import PQueue from 'p-queue';

// Configure queue per API — match to known rate limits
const fireflyQueue = new PQueue({
  concurrency: 2,        // Max concurrent requests
  interval: 3000,        // Time window (ms)
  intervalCap: 1,        // Max requests per interval
});

const pdfServicesQueue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 5,
});

const eventsQueue = new PQueue({
  concurrency: 10,
  interval: 5000,
  intervalCap: 3000,     // Match Adobe's 3000/5sec limit
});

// Usage
async function batchFireflyGenerate(prompts: string[]) {
  const results = await Promise.all(
    prompts.map(prompt =>
      fireflyQueue.add(() =>
        withAdobeBackoff(() => generateImage({ prompt }))
      )
    )
  );
  return results;
}
```

### Step 5: PDF Services Transaction Monitoring

```typescript
// Track monthly PDF Services usage against free tier limit
class PdfServicesQuotaTracker {
  private transactionsUsed = 0;
  private readonly monthlyLimit: number;

  constructor(tier: 'free' | 'paid' = 'free') {
    this.monthlyLimit = tier === 'free' ? 500 : Infinity;
  }

  recordTransaction(): void {
    this.transactionsUsed++;
    const remaining = this.monthlyLimit - this.transactionsUsed;

    if (remaining <= 50) {
      console.warn(`PDF Services: ${remaining} transactions remaining this month`);
    }
    if (remaining <= 0) {
      throw new Error('PDF Services monthly quota exceeded. Upgrade plan or wait for reset.');
    }
  }

  getUsage(): { used: number; limit: number; remaining: number } {
    return {
      used: this.transactionsUsed,
      limit: this.monthlyLimit,
      remaining: Math.max(0, this.monthlyLimit - this.transactionsUsed),
    };
  }
}
```

## Output

- Retry logic that honors Adobe `Retry-After` headers
- Per-API queue-based rate limiting for batch operations
- Monthly transaction tracking for PDF Services free tier
- Proactive backpressure before hitting limits

## Error Handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| Single 429 | `Retry-After` header | Wait specified seconds, retry |
| Sustained 429s | Multiple retries fail | Reduce concurrency; check tier |
| PDF `QUOTA_EXCEEDED` | Monthly limit hit | Upgrade tier or wait for reset |
| Events 429 | 3000/5sec exceeded | Reduce batch size or add queue |

## Resources

- [Adobe Events API Rate Limits](https://developer.adobe.com/events/docs/guides/api/eventsingress-api)
- [Adobe Analytics API FAQ](https://developer.adobe.com/analytics-apis/docs/2.0/guides/faq/)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `adobe-security-basics`.
