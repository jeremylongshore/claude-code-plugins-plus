---
name: cohere-rate-limits
description: |
  Implement Cohere rate limiting, backoff, and request queuing patterns.
  Use when handling 429 errors, implementing retry logic,
  or optimizing API request throughput for Cohere.
  Trigger with phrases like "cohere rate limit", "cohere throttling",
  "cohere 429", "cohere retry", "cohere backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Rate Limits

## Overview
Handle Cohere rate limits with exponential backoff, request queuing, and proactive throttling. Real rate limits from Cohere's documentation.

## Prerequisites
- `cohere-ai` SDK installed
- Understanding of async/await patterns

## Actual Cohere Rate Limits

| Key Type | Endpoint | Rate Limit | Monthly Limit |
|----------|----------|-----------|---------------|
| **Trial** | Chat | 20 calls/min | 1,000 total |
| **Trial** | Embed | 5 calls/min | 1,000 total |
| **Trial** | Rerank | 5 calls/min | 1,000 total |
| **Trial** | Classify | 5 calls/min | 1,000 total |
| **Production** | All endpoints | 1,000 calls/min | Unlimited |

Trial keys are free. Production keys require billing at [dashboard.cohere.com](https://dashboard.cohere.com).

## Instructions

### Step 1: Exponential Backoff with Jitter

```typescript
import { CohereError, CohereTimeoutError } from 'cohere-ai';

interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

const DEFAULT_RETRY: RetryConfig = {
  maxRetries: 5,
  baseDelayMs: 1000,
  maxDelayMs: 60_000,
};

async function withBackoff<T>(
  operation: () => Promise<T>,
  config = DEFAULT_RETRY
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === config.maxRetries) throw err;

      // Only retry on rate limits (429) and server errors (5xx)
      let shouldRetry = false;
      let retryAfterMs: number | undefined;

      if (err instanceof CohereError) {
        if (err.statusCode === 429) {
          shouldRetry = true;
          // Cohere returns Retry-After header (seconds)
          // SDK may expose this via err.headers
        } else if (err.statusCode && err.statusCode >= 500) {
          shouldRetry = true;
        }
      } else if (err instanceof CohereTimeoutError) {
        shouldRetry = true;
      }

      if (!shouldRetry) throw err;

      // Exponential delay with jitter
      const exponential = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * config.baseDelayMs;
      const delay = Math.min(exponential + jitter, config.maxDelayMs);

      console.warn(`Cohere retry ${attempt + 1}/${config.maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, retryAfterMs ?? delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 2: Request Queue (Concurrency-Limited)

```typescript
import PQueue from 'p-queue';

// Match rate limits: trial=20/min for chat, production=1000/min
function createCohereQueue(callsPerMinute: number) {
  return new PQueue({
    concurrency: 5,
    interval: 60_000,
    intervalCap: callsPerMinute,
  });
}

// Trial key queue
const trialChatQueue = createCohereQueue(20);
const trialEmbedQueue = createCohereQueue(5);

// Production key queue
const prodQueue = createCohereQueue(1000);

// Usage
async function queuedChat(params: any) {
  return trialChatQueue.add(() =>
    withBackoff(() => cohere.chat(params))
  );
}
```

### Step 3: Proactive Rate Tracking

```typescript
class RateLimitTracker {
  private windows: Map<string, number[]> = new Map();

  constructor(private limitsPerMinute: Record<string, number>) {}

  canProceed(endpoint: string): boolean {
    const limit = this.limitsPerMinute[endpoint] ?? 1000;
    const now = Date.now();
    const window = this.windows.get(endpoint) ?? [];

    // Remove entries older than 1 minute
    const active = window.filter(t => now - t < 60_000);
    this.windows.set(endpoint, active);

    return active.length < limit;
  }

  record(endpoint: string): void {
    const window = this.windows.get(endpoint) ?? [];
    window.push(Date.now());
    this.windows.set(endpoint, window);
  }

  waitTime(endpoint: string): number {
    const limit = this.limitsPerMinute[endpoint] ?? 1000;
    const window = this.windows.get(endpoint) ?? [];
    const now = Date.now();
    const active = window.filter(t => now - t < 60_000);

    if (active.length < limit) return 0;
    return 60_000 - (now - active[0]); // Wait until oldest entry expires
  }
}

// Trial key tracker
const tracker = new RateLimitTracker({
  chat: 20,
  embed: 5,
  rerank: 5,
  classify: 5,
});

// Use before each call
async function trackedEmbed(params: any) {
  const wait = tracker.waitTime('embed');
  if (wait > 0) {
    console.log(`Throttling embed: waiting ${wait}ms`);
    await new Promise(r => setTimeout(r, wait));
  }
  tracker.record('embed');
  return withBackoff(() => cohere.embed(params));
}
```

### Step 4: Batch-Aware Embedding

```typescript
// Embed supports up to 96 texts per call — maximize batch size to reduce calls
async function efficientEmbed(
  texts: string[],
  inputType: 'search_document' | 'search_query' = 'search_document'
): Promise<number[][]> {
  const BATCH_SIZE = 96; // Cohere max per request
  const allVectors: number[][] = [];

  for (let i = 0; i < texts.length; i += BATCH_SIZE) {
    const batch = texts.slice(i, i + BATCH_SIZE);

    const response = await trackedEmbed({
      model: 'embed-v4.0',
      texts: batch,
      inputType,
      embeddingTypes: ['float'],
    });

    allVectors.push(...response.embeddings.float);
  }

  return allVectors;
}

// 960 texts = 10 API calls (not 960)
const vectors = await efficientEmbed(largeTextArray);
```

## Cost-Aware Rate Limiting

For production keys, rate limits are per-minute but costs are per-token:

```typescript
class TokenBudget {
  private tokensUsed = 0;
  private readonly resetInterval: NodeJS.Timer;

  constructor(
    private maxTokensPerMinute: number,
    private alertCallback?: (used: number) => void
  ) {
    // Reset every minute
    this.resetInterval = setInterval(() => { this.tokensUsed = 0; }, 60_000);
  }

  canAfford(estimatedTokens: number): boolean {
    return this.tokensUsed + estimatedTokens <= this.maxTokensPerMinute;
  }

  record(actualTokens: number): void {
    this.tokensUsed += actualTokens;
    if (this.tokensUsed > this.maxTokensPerMinute * 0.8) {
      this.alertCallback?.(this.tokensUsed);
    }
  }

  dispose(): void {
    clearInterval(this.resetInterval);
  }
}
```

## Output
- Automatic retry with exponential backoff + jitter
- Concurrency-limited request queue matching Cohere rate limits
- Proactive throttling before hitting limits
- Batch-optimized embedding to minimize API calls

## Error Handling
| Scenario | Detection | Action |
|----------|-----------|--------|
| 429 from trial key | `CohereError.statusCode === 429` | Wait 60s, retry |
| 429 from prod key | Same | Backoff, check concurrency |
| Monthly limit hit (trial) | 429 with limit message | Upgrade to production key |
| Burst of requests | Queue depth > threshold | Add backpressure |

## Resources
- [Cohere Rate Limits](https://docs.cohere.com/docs/rate-limits)
- [Cohere API Keys](https://dashboard.cohere.com/api-keys)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For security configuration, see `cohere-security-basics`.
