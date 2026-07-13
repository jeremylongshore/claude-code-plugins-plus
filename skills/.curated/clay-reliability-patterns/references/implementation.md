# Clay Reliability Patterns - Implementation Details

## Configuration

### Circuit Breaker Setup

```typescript
import CircuitBreaker from 'opossum';

const clayBreaker = new CircuitBreaker(callClayApi, {
  timeout: 10000,
  errorThresholdPercentage: 50,
  resetTimeout: 30000,
  volumeThreshold: 5,
});

clayBreaker.on('open', () => console.warn('[Clay] Circuit OPEN - requests failing'));
clayBreaker.on('halfOpen', () => console.log('[Clay] Circuit HALF-OPEN - testing'));
clayBreaker.on('close', () => console.log('[Clay] Circuit CLOSED - recovered'));

async function callClayApi(endpoint: string, body: any) {
  const response = await fetch(`https://api.clay.com/v1/${endpoint}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.CLAY_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`Clay ${response.status}`);
  return response.json();
}

// Usage: all Clay calls go through the breaker
export const clay = {
  enrich: (data: any) => clayBreaker.fire('enrich', data),
  search: (query: any) => clayBreaker.fire('search', query),
};
```

## Advanced Patterns

### Idempotent Request Wrapper

```typescript
import crypto from 'crypto';

const idempotencyStore = new Map<string, { result: any; expiry: number }>();

async function idempotentClayCall(
  key: string,
  fn: () => Promise<any>,
  ttlMs = 3600000
): Promise<any> {
  const hash = crypto.createHash('sha256').update(key).digest('hex');
  const cached = idempotencyStore.get(hash);

  if (cached && cached.expiry > Date.now()) {
    return cached.result;
  }

  const result = await fn();
  idempotencyStore.set(hash, { result, expiry: Date.now() + ttlMs });
  return result;
}
```

### Graceful Degradation with Fallback

```typescript
async function enrichContact(email: string) {
  try {
    return await clay.enrich({ email });
  } catch (err) {
    console.warn(`Clay enrichment failed for ${email}, using fallback`);
    return {
      email,
      enriched: false,
      fallback: true,
      source: 'cache',
      data: await getCachedProfile(email),
    };
  }
}
```

### Retry Queue with Dead Letter

```typescript
interface RetryItem {
  payload: any;
  attempts: number;
  lastError: string;
  nextRetry: number;
}

class ClayRetryQueue {
  private queue: RetryItem[] = [];
  private deadLetter: RetryItem[] = [];
  private maxRetries = 5;

  add(payload: any, error: string) {
    this.queue.push({
      payload,
      attempts: 1,
      lastError: error,
      nextRetry: Date.now() + 5000,
    });
  }

  async processQueue() {
    const now = Date.now();
    const ready = this.queue.filter((item) => item.nextRetry <= now);

    for (const item of ready) {
      try {
        await clay.enrich(item.payload);
        this.queue = this.queue.filter((q) => q !== item);
      } catch (err) {
        item.attempts++;
        item.lastError = String(err);
        item.nextRetry = now + Math.pow(2, item.attempts) * 1000;

        if (item.attempts >= this.maxRetries) {
          this.deadLetter.push(item);
          this.queue = this.queue.filter((q) => q !== item);
        }
      }
    }
  }
}
```

## Troubleshooting

### Circuit Breaker Stuck Open

If the breaker stays open, check:

```bash
# Test Clay API directly
curl -s -w "\nHTTP %{http_code}\n" \
  -H "Authorization: Bearer $CLAY_API_KEY" \
  https://api.clay.com/v1/health

# Check if DNS resolves
dig api.clay.com

# Verify no firewall rules blocking outbound
curl -v https://api.clay.com 2>&1 | grep -E "(Connected|SSL)"
```

### Idempotency Key Collisions

If duplicate operations occur despite idempotency keys, ensure the key includes all relevant fields:

```typescript
// Bad: only uses email (same person, different enrichment types collide)
const key = email;

// Good: includes operation type and parameters
const key = `${email}:enrich:${JSON.stringify(params)}`;
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
