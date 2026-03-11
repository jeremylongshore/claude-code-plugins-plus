# Guidewire Rate Limits — Implementation Guide

## Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1706312400
X-RateLimit-Scope: tenant
Retry-After: 60
```

## Rate Limit Tracker

```typescript
// Track rate limits from response headers
interface RateLimitInfo {
  limit: number;
  remaining: number;
  resetTime: Date;
  scope: string;
}

class RateLimitTracker {
  private current: RateLimitInfo | null = null;

  updateFromResponse(response: AxiosResponse): void {
    const headers = response.headers;

    this.current = {
      limit: parseInt(headers['x-ratelimit-limit'] || '1000'),
      remaining: parseInt(headers['x-ratelimit-remaining'] || '1000'),
      resetTime: new Date(parseInt(headers['x-ratelimit-reset'] || '0') * 1000),
      scope: headers['x-ratelimit-scope'] || 'tenant'
    };

    // Warn if approaching limit
    if (this.current.remaining < this.current.limit * 0.1) {
      console.warn(`Rate limit warning: ${this.current.remaining}/${this.current.limit} remaining`);
    }
  }

  canMakeRequest(): boolean {
    if (!this.current) return true;
    return this.current.remaining > 0 || new Date() > this.current.resetTime;
  }

  getWaitTime(): number {
    if (!this.current || this.current.remaining > 0) return 0;
    return Math.max(0, this.current.resetTime.getTime() - Date.now());
  }
}
```

## Exponential Backoff with Jitter

```typescript
interface BackoffConfig {
  initialDelayMs: number;
  maxDelayMs: number;
  multiplier: number;
  jitterFactor: number;
}

class ExponentialBackoff {
  private attempt: number = 0;
  private config: BackoffConfig;

  constructor(config: Partial<BackoffConfig> = {}) {
    this.config = {
      initialDelayMs: config.initialDelayMs || 1000,
      maxDelayMs: config.maxDelayMs || 60000,
      multiplier: config.multiplier || 2,
      jitterFactor: config.jitterFactor || 0.1
    };
  }

  getNextDelay(): number {
    const baseDelay = Math.min(
      this.config.initialDelayMs * Math.pow(this.config.multiplier, this.attempt),
      this.config.maxDelayMs
    );

    // Add jitter to prevent thundering herd
    const jitter = baseDelay * this.config.jitterFactor * (Math.random() * 2 - 1);

    this.attempt++;
    return Math.round(baseDelay + jitter);
  }

  reset(): void {
    this.attempt = 0;
  }
}

// Usage in API client
async function makeRequestWithBackoff<T>(
  request: () => Promise<T>,
  maxRetries: number = 5
): Promise<T> {
  const backoff = new ExponentialBackoff();

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const result = await request();
      backoff.reset();
      return result;
    } catch (error) {
      if (error.response?.status === 429) {
        const retryAfter = parseInt(error.response.headers['retry-after'] || '0') * 1000;
        const delay = Math.max(retryAfter, backoff.getNextDelay());

        console.log(`Rate limited, waiting ${delay}ms before retry ${attempt + 1}/${maxRetries}`);
        await sleep(delay);
        continue;
      }
      throw error;
    }
  }

  throw new Error(`Request failed after ${maxRetries} retries due to rate limiting`);
}
```

## Request Queue with Throttling

```typescript
import PQueue from 'p-queue';

class RateLimitedClient {
  private queue: PQueue;
  private rateLimiter: RateLimitTracker;

  constructor(requestsPerSecond: number = 40) {
    this.queue = new PQueue({
      concurrency: 10,
      interval: 1000,
      intervalCap: requestsPerSecond
    });
    this.rateLimiter = new RateLimitTracker();
  }

  async request<T>(config: AxiosRequestConfig): Promise<T> {
    return this.queue.add(async () => {
      const waitTime = this.rateLimiter.getWaitTime();
      if (waitTime > 0) {
        console.log(`Waiting ${waitTime}ms due to rate limit`);
        await sleep(waitTime);
      }

      const response = await axios.request<T>(config);
      this.rateLimiter.updateFromResponse(response);

      return response.data;
    });
  }

  // Batch requests efficiently
  async batchRequest<T, R>(
    items: T[],
    requestFn: (item: T) => Promise<R>,
    options: { batchSize?: number; delayBetweenBatches?: number } = {}
  ): Promise<R[]> {
    const { batchSize = 10, delayBetweenBatches = 100 } = options;
    const results: R[] = [];

    for (let i = 0; i < items.length; i += batchSize) {
      const batch = items.slice(i, i + batchSize);
      const batchResults = await Promise.all(batch.map(item => this.request(requestFn(item))));
      results.push(...batchResults);

      if (i + batchSize < items.length) {
        await sleep(delayBetweenBatches);
      }
    }

    return results;
  }
}
```

## API Optimization Patterns

```typescript
// Use includes to reduce API calls
// BAD: Multiple API calls
async function getAccountWithPoliciesBad(accountId: string): Promise<any> {
  const account = await client.get(`/account/v1/accounts/${accountId}`);
  const policies = await client.get(`/account/v1/accounts/${accountId}/policies`);
  const contacts = await client.get(`/account/v1/accounts/${accountId}/contacts`);
  return { account, policies, contacts };
}

