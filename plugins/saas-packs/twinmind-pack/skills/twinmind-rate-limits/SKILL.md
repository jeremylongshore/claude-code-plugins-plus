---
name: twinmind-rate-limits
description: |
  Implement TwinMind rate limiting, backoff, and optimization patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for TwinMind.
  Trigger with phrases like "twinmind rate limit", "twinmind throttling",
  "twinmind 429", "twinmind retry", "twinmind backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Rate Limits

## Overview
Handle TwinMind rate limits gracefully with exponential backoff and request optimization.

## Prerequisites
- TwinMind API access (Pro/Enterprise)
- Understanding of async/await patterns
- Familiarity with rate limiting concepts

## Instructions

### Step 1: Understand Rate Limit Tiers

| Tier | Audio Hours/Month | API Requests/Min | Concurrent Transcriptions | Burst |
|------|-------------------|------------------|--------------------------|-------|
| Free | Unlimited | 30 | 1 | 5 |
| Pro ($10/mo) | Unlimited | 60 | 3 | 15 |
| Enterprise | Unlimited | 300 | 10 | 50 |

**Key Limits:**
- Transcription: Based on audio duration ($0.23/hour with Ear-3)
- AI Operations: Token-based (2M context for Pro)
- Summarization: 10/minute (Free), 30/minute (Pro)
- Memory Search: 60/minute (Free), 300/minute (Pro)

### Step 2: Implement Exponential Backoff with Jitter

```typescript
// src/twinmind/rate-limit.ts
interface RateLimitConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterMs: number;
}

const defaultConfig: RateLimitConfig = {
  maxRetries: 5,
  baseDelayMs: 1000,  # 1000: 1 second in ms
  maxDelayMs: 60000, // Max 1 minute  # 60000: 1 minute in ms
  jitterMs: 500,  # HTTP 500 Internal Server Error
};

export async function withRateLimit<T>(
  operation: () => Promise<T>,
  config: Partial<RateLimitConfig> = {}
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs, jitterMs } = {
    ...defaultConfig,
    ...config,
  };

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === maxRetries) throw error;

      const status = error.response?.status;
      if (status !== 429 && status !== 503) throw error; // Only retry on rate limits  # 503: HTTP 429 Too Many Requests

      // Check Retry-After header
      const retryAfter = error.response?.headers?.['retry-after'];
      let delay: number;

      if (retryAfter) {
        delay = parseInt(retryAfter) * 1000;  # 1 second in ms
      } else {
        // Exponential backoff with jitter
        const exponential = baseDelayMs * Math.pow(2, attempt);
        const jitter = Math.random() * jitterMs;
        delay = Math.min(exponential + jitter, maxDelayMs);
      }

      console.log(`Rate limited (attempt ${attempt + 1}). Waiting ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }

  throw new Error('Max retries exceeded');
}
```

### Step 3: Implement Request Queue

```typescript
// src/twinmind/queue.ts
import PQueue from 'p-queue';

interface QueueConfig {
  concurrency: number;
  intervalMs: number;
  intervalCap: number;
}

const tierConfigs: Record<string, QueueConfig> = {
  free: { concurrency: 1, intervalMs: 60000, intervalCap: 30 },  # 60000: 1 minute in ms
  pro: { concurrency: 3, intervalMs: 60000, intervalCap: 60 },  # 1 minute in ms
  enterprise: { concurrency: 10, intervalMs: 60000, intervalCap: 300 },  # 300: 1 minute in ms
};

export class TwinMindQueue {
  private queue: PQueue;
  private tier: string;

  constructor(tier: 'free' | 'pro' | 'enterprise' = 'pro') {
    const config = tierConfigs[tier];
    this.tier = tier;
    this.queue = new PQueue({
      concurrency: config.concurrency,
      interval: config.intervalMs,
      intervalCap: config.intervalCap,
    });
  }

  async add<T>(operation: () => Promise<T>, priority?: number): Promise<T> {
    return this.queue.add(operation, { priority }) as Promise<T>;
  }

  get pending(): number {
    return this.queue.pending;
  }

  get size(): number {
    return this.queue.size;
  }

  pause(): void {
    this.queue.pause();
  }

  resume(): void {
    this.queue.start();
  }

  clear(): void {
    this.queue.clear();
  }
}

// Singleton instance
let queueInstance: TwinMindQueue | null = null;

export function getQueue(tier?: 'free' | 'pro' | 'enterprise'): TwinMindQueue {
  if (!queueInstance) {
    queueInstance = new TwinMindQueue(tier);
  }
  return queueInstance;
}
```

### Step 4: Monitor Rate Limit Headers

```typescript
// src/twinmind/rate-monitor.ts
export interface RateLimitStatus {
  limit: number;
  remaining: number;
  reset: Date;
  percentUsed: number;
}

export class RateLimitMonitor {
  private limits = new Map<string, RateLimitStatus>();

  updateFromResponse(endpoint: string, headers: Headers): void {
    const limit = parseInt(headers.get('X-RateLimit-Limit') || '60');
    const remaining = parseInt(headers.get('X-RateLimit-Remaining') || '60');
    const resetTimestamp = headers.get('X-RateLimit-Reset');
    const reset = resetTimestamp
      ? new Date(parseInt(resetTimestamp) * 1000)  # 1000: 1 second in ms
      : new Date(Date.now() + 60000);  # 60000: 1 minute in ms

    this.limits.set(endpoint, {
      limit,
      remaining,
      reset,
      percentUsed: ((limit - remaining) / limit) * 100,
    });
  }

