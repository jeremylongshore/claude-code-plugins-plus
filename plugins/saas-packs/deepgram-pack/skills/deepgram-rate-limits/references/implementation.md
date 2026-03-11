# Deepgram Rate Limits - Implementation Details

## TypeScript Rate Limiter
```typescript
interface RateLimiterConfig {
  maxConcurrent: number;
  maxPerMinute: number;
  retryAttempts: number;
  baseDelay: number;
}

export class DeepgramRateLimiter {
  private queue: Array<{ fn: () => Promise<unknown>; resolve: (value: unknown) => void; reject: (error: Error) => void }> = [];
  private activeRequests = 0;
  private requestsThisMinute = 0;
  private minuteStart = Date.now();
  private config: RateLimiterConfig;

  constructor(config: Partial<RateLimiterConfig> = {}) {
    this.config = {
      maxConcurrent: config.maxConcurrent ?? 50,
      maxPerMinute: config.maxPerMinute ?? 500,
      retryAttempts: config.retryAttempts ?? 3,
      baseDelay: config.baseDelay ?? 1000,
    };
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({ fn, resolve: resolve as (value: unknown) => void, reject });
      this.processQueue();
    });
  }

  private async processQueue() {
    const now = Date.now();
    if (now - this.minuteStart >= 60000) { this.requestsThisMinute = 0; this.minuteStart = now; }
    if (this.activeRequests >= this.config.maxConcurrent) return;
    if (this.requestsThisMinute >= this.config.maxPerMinute) return;
    if (this.queue.length === 0) return;

    const { fn, resolve, reject } = this.queue.shift()!;
    this.activeRequests++;
    this.requestsThisMinute++;

    try {
      const result = await this.executeWithRetry(fn);
      resolve(result);
    } catch (error) {
      reject(error instanceof Error ? error : new Error(String(error)));
    } finally {
      this.activeRequests--;
      this.processQueue();
    }
  }

  private async executeWithRetry<T>(fn: () => Promise<T>, attempt = 0): Promise<T> {
    try { return await fn(); }
    catch (error) {
      const isRateLimited = error instanceof Error && (error.message.includes('429') || error.message.includes('rate limit'));
      if (isRateLimited && attempt < this.config.retryAttempts) {
        const delay = this.config.baseDelay * Math.pow(2, attempt);
        await new Promise(r => setTimeout(r, delay + Math.random() * 1000));
        return this.executeWithRetry(fn, attempt + 1);
      }
      throw error;
    }
  }

  getStats() {
    return { activeRequests: this.activeRequests, queuedRequests: this.queue.length, requestsThisMinute: this.requestsThisMinute };
  }
}
```

## Exponential Backoff with Jitter
```typescript
export class ExponentialBackoff {
  private attempt = 0;
  private config: { baseDelay: number; maxDelay: number; factor: number; jitter: boolean };

  constructor(config: Partial<typeof ExponentialBackoff.prototype.config> = {}) {
    this.config = { baseDelay: config?.baseDelay ?? 1000, maxDelay: config?.maxDelay ?? 60000, factor: config?.factor ?? 2, jitter: config?.jitter ?? true };
  }

  getDelay(): number {
    const exponential = this.config.baseDelay * Math.pow(this.config.factor, this.attempt);
    const capped = Math.min(exponential, this.config.maxDelay);
    return this.config.jitter ? Math.random() * capped : capped;
  }

  increment() { this.attempt++; }
  reset() { this.attempt = 0; }
  async wait() { await new Promise(r => setTimeout(r, this.getDelay())); this.increment(); }
}
```

## Circuit Breaker Pattern
```typescript
enum CircuitState { CLOSED = 'CLOSED', OPEN = 'OPEN', HALF_OPEN = 'HALF_OPEN' }

export class CircuitBreaker {
  private state = CircuitState.CLOSED;
  private failures = 0;
  private lastFailure = 0;
  private halfOpenSuccesses = 0;
  private config: { failureThreshold: number; resetTimeout: number; halfOpenRequests: number };

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() - this.lastFailure > this.config.resetTimeout) {
        this.state = CircuitState.HALF_OPEN;
        this.halfOpenSuccesses = 0;
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }
    try {
      const result = await fn();
      if (this.state === CircuitState.HALF_OPEN) {
        this.halfOpenSuccesses++;
        if (this.halfOpenSuccesses >= this.config.halfOpenRequests) { this.state = CircuitState.CLOSED; this.failures = 0; }
      }
      return result;
    } catch (error) {
      this.failures++;
      this.lastFailure = Date.now();
      if (this.failures >= this.config.failureThreshold) { this.state = CircuitState.OPEN; }
      throw error;
    }
  }
}
```

## Usage Monitor
```typescript
export class DeepgramUsageMonitor {
  private stats = { requestCount: 0, audioSeconds: 0, errorCount: 0, rateLimitHits: 0, startTime: new Date() };

  recordRequest(audioSeconds = 0) { this.stats.requestCount++; this.stats.audioSeconds += audioSeconds; }
  recordError(isRateLimit = false) { this.stats.errorCount++; if (isRateLimit) this.stats.rateLimitHits++; }

  shouldAlert(): boolean {
    const hitRate = this.stats.rateLimitHits / this.stats.requestCount;
    return hitRate > 0.1 && this.stats.requestCount > 10;
  }
}
```

## Python Rate Limiter
```python
import asyncio, time
from collections import deque

class RateLimiter:
    def __init__(self, max_concurrent=50, max_per_minute=500):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_per_minute = max_per_minute
        self.request_times = deque()

    async def execute(self, fn):
        await self._wait_for_rate_limit()
        async with self.semaphore:
            self.request_times.append(time.time())
            return await fn()

    async def _wait_for_rate_limit(self):
        now = time.time()
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()
        if len(self.request_times) >= self.max_per_minute:
            wait_time = 60 - (now - self.request_times[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
```