// GOOD: Single call with includes
async function getAccountWithPoliciesGood(accountId: string): Promise<any> {
  return client.get(`/account/v1/accounts/${accountId}?include=policies,contacts`);
}

// Use filtering to reduce response size
// BAD: Get all, filter client-side
async function getActivePoliciesBad(accountId: string): Promise<Policy[]> {
  const response = await client.get(`/account/v1/accounts/${accountId}/policies`);
  return response.data.filter((p: Policy) => p.status.code === 'InForce');
}

// GOOD: Server-side filtering
async function getActivePoliciesGood(accountId: string): Promise<Policy[]> {
  const response = await client.get(
    `/account/v1/accounts/${accountId}/policies?filter=status:eq:InForce`
  );
  return response.data;
}

// Use pagination efficiently
async function getAllPolicies(accountId: string): Promise<Policy[]> {
  const policies: Policy[] = [];
  let cursor: string | undefined;

  do {
    const response = await client.get(
      `/account/v1/accounts/${accountId}/policies`,
      { params: { pageSize: 100, cursor } }
    );
    policies.push(...response.data);
    cursor = response.links?.next;
  } while (cursor);

  return policies;
}
```

## Circuit Breaker

```typescript
enum CircuitState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN'
}

class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failures: number = 0;
  private lastFailureTime: Date | null = null;
  private successCount: number = 0;

  constructor(
    private failureThreshold: number = 5,
    private resetTimeoutMs: number = 60000,
    private halfOpenSuccessThreshold: number = 3
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (this.shouldAttemptReset()) {
        this.state = CircuitState.HALF_OPEN;
        this.successCount = 0;
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure(error);
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= this.halfOpenSuccessThreshold) {
        this.state = CircuitState.CLOSED;
        console.log('Circuit breaker closed');
      }
    }
  }

  private onFailure(error: any): void {
    if (error.response?.status === 429) {
      this.failures++;
      this.lastFailureTime = new Date();

      if (this.failures >= this.failureThreshold) {
        this.state = CircuitState.OPEN;
        console.warn('Circuit breaker opened due to rate limiting');
      }
    }
  }

  private shouldAttemptReset(): boolean {
    if (!this.lastFailureTime) return true;
    return Date.now() - this.lastFailureTime.getTime() >= this.resetTimeoutMs;
  }
}
```

## Gosu Rate Limit Handling

```gosu
package gw.integration.ratelimit

uses gw.api.util.Logger
uses java.util.concurrent.Semaphore
uses java.util.concurrent.TimeUnit

class RateLimiter {
  private static final var LOG = Logger.forCategory("RateLimiter")

  private var _permits : Semaphore
  private var _lastRefill : long
  private var _refillInterval : long
  private var _maxPermits : int

  construct(maxRequestsPerSecond : int) {
    _maxPermits = maxRequestsPerSecond
    _permits = new Semaphore(maxRequestsPerSecond)
    _lastRefill = System.currentTimeMillis()
    _refillInterval = 1000
  }

  function acquire() : boolean {
    refillPermits()
    return _permits.tryAcquire(5, TimeUnit.SECONDS)
  }

  private function refillPermits() {
    var now = System.currentTimeMillis()
    var elapsed = now - _lastRefill

    if (elapsed >= _refillInterval) {
      var periods = (elapsed / _refillInterval) as int
      var permitsToAdd = Math.min(periods * _maxPermits, _maxPermits - _permits.availablePermits())
      _permits.release(permitsToAdd)
      _lastRefill = now
    }
  }

  function executeWithRateLimit<T>(operation() : T) : T {
    if (!acquire()) {
      LOG.warn("Rate limit exceeded, request blocked")
      throw new RateLimitException("Rate limit exceeded")
    }

    try {
      return operation()
    } finally {
      // Permit is consumed, will be refilled later
    }
  }
}
```

## Monitoring Metrics

```typescript
interface RateLimitMetrics {
  totalRequests: number;
  rateLimitedRequests: number;
  avgResponseTime: number;
  currentUsage: number;
  limit: number;
}

class RateLimitMonitor {
  private metrics: RateLimitMetrics = {
    totalRequests: 0,
    rateLimitedRequests: 0,
    avgResponseTime: 0,
    currentUsage: 0,
    limit: 1000
  };

  recordRequest(duration: number, rateLimited: boolean): void {
    this.metrics.totalRequests++;
    if (rateLimited) {
      this.metrics.rateLimitedRequests++;
    }
    this.metrics.avgResponseTime =
      (this.metrics.avgResponseTime * (this.metrics.totalRequests - 1) + duration) /
      this.metrics.totalRequests;
  }

  updateUsage(remaining: number, limit: number): void {
    this.metrics.currentUsage = limit - remaining;
    this.metrics.limit = limit;
  }

  getMetrics(): RateLimitMetrics {
    return { ...this.metrics };
  }

  toPrometheus(): string {
    return `
# HELP guidewire_requests_total Total API requests
# TYPE guidewire_requests_total counter
guidewire_requests_total ${this.metrics.totalRequests}

# HELP guidewire_rate_limited_total Rate limited requests
# TYPE guidewire_rate_limited_total counter
guidewire_rate_limited_total ${this.metrics.rateLimitedRequests}

# HELP guidewire_rate_limit_usage Current rate limit usage
# TYPE guidewire_rate_limit_usage gauge
guidewire_rate_limit_usage ${this.metrics.currentUsage}
`.trim();
  }
}
```