  getStatus(endpoint: string): RateLimitStatus | undefined {
    return this.limits.get(endpoint);
  }

  shouldThrottle(endpoint: string, threshold = 10): boolean {
    const status = this.limits.get(endpoint);
    if (!status) return false;

    // Throttle if remaining < threshold AND reset hasn't happened
    return status.remaining < threshold && new Date() < status.reset;
  }

  getWaitTime(endpoint: string): number {
    const status = this.limits.get(endpoint);
    if (!status) return 0;

    const now = Date.now();
    const resetTime = status.reset.getTime();

    return Math.max(0, resetTime - now);
  }

  getAllStatuses(): Map<string, RateLimitStatus> {
    return new Map(this.limits);
  }
}

export const rateLimitMonitor = new RateLimitMonitor();
```

### Step 5: Implement Adaptive Rate Limiting

```typescript
// src/twinmind/adaptive-limiter.ts
export class AdaptiveRateLimiter {
  private successCount = 0;
  private failureCount = 0;
  private currentDelay = 0;
  private minDelay = 0;
  private maxDelay = 5000;  # 5000: 5 seconds in ms
  private windowMs = 60000;  # 60000: 1 minute in ms
  private windowStart = Date.now();

  recordSuccess(): void {
    this.maybeResetWindow();
    this.successCount++;

    // Decrease delay on success (min 0)
    if (this.currentDelay > 0) {
      this.currentDelay = Math.max(0, this.currentDelay - 100);
    }
  }

  recordFailure(isRateLimit: boolean): void {
    this.maybeResetWindow();
    this.failureCount++;

    if (isRateLimit) {
      // Increase delay on rate limit
      this.currentDelay = Math.min(this.maxDelay, this.currentDelay + 500);  # HTTP 500 Internal Server Error
    }
  }

  private maybeResetWindow(): void {
    const now = Date.now();
    if (now - this.windowStart > this.windowMs) {
      this.successCount = 0;
      this.failureCount = 0;
      this.windowStart = now;
    }
  }

  getDelay(): number {
    return this.currentDelay;
  }

  getMetrics(): { success: number; failure: number; delay: number; ratio: number } {
    const total = this.successCount + this.failureCount;
    return {
      success: this.successCount,
      failure: this.failureCount,
      delay: this.currentDelay,
      ratio: total > 0 ? this.successCount / total : 1,
    };
  }

  async wait(): Promise<void> {
    if (this.currentDelay > 0) {
      await new Promise(r => setTimeout(r, this.currentDelay));
    }
  }
}
```

### Step 6: Batch Requests for Efficiency

```typescript
// src/twinmind/batch.ts
export interface BatchOptions {
  maxBatchSize: number;
  maxWaitMs: number;
}

export class TranscriptionBatcher {
  private pending: Array<{
    audioUrl: string;
    resolve: (value: any) => void;
    reject: (error: any) => void;
  }> = [];
  private timer: NodeJS.Timeout | null = null;
  private options: BatchOptions;

  constructor(options: Partial<BatchOptions> = {}) {
    this.options = {
      maxBatchSize: 5,
      maxWaitMs: 1000,  # 1000: 1 second in ms
      ...options,
    };
  }

  async transcribe(audioUrl: string): Promise<any> {
    return new Promise((resolve, reject) => {
      this.pending.push({ audioUrl, resolve, reject });

      if (this.pending.length >= this.options.maxBatchSize) {
        this.flush();
      } else if (!this.timer) {
        this.timer = setTimeout(() => this.flush(), this.options.maxWaitMs);
      }
    });
  }

  private async flush(): Promise<void> {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }

    const batch = this.pending.splice(0, this.options.maxBatchSize);
    if (batch.length === 0) return;

    try {
      // Use batch API if available
      const results = await this.processBatch(batch.map(b => b.audioUrl));

      batch.forEach((item, index) => {
        item.resolve(results[index]);
      });
    } catch (error) {
      batch.forEach(item => item.reject(error));
    }
  }

  private async processBatch(audioUrls: string[]): Promise<any[]> {
    const client = getTwinMindClient();
    const response = await client.post('/transcribe/batch', {
      audio_urls: audioUrls,
      model: 'ear-3',
    });
    return response.data.transcripts;
  }
}
```

## Output
- Reliable API calls with automatic retry
- Request queue with rate limit awareness
- Adaptive throttling based on response patterns
- Batch processing for efficiency
- Real-time rate limit monitoring

## Error Handling

| Header | Description | Action |
|--------|-------------|--------|
| X-RateLimit-Limit | Max requests per window | Monitor total quota |
| X-RateLimit-Remaining | Remaining in window | Throttle when low |
| X-RateLimit-Reset | Unix timestamp of reset | Wait until reset |
| Retry-After | Seconds to wait | Honor this value |

## Rate Limit Best Practices

1. **Always handle 429 responses** - Never let rate limits crash your app
2. **Use request queues** - Don't burst requests
3. **Monitor remaining quota** - Throttle before hitting limits
4. **Implement circuit breakers** - Fail fast when API is overloaded
5. **Cache responses** - Avoid redundant requests
6. **Batch when possible** - Reduce total request count

## Resources
- [TwinMind Rate Limits](https://twinmind.com/docs/rate-limits)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [Rate Limiting Patterns](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)

## Next Steps
For security configuration, see `twinmind-security-basics`.

## Examples

**Basic usage**: Apply twinmind rate limits to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind rate limits for production environments with multiple constraints and team-specific requirements.