---
name: perplexity-rate-limits
description: |
  Implement Perplexity rate limiting, backoff, and request queuing.
  Use when handling 429 errors, implementing retry logic,
  or optimizing API request throughput for Perplexity Sonar.
  Trigger with phrases like "perplexity rate limit", "perplexity throttling",
  "perplexity 429", "perplexity retry", "perplexity backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, api]

---
# Perplexity Rate Limits

## Overview
Handle Perplexity Sonar API rate limits. Perplexity uses a leaky bucket algorithm: burst capacity is available, with tokens refilling continuously at your assigned rate. Rate limits are based on requests per minute (RPM).

## Rate Limit Tiers

| Tier | RPM | Notes |
|------|-----|-------|
| Free / Starter | 50 | Default for new API keys |
| Search API | ~3 req/sec | Per-endpoint limit |
| Higher tiers | Contact sales | Custom limits available |

Rate limits apply per API key, not per model. Using `sonar-pro` counts against the same RPM as `sonar`.

## Prerequisites
- `PERPLEXITY_API_KEY` set
- Understanding of HTTP 429 responses

## Instructions

### Step 1: Exponential Backoff with Jitter
```typescript
async function withExponentialBackoff<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 30000, jitterMs: 500 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;

      const status = error.status || error.response?.status;
      // Only retry on 429 (rate limit) and 5xx (server errors)
      if (status && status !== 429 && status < 500) throw error;

      const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * config.jitterMs;
      const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);

      console.warn(`[Perplexity] ${status || "error"} — retry ${attempt + 1}/${config.maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage
const result = await withExponentialBackoff(() =>
  perplexity.chat.completions.create({
    model: "sonar",
    messages: [{ role: "user", content: "test query" }],
  })
);
```

### Step 2: Queue-Based Rate Limiting
```typescript
import PQueue from "p-queue";

// 50 RPM = ~0.83 req/sec. Set intervalCap=1, interval=1200ms for safety.
const perplexityQueue = new PQueue({
  concurrency: 3,
  interval: 1200,
  intervalCap: 1,
});

async function queuedSearch(query: string, model = "sonar") {
  return perplexityQueue.add(() =>
    withExponentialBackoff(() =>
      perplexity.chat.completions.create({
        model,
        messages: [{ role: "user", content: query }],
      })
    )
  );
}

// Batch queries are automatically rate-limited
const queries = ["query 1", "query 2", "query 3", "query 4", "query 5"];
const results = await Promise.all(queries.map((q) => queuedSearch(q)));
```

### Step 3: Token Bucket Implementation (No Dependencies)
```typescript
class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private maxTokens: number = 50,
    private refillRate: number = 50 / 60  // 50 per minute = 0.83/sec
  ) {
    this.tokens = maxTokens;
    this.lastRefill = Date.now();
  }

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens >= 1) {
      this.tokens -= 1;
      return;
    }
    // Wait until a token is available
    const waitMs = (1 / this.refillRate) * 1000;
    await new Promise((r) => setTimeout(r, waitMs));
    this.refill();
    this.tokens -= 1;
  }

  private refill() {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }

  get available(): number {
    this.refill();
    return Math.floor(this.tokens);
  }
}

const bucket = new TokenBucket(50, 50 / 60);

async function rateLimitedSearch(query: string) {
  await bucket.acquire();
  return perplexity.chat.completions.create({
    model: "sonar",
    messages: [{ role: "user", content: query }],
  });
}
```

### Step 4: Python Rate Limiting
```python
import time, asyncio
from collections import deque

class RateLimiter:
    def __init__(self, rpm: int = 50):
        self.rpm = rpm
        self.window = deque()

    def wait_if_needed(self):
        now = time.time()
        # Remove timestamps older than 60 seconds
        while self.window and self.window[0] < now - 60:
            self.window.popleft()
        if len(self.window) >= self.rpm:
            sleep_time = 60 - (now - self.window[0])
            time.sleep(max(0, sleep_time))
        self.window.append(time.time())

limiter = RateLimiter(rpm=50)

def rate_limited_search(client, query: str, model: str = "sonar"):
    limiter.wait_if_needed()
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": query}],
    )
```

## Error Handling
| Signal | Meaning | Action |
|--------|---------|--------|
| HTTP 429 | RPM exceeded | Backoff and retry |
| `Retry-After` header | Seconds until reset | Honor this value exactly |
| Repeated 429s | Sustained overload | Reduce concurrency or add queue |
| 429 on burst | Bucket empty | Space requests 1.2s apart |

## Output
- Automatic retry with exponential backoff and jitter
- Queue-based rate limiting for batch operations
- Token bucket for fine-grained control
- Python rate limiter for synchronous code

## Resources
- [Perplexity Rate Limits](https://docs.perplexity.ai/guides/rate-limits)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)

## Next Steps
For security configuration, see `perplexity-security-basics`.
