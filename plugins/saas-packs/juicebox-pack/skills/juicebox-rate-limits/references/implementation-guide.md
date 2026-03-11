# Juicebox Rate Limits - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Understand Rate Limit Headers
```typescript
// Juicebox returns these headers with every response
interface RateLimitHeaders {
  'x-ratelimit-limit': string;      // Max requests per window
  'x-ratelimit-remaining': string;  // Remaining requests
  'x-ratelimit-reset': string;      // Unix timestamp when limit resets
  'retry-after'?: string;           // Seconds to wait (only on 429)
}

function parseRateLimitHeaders(headers: Headers) {
  return {
    limit: parseInt(headers.get('x-ratelimit-limit') || '0'),
    remaining: parseInt(headers.get('x-ratelimit-remaining') || '0'),
    reset: new Date(parseInt(headers.get('x-ratelimit-reset') || '0') * 1000),
    retryAfter: parseInt(headers.get('retry-after') || '0')
  };
}
```

### Step 2: Implement Rate Limiter
```typescript
// lib/rate-limiter.ts
export class RateLimiter {
  private queue: Array<() => Promise<void>> = [];
  private processing = false;
  private lastRequestTime = 0;
  private minInterval: number;

  constructor(requestsPerMinute: number) {
    this.minInterval = 60000 / requestsPerMinute;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await fn();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });

      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.processing || this.queue.length === 0) return;
    this.processing = true;

    while (this.queue.length > 0) {
      const now = Date.now();
      const elapsed = now - this.lastRequestTime;

      if (elapsed < this.minInterval) {
        await sleep(this.minInterval - elapsed);
      }

      const task = this.queue.shift();
      if (task) {
        this.lastRequestTime = Date.now();
        await task();
      }
    }

    this.processing = false;
  }
}
```

### Step 3: Add Exponential Backoff
```typescript
// lib/backoff.ts
export async function withExponentialBackoff<T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number;
    baseDelay?: number;
    maxDelay?: number;
  } = {}
): Promise<T> {
  const { maxRetries = 5, baseDelay = 1000, maxDelay = 60000 } = options;

  let lastError: Error;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      lastError = error;

      if (error.code === 'RATE_LIMITED') {
        const retryAfter = error.retryAfter || 0;
        const backoffDelay = Math.min(
          baseDelay * Math.pow(2, attempt),
          maxDelay
        );
        const delay = Math.max(retryAfter * 1000, backoffDelay);

        console.log(`Rate limited. Retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries})`);
        await sleep(delay);
        continue;
      }

      throw error;
    }
  }

  throw lastError!;
}
```

### Step 4: Implement Quota Tracking
```typescript
// lib/quota-tracker.ts
export class QuotaTracker {
  private dailyRequests = 0;
  private dailyResetTime: Date;

  constructor(private dailyLimit: number) {
    this.dailyResetTime = this.getNextMidnight();
  }

  async checkQuota(): Promise<boolean> {
    this.maybeResetDaily();
    return this.dailyRequests < this.dailyLimit;
  }

  recordRequest() {
    this.dailyRequests++;
  }

  getRemainingQuota(): number {
    this.maybeResetDaily();
    return this.dailyLimit - this.dailyRequests;
  }

  private maybeResetDaily() {
    if (new Date() > this.dailyResetTime) {
      this.dailyRequests = 0;
      this.dailyResetTime = this.getNextMidnight();
    }
  }
}
```

## Error Handling

| Scenario | Strategy |
|----------|----------|
| 429 with Retry-After | Wait exact duration |
| 429 without Retry-After | Exponential backoff |
| Approaching limit | Proactive throttling |
| Daily quota exhausted | Queue for next day |
