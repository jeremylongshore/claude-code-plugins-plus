# Customer.io Rate Limits - Implementation Guide

### Step 1: Implement Rate Limiter
```typescript
// lib/rate-limiter.ts
class RateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly maxTokens: number;
  private readonly refillRate: number;

  constructor(maxRequestsPerSecond: number = 100) {
    this.maxTokens = maxRequestsPerSecond;
    this.tokens = maxRequestsPerSecond;
    this.refillRate = maxRequestsPerSecond;
    this.lastRefill = Date.now();
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }

  async acquire(): Promise<void> {
    this.refill();

    if (this.tokens >= 1) {
      this.tokens -= 1;
      return;
    }

    // Wait for token to become available
    const waitTime = ((1 - this.tokens) / this.refillRate) * 1000;
    await new Promise(resolve => setTimeout(resolve, waitTime));
    this.tokens = 0;
    this.lastRefill = Date.now();
  }
}

export const trackApiLimiter = new RateLimiter(100);
```

### Step 2: Implement Exponential Backoff
```typescript
// lib/backoff.ts
interface BackoffConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  jitterFactor: number;
}

const defaultConfig: BackoffConfig = {
  maxRetries: 5,
  baseDelay: 1000,
  maxDelay: 32000,
  jitterFactor: 0.1
};

function calculateDelay(attempt: number, config: BackoffConfig): number {
  const exponentialDelay = config.baseDelay * Math.pow(2, attempt);
  const cappedDelay = Math.min(exponentialDelay, config.maxDelay);
  const jitter = cappedDelay * config.jitterFactor * Math.random();
  return cappedDelay + jitter;
}

export async function withExponentialBackoff<T>(
  operation: () => Promise<T>,
  config: BackoffConfig = defaultConfig
): Promise<T> {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      lastError = error;

      // Don't retry on client errors (except 429)
      if (error.statusCode >= 400 && error.statusCode < 500 && error.statusCode !== 429) {
        throw error;
      }

      if (attempt < config.maxRetries) {
        const delay = calculateDelay(attempt, config);
        console.log(`Retry ${attempt + 1}/${config.maxRetries} after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError;
}
```

### Step 3: Create Rate-Limited Client
```typescript
// lib/customerio-rate-limited.ts
import { TrackClient, RegionUS } from '@customerio/track';
import { trackApiLimiter } from './rate-limiter';
import { withExponentialBackoff } from './backoff';

export class RateLimitedCustomerIO {
  private client: TrackClient;

  constructor() {
    this.client = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_API_KEY!,
      { region: RegionUS }
    );
  }

  async identify(userId: string, attributes: Record<string, any>) {
    await trackApiLimiter.acquire();
    return withExponentialBackoff(() =>
      this.client.identify(userId, attributes)
    );
  }

  async track(userId: string, event: string, data?: Record<string, any>) {
    await trackApiLimiter.acquire();
    return withExponentialBackoff(() =>
      this.client.track(userId, { name: event, data })
    );
  }

  // Batch operations for high volume
  async batchIdentify(users: Array<{ id: string; attributes: Record<string, any> }>) {
    const results: Array<{ id: string; success: boolean; error?: string }> = [];

    for (const user of users) {
      await trackApiLimiter.acquire();
      try {
        await withExponentialBackoff(() =>
          this.client.identify(user.id, user.attributes)
        );
        results.push({ id: user.id, success: true });
      } catch (error: any) {
        results.push({ id: user.id, success: false, error: error.message });
      }
    }

    return results;
  }
}
```

### Step 4: Handle 429 Response Headers
```typescript
// lib/rate-limit-handler.ts
interface RateLimitInfo {
  remaining: number;
  resetTime: Date;
  retryAfter?: number;
}

function parseRateLimitHeaders(headers: Headers): RateLimitInfo | null {
  const remaining = headers.get('X-RateLimit-Remaining');
  const reset = headers.get('X-RateLimit-Reset');
  const retryAfter = headers.get('Retry-After');

  if (!remaining || !reset) return null;

  return {
    remaining: parseInt(remaining, 10),
    resetTime: new Date(parseInt(reset, 10) * 1000),
    retryAfter: retryAfter ? parseInt(retryAfter, 10) : undefined
  };
}

async function handleRateLimitResponse(response: Response): Promise<void> {
  if (response.status === 429) {
    const info = parseRateLimitHeaders(response.headers);
    const waitTime = info?.retryAfter || 60;

    console.warn(`Rate limited. Waiting ${waitTime}s before retry.`);
    await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
  }
}
```

### Step 5: Queue-Based Rate Limiting
```typescript
// lib/customerio-queue.ts
import PQueue from 'p-queue';

const queue = new PQueue({
  concurrency: 10,
  interval: 1000,
  intervalCap: 100 // 100 requests per second
});

export class QueuedCustomerIO {
  private client: TrackClient;

  constructor() {
    this.client = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_API_KEY!,
      { region: RegionUS }
    );
  }

  async identify(userId: string, attributes: Record<string, any>) {
    return queue.add(() => this.client.identify(userId, attributes));
  }

  async track(userId: string, event: string, data?: Record<string, any>) {
    return queue.add(() => this.client.track(userId, { name: event, data }));
  }

  // Get queue stats
  getStats() {
    return {
      pending: queue.pending,
      size: queue.size,
      isPaused: queue.isPaused
    };
  }
}
```
