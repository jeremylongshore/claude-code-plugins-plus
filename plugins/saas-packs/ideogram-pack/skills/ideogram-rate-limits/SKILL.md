---
name: ideogram-rate-limits
description: |
  Implement Ideogram rate limiting, backoff, and request queuing patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Ideogram.
  Trigger with phrases like "ideogram rate limit", "ideogram throttling",
  "ideogram 429", "ideogram retry", "ideogram backoff", "ideogram queue".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, api, rate-limiting]

---
# Ideogram Rate Limits

## Overview
Handle Ideogram's rate limits with exponential backoff, request queuing, and concurrency control. Ideogram enforces a default limit of **10 in-flight requests** (concurrent, not per-minute). Image generation takes 5-15 seconds per call, so this limit can be hit quickly during batch operations.

## Prerequisites
- `IDEOGRAM_API_KEY` configured
- Understanding of async patterns
- `p-queue` npm package (optional, for queue-based approach)

## Ideogram Rate Limit Model

| Aspect | Detail |
|--------|--------|
| Type | Concurrent in-flight requests |
| Default limit | 10 simultaneous requests |
| Error code | HTTP 429 |
| Retry header | Not guaranteed -- use exponential backoff |
| Higher limits | Contact `partnership@ideogram.ai` |
| Generation time | 5-15s per image (varies by model/resolution) |

## Instructions

### Step 1: Exponential Backoff with Jitter
```typescript
async function withBackoff<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseMs: 1000, maxMs: 30000, jitterMs: 500 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      if (attempt === config.maxRetries) throw err;

      const status = err.status ?? err.response?.status;
      // Only retry on 429 (rate limited) or 5xx (server error)
      if (status && status !== 429 && status < 500) throw err;

      const exponential = config.baseMs * Math.pow(2, attempt);
      const jitter = Math.random() * config.jitterMs;
      const delay = Math.min(exponential + jitter, config.maxMs);

      console.warn(`Rate limited (attempt ${attempt + 1}/${config.maxRetries}). Waiting ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 2: Concurrency-Limited Queue
```typescript
import PQueue from "p-queue";

// Ideogram allows 10 in-flight -- use 8 to leave headroom
const ideogramQueue = new PQueue({ concurrency: 8 });

async function queuedGenerate(prompt: string, options: any = {}) {
  return ideogramQueue.add(async () => {
    const response = await fetch("https://api.ideogram.ai/generate", {
      method: "POST",
      headers: {
        "Api-Key": process.env.IDEOGRAM_API_KEY!,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_request: { prompt, model: "V_2", ...options },
      }),
    });

    if (response.status === 429) {
      throw Object.assign(new Error("Rate limited"), { status: 429 });
    }
    if (!response.ok) throw new Error(`Generate failed: ${response.status}`);
    return response.json();
  });
}

// Process 50 prompts safely -- queue manages concurrency
const prompts = Array.from({ length: 50 }, (_, i) => `Design variant ${i + 1}`);
const results = await Promise.all(prompts.map(p => queuedGenerate(p)));
```

### Step 3: Token Bucket Rate Limiter
```typescript
class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private maxTokens: number = 10,
    private refillRate: number = 1, // tokens per second
  ) {
    this.tokens = maxTokens;
    this.lastRefill = Date.now();
  }

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens > 0) {
      this.tokens--;
      return;
    }
    // Wait for next token
    const waitMs = (1 / this.refillRate) * 1000;
    await new Promise(r => setTimeout(r, waitMs));
    this.refill();
    this.tokens--;
  }

  private refill() {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }
}

const bucket = new TokenBucket(10, 1);

async function throttledGenerate(prompt: string) {
  await bucket.acquire();
  return queuedGenerate(prompt);
}
```

### Step 4: Batch with Progress Tracking
```typescript
async function batchGenerate(
  prompts: string[],
  onProgress?: (done: number, total: number) => void
) {
  const results: any[] = [];
  const errors: { prompt: string; error: Error }[] = [];

  for (let i = 0; i < prompts.length; i++) {
    try {
      const result = await withBackoff(() => queuedGenerate(prompts[i]));
      results.push(result);
    } catch (err) {
      errors.push({ prompt: prompts[i], error: err as Error });
    }
    onProgress?.(i + 1, prompts.length);
  }

  console.log(`Batch complete: ${results.length} success, ${errors.length} failed`);
  return { results, errors };
}
```

## Error Handling
| Scenario | Detection | Action |
|----------|-----------|--------|
| 429 received | HTTP status | Exponential backoff + retry |
| All retries exhausted | Max attempts reached | Log and skip, continue batch |
| Burst spike | Queue depth > 20 | Pause new submissions |
| Credits exhausted | 402 status | Alert, stop batch immediately |

## Output
- Reliable API calls with automatic retry on 429
- Concurrency-controlled request queue
- Token bucket for sustained throughput
- Batch processing with progress and error tracking

## Resources
- [Ideogram API Overview](https://developer.ideogram.ai/ideogram-api/api-overview)
- [p-queue](https://github.com/sindresorhus/p-queue)
- Enterprise limits: `partnership@ideogram.ai`

## Next Steps
For security configuration, see `ideogram-security-basics`.
