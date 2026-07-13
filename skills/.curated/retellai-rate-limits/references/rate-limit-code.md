# Rate Limit Implementation Code

## Exponential Backoff with Jitter

```typescript
async function withExponentialBackoff<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 32000, jitterMs: 500 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;
      const status = error.status || error.response?.status;
      if (status !== 429 && (status < 500 || status >= 600)) throw error;

      // Exponential delay with jitter to prevent thundering herd
      const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * config.jitterMs;
      const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);

      console.log(`Rate limited. Retrying in ${delay.toFixed(0)}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Idempotency Keys

```typescript
import { v4 as uuidv4 } from 'uuid';
import crypto from 'crypto';

// Generate deterministic key from operation params (for safe retries)
function generateIdempotencyKey(operation: string, params: Record<string, any>): string {
  const data = JSON.stringify({ operation, params });
  return crypto.createHash('sha256').update(data).digest('hex');
}

async function idempotentRequest<T>(
  client: RetellAIClient,
  params: Record<string, any>,
  idempotencyKey?: string
): Promise<T> {
  const key = idempotencyKey || generateIdempotencyKey(params.method || 'POST', params);
  return client.request({
    ...params,
    headers: { 'Idempotency-Key': key, ...params.headers },
  });
}
```

## Queue-Based Rate Limiting

```typescript
import PQueue from 'p-queue';

const queue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 10,
});

async function queuedRequest<T>(operation: () => Promise<T>): Promise<T> {
  return queue.add(operation);
}
```

## Rate Limit Monitor

```typescript
class RateLimitMonitor {
  private remaining: number = 60;
  private resetAt: Date = new Date();

  updateFromHeaders(headers: Headers) {
    this.remaining = parseInt(headers.get('X-RateLimit-Remaining') || '60');
    const resetTimestamp = headers.get('X-RateLimit-Reset');
    if (resetTimestamp) {
      this.resetAt = new Date(parseInt(resetTimestamp) * 1000);
    }
  }

  shouldThrottle(): boolean {
    return this.remaining < 5 && new Date() < this.resetAt;
  }

  getWaitTime(): number {
    return Math.max(0, this.resetAt.getTime() - Date.now());
  }
}
```
