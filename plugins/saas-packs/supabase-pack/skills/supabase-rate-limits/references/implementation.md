## Implementation Guide

### Step 1: Understand Rate Limit Tiers

| Tier | Requests/min | Requests/day | Burst |
|------|-------------|--------------|-------|
| Free | 500 | 50,000 | 10 |
| Pro | 5,000 | 1,000,000 | 50 |
| Enterprise | Unlimited | Unlimited | 200 |

### Step 2: Implement Exponential Backoff with Jitter

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

### Step 3: Add Idempotency Keys

```typescript
import { v4 as uuidv4 } from 'uuid';
import crypto from 'crypto';

// Generate deterministic key from operation params (for safe retries)
function generateIdempotencyKey(operation: string, params: Record<string, any>): string {
  const data = JSON.stringify({ operation, params });
  return crypto.createHash('sha256').update(data).digest('hex');
}

async function idempotentRequest<T>(
  client: SupabaseClient,
  params: Record<string, any>,
  idempotencyKey?: string  // Pass existing key for retries
): Promise<T> {
  // Use provided key (for retries) or generate deterministic key from params
  const key = idempotencyKey || generateIdempotencyKey(params.method || 'POST', params);
  return client.request({
    ...params,
    headers: { 'Idempotency-Key': key, ...params.headers },
  });
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
