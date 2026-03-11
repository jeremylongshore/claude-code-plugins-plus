# Linear Rate Limits - Implementation Guide

Detailed implementation examples and code patterns.

## Linear Rate Limit Structure

### Current Limits
| Tier | Requests/min | Complexity/min | Notes |
|------|-------------|----------------|-------|
| Standard | 1,500 | 250,000 | Most integrations |
| Enterprise | Higher | Higher | Contact Linear |

### Headers Returned
```
X-RateLimit-Limit: 1500
X-RateLimit-Remaining: 1499
X-RateLimit-Reset: 1640000000
X-Complexity-Limit: 250000
X-Complexity-Cost: 50
X-Complexity-Remaining: 249950
```

## Instructions

### Step 1: Basic Rate Limit Handler
```typescript
// lib/rate-limiter.ts
interface RateLimitState {
  remaining: number;
  reset: Date;
  complexityRemaining: number;
}

class LinearRateLimiter {
  private state: RateLimitState = {
    remaining: 1500,
    reset: new Date(),
    complexityRemaining: 250000,
  };

  updateFromHeaders(headers: Headers): void {
    const remaining = headers.get("x-ratelimit-remaining");
    const reset = headers.get("x-ratelimit-reset");
    const complexityRemaining = headers.get("x-complexity-remaining");

    if (remaining) this.state.remaining = parseInt(remaining);
    if (reset) this.state.reset = new Date(parseInt(reset) * 1000);
    if (complexityRemaining) {
      this.state.complexityRemaining = parseInt(complexityRemaining);
    }
  }

  async waitIfNeeded(): Promise<void> {
    // If very low on requests, wait until reset
    if (this.state.remaining < 10) {
      const waitMs = this.state.reset.getTime() - Date.now();
      if (waitMs > 0) {
        console.log(`Rate limit low, waiting ${waitMs}ms...`);
        await new Promise(r => setTimeout(r, waitMs));
      }
    }
  }

  getState(): RateLimitState {
    return { ...this.state };
  }
}

export const rateLimiter = new LinearRateLimiter();
```

### Step 2: Exponential Backoff
```typescript
// lib/backoff.ts
interface BackoffOptions {
  maxRetries?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  jitter?: boolean;
}

export async function withBackoff<T>(
  fn: () => Promise<T>,
  options: BackoffOptions = {}
): Promise<T> {
  const {
    maxRetries = 5,
    baseDelayMs = 1000,
    maxDelayMs = 30000,
    jitter = true,
  } = options;

  let lastError: Error | undefined;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      lastError = error;

      // Only retry on rate limit errors
      const isRateLimited =
        error?.extensions?.code === "RATE_LIMITED" ||
        error?.response?.status === 429;

      if (!isRateLimited || attempt === maxRetries - 1) {
        throw error;
      }

      // Calculate delay with exponential backoff
      let delay = Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs);

      // Add jitter to prevent thundering herd
      if (jitter) {
        delay += Math.random() * delay * 0.1;
      }

      // Check Retry-After header if available
      const retryAfter = error?.response?.headers?.get?.("retry-after");
      if (retryAfter) {
        delay = Math.max(delay, parseInt(retryAfter) * 1000);
      }

      console.log(
        `Rate limited, attempt ${attempt + 1}/${maxRetries}, ` +
        `retrying in ${Math.round(delay)}ms...`
      );

      await new Promise(r => setTimeout(r, delay));
    }
  }

  throw lastError;
}
```

### Step 3: Request Queue
```typescript
// lib/queue.ts
type QueuedRequest<T> = {
  fn: () => Promise<T>;
  resolve: (value: T) => void;
  reject: (error: Error) => void;
};

class RequestQueue {
  private queue: QueuedRequest<any>[] = [];
  private processing = false;
  private requestsPerSecond = 20; // Conservative rate

  async add<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({ fn, resolve, reject });
      this.process();
    });
  }

  private async process(): Promise<void> {
    if (this.processing) return;
    this.processing = true;

    while (this.queue.length > 0) {
      const request = this.queue.shift()!;

      try {
        const result = await request.fn();
        request.resolve(result);
      } catch (error) {
        request.reject(error as Error);
      }

      // Throttle requests
      await new Promise(r =>
        setTimeout(r, 1000 / this.requestsPerSecond)
      );
    }

    this.processing = false;
  }

  get pending(): number {
    return this.queue.length;
  }
}

export const requestQueue = new RequestQueue();
```

### Step 4: Batch Operations
```typescript
// lib/batch.ts
import { LinearClient } from "@linear/sdk";

interface BatchConfig {
  batchSize: number;
  delayBetweenBatches: number;
}

export async function batchProcess<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  config: BatchConfig = { batchSize: 10, delayBetweenBatches: 1000 }
): Promise<R[]> {
  const results: R[] = [];
  const batches: T[][] = [];

  // Split into batches
  for (let i = 0; i < items.length; i += config.batchSize) {
    batches.push(items.slice(i, i + config.batchSize));
  }

  for (let i = 0; i < batches.length; i++) {
    const batch = batches[i];
    console.log(`Processing batch ${i + 1}/${batches.length}...`);

    // Process batch in parallel
    const batchResults = await Promise.all(batch.map(processor));
    results.push(...batchResults);

    // Delay between batches (except last)
    if (i < batches.length - 1) {
      await new Promise(r => setTimeout(r, config.delayBetweenBatches));
    }
  }

  return results;
}

// Usage example
async function updateManyIssues(
  client: LinearClient,
  updates: { id: string; priority: number }[]
) {
  return batchProcess(
    updates,
    ({ id, priority }) => client.updateIssue(id, { priority }),
    { batchSize: 10, delayBetweenBatches: 2000 }
  );
}
```

### Step 5: Query Optimization
```typescript
// Reduce complexity by limiting fields
const optimizedQuery = `
  query Issues($filter: IssueFilter) {
    issues(filter: $filter, first: 50) {
      nodes {
        id
        identifier
        title
        # Avoid nested connections in loops
      }
    }
  }
`;

// Use SDK efficiently
async function getIssuesOptimized(client: LinearClient, teamKey: string) {
  // Good: Single query with filter
  return client.issues({
    filter: { team: { key: { eq: teamKey } } },
    first: 50,
  });

  // Bad: N+1 queries
  // const teams = await client.teams();
  // for (const team of teams.nodes) {
  //   const issues = await team.issues(); // N queries!
  // }
}
```
