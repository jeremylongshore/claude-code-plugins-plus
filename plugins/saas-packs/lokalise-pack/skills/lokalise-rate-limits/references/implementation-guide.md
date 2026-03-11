# Lokalise Rate Limits - Implementation Guide

Detailed implementation reference for the lokalise-rate-limits skill.

## Rate Limit Specifications

### Current Limits (2025)
| Limit Type | Value | Scope |
|------------|-------|-------|
| Requests per second | 6 | Per API token + IP |
| Concurrent requests | 10 | Per project |
| Concurrent per token | 1 | Per token (data consistency) |
| Keys per list request | 500 | Per request |
| Keys per bulk create | 500 | Per request |

### Rate Limit Headers
```
X-RateLimit-Limit: 6
X-RateLimit-Remaining: 5
X-RateLimit-Reset: 1640000000
```


## Instructions

### Step 1: Implement Request Queue
```typescript
import PQueue from "p-queue";

// Lokalise: 6 req/sec, 10 concurrent per project
const queue = new PQueue({
  concurrency: 5,        // Conservative concurrent limit
  interval: 1000,        // 1 second
  intervalCap: 5,        // Max 5 per second (leave headroom)
  carryoverConcurrencyCount: true,
});

export async function queuedRequest<T>(
  operation: () => Promise<T>
): Promise<T> {
  return queue.add(operation) as Promise<T>;
}

// Track queue status
queue.on("active", () => {
  console.log(`Queue: ${queue.size} waiting, ${queue.pending} running`);
});
```

### Step 2: Add Exponential Backoff with Jitter
```typescript
interface BackoffConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterMs: number;
}

const defaultConfig: BackoffConfig = {
  maxRetries: 5,
  baseDelayMs: 1000,
  maxDelayMs: 32000,
  jitterMs: 500,
};

export async function withExponentialBackoff<T>(
  operation: () => Promise<T>,
  config = defaultConfig
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      // Only retry on rate limits and server errors
      const isRetryable = error.code === 429 ||
        (error.code >= 500 && error.code < 600);

      if (!isRetryable || attempt === config.maxRetries) {
        throw error;
      }

      // Calculate delay with exponential backoff + jitter
      const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * config.jitterMs;
      const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);

      // Check Retry-After header if available
      const retryAfter = error.headers?.["retry-after"];
      const actualDelay = retryAfter
        ? parseInt(retryAfter) * 1000
        : delay;

      console.log(`Rate limited. Retry ${attempt + 1}/${config.maxRetries} in ${actualDelay}ms`);
      await new Promise(r => setTimeout(r, actualDelay));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 3: Create Rate-Aware Client Wrapper
```typescript
import { LokaliseApi, ApiError } from "@lokalise/node-api";

export class RateLimitedLokaliseClient {
  private client: LokaliseApi;
  private queue: PQueue;
  private rateLimitRemaining = 6;
  private rateLimitReset = 0;

  constructor(apiKey: string) {
    this.client = new LokaliseApi({ apiKey });
    this.queue = new PQueue({
      concurrency: 5,
      interval: 1000,
      intervalCap: 5,
    });
  }

  async request<T>(operation: () => Promise<T>): Promise<T> {
    // Proactive throttle if low on quota
    if (this.shouldThrottle()) {
      const waitTime = this.getWaitTime();
      console.log(`Proactive throttle: waiting ${waitTime}ms`);
      await new Promise(r => setTimeout(r, waitTime));
    }

    return this.queue.add(() =>
      withExponentialBackoff(async () => {
        try {
          const result = await operation();
          // Update rate limit info from response headers if available
          return result;
        } catch (error: any) {
          this.updateRateLimitFromError(error);
          throw error;
        }
      })
    ) as Promise<T>;
  }

  private shouldThrottle(): boolean {
    return this.rateLimitRemaining < 2 && Date.now() < this.rateLimitReset;
  }

  private getWaitTime(): number {
    return Math.max(0, this.rateLimitReset - Date.now());
  }

  private updateRateLimitFromError(error: any) {
    if (error.code === 429) {
      this.rateLimitRemaining = 0;
      this.rateLimitReset = Date.now() + 1000;
    }
  }

  // Expose underlying client methods through wrapper
  projects() {
    return {
      list: () => this.request(() => this.client.projects().list()),
      get: (id: string) => this.request(() => this.client.projects().get(id)),
    };
  }

  keys() {
    return {
      list: (params: any) => this.request(() => this.client.keys().list(params)),
      create: (params: any) => this.request(() => this.client.keys().create(params)),
    };
  }
}
```

### Step 4: Implement Batch Processing
```typescript
async function batchProcess<T, R>(
  items: T[],
  operation: (item: T) => Promise<R>,
  batchSize = 100
): Promise<R[]> {
  const results: R[] = [];

  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);

    // Process batch in parallel (respecting queue limits)
    const batchResults = await Promise.all(
      batch.map(item => queuedRequest(() => operation(item)))
    );

    results.push(...batchResults);

    // Progress logging
    console.log(`Processed ${Math.min(i + batchSize, items.length)}/${items.length}`);
  }

  return results;
}
```


## Detailed Examples

### CLI with Rate Limiting
```bash
#!/bin/bash
# Respect rate limits in shell scripts

lokalise_request() {
  local result
  result=$(lokalise2 "$@" 2>&1)
  local exit_code=$?

  if echo "$result" | grep -q "429"; then
    echo "Rate limited, waiting 2 seconds..."
    sleep 2
    lokalise_request "$@"
  else
    echo "$result"
    return $exit_code
  fi
}

# Use the wrapper
lokalise_request --token "$TOKEN" project list
```

### Monitor Rate Limit Usage
```typescript
class RateLimitMonitor {
  private requests: number[] = [];
  private readonly windowMs = 1000;
  private readonly limit = 6;

  track() {
    const now = Date.now();
    this.requests = this.requests.filter(t => now - t < this.windowMs);
    this.requests.push(now);
  }

  getCurrentRate(): number {
    const now = Date.now();
    return this.requests.filter(t => now - t < this.windowMs).length;
  }

  shouldWait(): boolean {
    return this.getCurrentRate() >= this.limit;
  }

  getStats() {
    return {
      currentRate: this.getCurrentRate(),
      limit: this.limit,
      utilizationPercent: (this.getCurrentRate() / this.limit) * 100,
    };
  }
}
```

### Bulk Operations with Progress
```typescript
async function bulkCreateKeys(
  projectId: string,
  keys: any[],
  onProgress?: (completed: number, total: number) => void
) {
  const client = new RateLimitedLokaliseClient(process.env.LOKALISE_API_TOKEN!);
  const batchSize = 100;  // Stay under 500 limit with margin
  const results: any[] = [];

  for (let i = 0; i < keys.length; i += batchSize) {
    const batch = keys.slice(i, i + batchSize);

    const result = await client.keys().create({
      project_id: projectId,
      keys: batch,
    });

    results.push(...result.items);
    onProgress?.(Math.min(i + batchSize, keys.length), keys.length);

    // Small delay between batches
    await new Promise(r => setTimeout(r, 200));
  }

  return results;
}
```

