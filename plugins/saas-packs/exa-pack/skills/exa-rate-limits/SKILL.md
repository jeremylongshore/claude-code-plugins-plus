---
name: exa-rate-limits
description: |
  Implement Exa rate limiting, exponential backoff, and request queuing.
  Use when handling 429 errors, implementing retry logic,
  or optimizing API request throughput for Exa.
  Trigger with phrases like "exa rate limit", "exa throttling",
  "exa 429", "exa retry", "exa backoff", "exa QPS".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, api, rate-limiting]

---
# Exa Rate Limits

## Overview
Handle Exa API rate limits gracefully. Default limit is 10 QPS (queries per second) across all endpoints. Rate limit errors return HTTP 429 with a simple `{ "error": "rate limit exceeded" }` response. For higher limits, contact hello@exa.ai for Enterprise plans.

## Rate Limit Structure

| Endpoint | Default QPS | Notes |
|----------|-------------|-------|
| `/search` | 10 | Most endpoints share this limit |
| `/find-similar` | 10 | Same pool as search |
| `/contents` | 10 | Same pool |
| `/answer` | 10 | Same pool |
| Research API | Concurrent task limit | Long-running operations |

## Prerequisites
- `exa-js` SDK installed
- Understanding of async/await patterns

## Instructions

### Step 1: Exponential Backoff with Jitter
```typescript
import Exa from "exa-js";

const exa = new Exa(process.env.EXA_API_KEY);

async function withBackoff<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 32000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      const status = err.status || err.response?.status;
      // Only retry on 429 (rate limit) and 5xx (server errors)
      if (status !== 429 && (status < 500 || status >= 600)) throw err;
      if (attempt === config.maxRetries) throw err;

      // Exponential delay with random jitter to prevent thundering herd
      const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * 500;
      const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);

      console.log(`[Exa] ${status} — retry ${attempt + 1}/${config.maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage
const results = await withBackoff(() =>
  exa.searchAndContents("AI research", { numResults: 5, text: true })
);
```

### Step 2: Request Queue with Concurrency Control
```typescript
import PQueue from "p-queue";

// Limit to 8 concurrent requests (under the 10 QPS limit)
const exaQueue = new PQueue({
  concurrency: 8,
  interval: 1000,    // per second
  intervalCap: 10,   // max 10 per interval (matches Exa's QPS limit)
});

async function queuedSearch(query: string, opts: any = {}) {
  return exaQueue.add(() => exa.searchAndContents(query, opts));
}

// Batch many queries safely
async function batchSearch(queries: string[]) {
  const results = await Promise.all(
    queries.map(q => queuedSearch(q, { numResults: 5, text: true }))
  );
  return results;
}
```

### Step 3: Adaptive Rate Limiter
```typescript
class AdaptiveRateLimiter {
  private currentDelay = 100; // ms between requests
  private minDelay = 50;
  private maxDelay = 5000;
  private consecutiveSuccesses = 0;
  private lastRequestTime = 0;

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    const now = Date.now();
    const elapsed = now - this.lastRequestTime;
    if (elapsed < this.currentDelay) {
      await new Promise(r => setTimeout(r, this.currentDelay - elapsed));
    }

    try {
      this.lastRequestTime = Date.now();
      const result = await fn();
      this.consecutiveSuccesses++;

      // Speed up after 10 consecutive successes
      if (this.consecutiveSuccesses >= 10) {
        this.currentDelay = Math.max(this.minDelay, this.currentDelay * 0.8);
        this.consecutiveSuccesses = 0;
      }
      return result;
    } catch (err: any) {
      if (err.status === 429) {
        // Slow down on rate limit
        this.currentDelay = Math.min(this.maxDelay, this.currentDelay * 2);
        this.consecutiveSuccesses = 0;
        console.log(`[Exa] Rate limited. New delay: ${this.currentDelay}ms`);
      }
      throw err;
    }
  }
}

const limiter = new AdaptiveRateLimiter();

// Combine with backoff
const results = await withBackoff(() =>
  limiter.execute(() => exa.search("query", { numResults: 5 }))
);
```

### Step 4: Batch Processing with Rate Awareness
```typescript
async function processBatch(
  queries: string[],
  batchSize = 5,
  delayBetweenBatches = 1000
) {
  const allResults = [];

  for (let i = 0; i < queries.length; i += batchSize) {
    const batch = queries.slice(i, i + batchSize);

    // Process batch concurrently
    const batchResults = await Promise.all(
      batch.map(q => withBackoff(() =>
        exa.searchAndContents(q, { numResults: 3, text: true })
      ))
    );
    allResults.push(...batchResults);

    // Pause between batches to stay under rate limit
    if (i + batchSize < queries.length) {
      await new Promise(r => setTimeout(r, delayBetweenBatches));
    }

    console.log(`Processed ${Math.min(i + batchSize, queries.length)}/${queries.length}`);
  }

  return allResults;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 errors | Exceeding 10 QPS | Implement backoff + queue |
| Burst rejected | Too many simultaneous requests | Use `p-queue` with intervalCap |
| Batch job failures | No delay between batches | Add `delayBetweenBatches` |
| Inconsistent throttling | No jitter in retry | Add random jitter to prevent thundering herd |

## Examples

### Simple Retry Wrapper
```typescript
async function retrySearch(query: string, maxRetries = 3) {
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await exa.search(query, { numResults: 5 });
    } catch (err: any) {
      if (err.status !== 429 || i === maxRetries) throw err;
      await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
    }
  }
}
```

## Resources
- [Exa Rate Limits](https://docs.exa.ai/reference/rate-limits)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For security configuration, see `exa-security-basics`.
