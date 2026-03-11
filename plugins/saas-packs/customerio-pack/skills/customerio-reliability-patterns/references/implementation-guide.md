# Customer.io Reliability Patterns - Implementation Guide

### Pattern 1: Circuit Breaker
```typescript
// lib/circuit-breaker.ts
enum CircuitState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN'
}

interface CircuitBreakerConfig {
  failureThreshold: number;
  successThreshold: number;
  timeout: number;
}

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failures: number = 0;
  private successes: number = 0;
  private lastFailureTime: number = 0;
  private config: CircuitBreakerConfig;

  constructor(config: Partial<CircuitBreakerConfig> = {}) {
    this.config = {
      failureThreshold: config.failureThreshold || 5,
      successThreshold: config.successThreshold || 3,
      timeout: config.timeout || 30000
    };
  }

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() - this.lastFailureTime >= this.config.timeout) {
        this.state = CircuitState.HALF_OPEN;
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;

    if (this.state === CircuitState.HALF_OPEN) {
      this.successes++;
      if (this.successes >= this.config.successThreshold) {
        this.state = CircuitState.CLOSED;
        this.successes = 0;
      }
    }
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();
    this.successes = 0;

    if (this.failures >= this.config.failureThreshold) {
      this.state = CircuitState.OPEN;
    }
  }

  getState(): CircuitState {
    return this.state;
  }
}
```

### Pattern 2: Retry with Jitter
```typescript
// lib/retry.ts
interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  jitter: boolean;
}

function calculateDelay(attempt: number, config: RetryConfig): number {
  const exponentialDelay = config.baseDelay * Math.pow(2, attempt);
  const cappedDelay = Math.min(exponentialDelay, config.maxDelay);

  if (config.jitter) {
    // Add 0-30% jitter to prevent thundering herd
    return cappedDelay * (1 + Math.random() * 0.3);
  }

  return cappedDelay;
}

export async function withRetry<T>(
  operation: () => Promise<T>,
  config: RetryConfig = { maxRetries: 3, baseDelay: 1000, maxDelay: 30000, jitter: true }
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

### Pattern 3: Fallback Queue
```typescript
// lib/fallback-queue.ts
import { Queue, Worker } from 'bullmq';
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL!);

interface QueuedOperation {
  type: 'identify' | 'track';
  userId: string;
  data: any;
  timestamp: number;
  retryCount: number;
}

const fallbackQueue = new Queue<QueuedOperation>('customerio-fallback', {
  connection: redis
});

// Add to queue when circuit is open
export async function queueForRetry(operation: QueuedOperation): Promise<void> {
  await fallbackQueue.add('retry', operation, {
    attempts: 5,
    backoff: {
      type: 'exponential',
      delay: 60000 // Start with 1 minute
    },
    removeOnComplete: 1000,
    removeOnFail: 5000
  });
}

// Worker to process queued operations
const worker = new Worker<QueuedOperation>(
  'customerio-fallback',
  async (job) => {
    const { type, userId, data } = job.data;

    if (type === 'identify') {
      await client.identify(userId, data);
    } else if (type === 'track') {
      await client.track(userId, { name: data.event, data: data.properties });
    }
  },
  { connection: redis }
);

worker.on('failed', (job, error) => {
  console.error(`Fallback job ${job?.id} failed:`, error.message);
});
```

### Pattern 4: Graceful Degradation
```typescript
// lib/graceful-degradation.ts
import { TrackClient } from '@customerio/track';
import { CircuitBreaker } from './circuit-breaker';
import { queueForRetry } from './fallback-queue';

export class ResilientCustomerIO {
  private client: TrackClient;
  private circuitBreaker: CircuitBreaker;
  private fallbackEnabled: boolean;

  constructor(
    client: TrackClient,
    options: { fallbackEnabled?: boolean } = {}
  ) {
    this.client = client;
    this.circuitBreaker = new CircuitBreaker({
      failureThreshold: 5,
      successThreshold: 3,
      timeout: 30000
    });
    this.fallbackEnabled = options.fallbackEnabled ?? true;
  }

  async identify(userId: string, attributes: Record<string, any>): Promise<void> {
    try {
      await this.circuitBreaker.execute(() =>
        this.client.identify(userId, attributes)
      );
    } catch (error) {
      if (this.fallbackEnabled && this.circuitBreaker.getState() === 'OPEN') {
        console.log('Circuit open, queueing for retry');
        await queueForRetry({
          type: 'identify',
          userId,
          data: attributes,
          timestamp: Date.now(),
          retryCount: 0
        });
      } else {
        throw error;
      }
    }
  }

  async track(userId: string, event: string, data?: Record<string, any>): Promise<void> {
    try {
      await this.circuitBreaker.execute(() =>
        this.client.track(userId, { name: event, data })
      );
    } catch (error) {
      if (this.fallbackEnabled && this.circuitBreaker.getState() === 'OPEN') {
        console.log('Circuit open, queueing for retry');
        await queueForRetry({
          type: 'track',
          userId,
          data: { event, properties: data },
          timestamp: Date.now(),
          retryCount: 0
        });
      } else {
        throw error;
      }
    }
  }
}
```

### Pattern 5: Health Checks
```typescript
// lib/health-check.ts
interface HealthStatus {
  healthy: boolean;
  latency: number;
  circuitState: string;
  queueDepth: number;
  lastSuccess: Date | null;
  lastFailure: Date | null;
}

export class CustomerIOHealthChecker {
  private lastSuccess: Date | null = null;
  private lastFailure: Date | null = null;

  async check(): Promise<HealthStatus> {
    const start = Date.now();
    let healthy = false;

    try {
      await this.client.identify('health-check', { _health_check: true });
      healthy = true;
      this.lastSuccess = new Date();
    } catch (error) {
      this.lastFailure = new Date();
    }

    const queueDepth = await fallbackQueue.count();

    return {
      healthy,
      latency: Date.now() - start,
      circuitState: circuitBreaker.getState(),
      queueDepth,
      lastSuccess: this.lastSuccess,
      lastFailure: this.lastFailure
    };
  }
}
```

### Pattern 6: Idempotency
```typescript
// lib/idempotency.ts
import { LRUCache } from 'lru-cache';
import crypto from 'crypto';

const processedOperations = new LRUCache<string, boolean>({
  max: 100000,
  ttl: 3600000 // 1 hour
});

export function generateIdempotencyKey(
  userId: string,
  operation: string,
  data: any
): string {
  const payload = JSON.stringify({ userId, operation, data });
  return crypto.createHash('sha256').update(payload).digest('hex');
}

export async function executeIdempotent<T>(
  key: string,
  operation: () => Promise<T>
): Promise<T | null> {
  // Check if already processed
  if (processedOperations.has(key)) {
    console.log('Skipping duplicate operation:', key);
    return null;
  }

  // Execute operation
  const result = await operation();

  // Mark as processed
  processedOperations.set(key, true);

  return result;
}

// Usage
const key = generateIdempotencyKey(userId, 'track', { event, data });
await executeIdempotent(key, () => client.track(userId, { name: event, data }));
```
