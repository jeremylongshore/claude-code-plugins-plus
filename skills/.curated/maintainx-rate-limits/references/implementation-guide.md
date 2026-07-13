# MaintainX Rate Limits - Implementation Guide

> Full implementation details and code examples for the `maintainx-rate-limits` skill.

# MaintainX Rate Limits

## Overview

Handle MaintainX API rate limits gracefully with exponential backoff, pagination, and request queuing.

## Prerequisites

- MaintainX SDK installed
- Understanding of async/await patterns
- Familiarity with cursor-based pagination

## MaintainX API Limits

| Aspect | Limit | Notes |
|--------|-------|-------|
| Requests per minute | Varies by plan | Check your subscription |
| Page size | 100 max | Default varies by endpoint |
| Concurrent requests | Recommended: 5 | Avoid parallel bursts |

## Instructions

### Step 1: Exponential Backoff with Jitter

```typescript
// src/utils/rate-limit.ts

interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterMs: number;
}

const defaultConfig: RetryConfig = {
  maxRetries: 5,
  baseDelayMs: 1000,
  maxDelayMs: 60000,
  jitterMs: 500,
};

async function withExponentialBackoff<T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {}
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

      // Only retry on rate limits (429) and server errors (5xx)
      if (status !== 429 && (status < 500 || status >= 600)) {
        throw error;
      }

      // Check for Retry-After header
      const retryAfter = error.response?.headers?.['retry-after'];
      let delay: number;

      if (retryAfter) {
        delay = parseInt(retryAfter) * 1000;
      } else {
        // Exponential backoff with jitter
        const exponentialDelay = baseDelayMs * Math.pow(2, attempt);
        const jitter = Math.random() * jitterMs;
        delay = Math.min(exponentialDelay + jitter, maxDelayMs);
      }

      console.log(
        `Rate limited (attempt ${attempt + 1}/${maxRetries}). ` +
        `Retrying in ${Math.round(delay)}ms...`
      );

      await new Promise(r => setTimeout(r, delay));
    }
  }

  throw new Error('Unreachable');
}

// Usage example
async function fetchWithRetry(client: MaintainXClient) {
  return withExponentialBackoff(
    () => client.getWorkOrders({ limit: 100 }),
    { maxRetries: 3 }
  );
}
```

### Step 2: Request Queue for Concurrency Control

```typescript
// src/utils/request-queue.ts
import PQueue from 'p-queue';

class RateLimitedClient {
  private queue: PQueue;
  private client: MaintainXClient;

  constructor(client: MaintainXClient, options?: { concurrency?: number; interval?: number }) {
    this.client = client;

    // Limit concurrent requests and requests per interval
    this.queue = new PQueue({
      concurrency: options?.concurrency || 5,
      interval: options?.interval || 1000,
      intervalCap: 10,  // Max requests per interval
    });
  }

  async getWorkOrders(params?: any) {
    return this.queue.add(() =>
      withExponentialBackoff(() => this.client.getWorkOrders(params))
    );
  }

  async getAssets(params?: any) {
    return this.queue.add(() =>
      withExponentialBackoff(() => this.client.getAssets(params))
    );
  }

  async createWorkOrder(data: any) {
    return this.queue.add(() =>
      withExponentialBackoff(() => this.client.createWorkOrder(data))
    );
  }

  // Get queue stats
  getQueueStats() {
    return {
      pending: this.queue.pending,
      size: this.queue.size,
    };
  }

  // Wait for all queued requests to complete
  async drain() {
    await this.queue.onIdle();
  }
}

// Usage
const rateLimitedClient = new RateLimitedClient(client, {
  concurrency: 5,
  interval: 1000,
});

// These will be queued and rate-limited automatically
await Promise.all([
  rateLimitedClient.getWorkOrders(),
  rateLimitedClient.getAssets(),
  rateLimitedClient.getWorkOrders({ status: 'OPEN' }),
]);
```

### Step 3: Cursor-Based Pagination

```typescript
// src/utils/pagination.ts

interface PaginationOptions {
  limit?: number;
  maxPages?: number;
  delayBetweenPages?: number;
}

// Generic paginator for any endpoint
async function* paginate<T>(
  fetchPage: (cursor?: string) => Promise<{ items: T[]; nextCursor: string | null }>,
  options: PaginationOptions = {}
): AsyncGenerator<T[], void, unknown> {
  const { limit = 100, maxPages = Infinity, delayBetweenPages = 100 } = options;

  let cursor: string | undefined;
  let pageCount = 0;

  do {
    const response = await fetchPage(cursor);
    yield response.items;

    cursor = response.nextCursor || undefined;
    pageCount++;

    // Delay between pages to avoid rate limits
    if (cursor && delayBetweenPages > 0) {
      await new Promise(r => setTimeout(r, delayBetweenPages));
    }
  } while (cursor && pageCount < maxPages);
}

// Work order paginator
async function* paginateWorkOrders(
  client: MaintainXClient,
  params: any = {},
  options: PaginationOptions = {}
): AsyncGenerator<WorkOrder[], void, unknown> {
  yield* paginate(
    async (cursor) => {
      const response = await withExponentialBackoff(() =>
        client.getWorkOrders({ ...params, cursor, limit: options.limit || 100 })
      );
      return {
        items: response.workOrders,
        nextCursor: response.nextCursor,
      };
    },
    options
  );
}

// Collect all pages
async function getAllWorkOrders(
  client: MaintainXClient,
  params?: any,
  options?: PaginationOptions
): Promise<WorkOrder[]> {
  const allWorkOrders: WorkOrder[] = [];

  for await (const batch of paginateWorkOrders(client, params, options)) {
    allWorkOrders.push(...batch);
    console.log(`Fetched ${allWorkOrders.length} work orders...`);
  }

  return allWorkOrders;
}

// Usage
async function fetchAllOpenWorkOrders(client: MaintainXClient) {
  const workOrders = await getAllWorkOrders(
    client,
    { status: 'OPEN' },
    {
      limit: 100,
      maxPages: 50,  // Safety limit
      delayBetweenPages: 200,
    }
  );

  console.log(`Total open work orders: ${workOrders.length}`);
  return workOrders;
}
```

### Step 4: Rate Limit Monitor

```typescript
// src/utils/rate-monitor.ts

class RateLimitMonitor {
  private requestCount = 0;
  private windowStart = Date.now();
  private readonly windowMs = 60000;  // 1 minute window
  private readonly maxRequests = 60;  // Adjust based on your plan

  recordRequest() {
    const now = Date.now();

    // Reset window if expired
    if (now - this.windowStart > this.windowMs) {
      this.requestCount = 0;
      this.windowStart = now;
    }

    this.requestCount++;
  }

  shouldThrottle(): boolean {
    return this.requestCount >= this.maxRequests * 0.8;  // 80% threshold
  }

  getWaitTime(): number {
    if (!this.shouldThrottle()) return 0;

    const windowEnd = this.windowStart + this.windowMs;
    return Math.max(0, windowEnd - Date.now());
  }

  getStats() {
    return {
      requestCount: this.requestCount,
      windowRemaining: Math.max(0, this.windowMs - (Date.now() - this.windowStart)),
      shouldThrottle: this.shouldThrottle(),
    };
  }
}

// Integrate with client
class MonitoredMaintainXClient {
  private client: MaintainXClient;
  private monitor: RateLimitMonitor;

  constructor(apiKey: string) {
    this.client = new MaintainXClient();
    this.monitor = new RateLimitMonitor();
  }

  private async throttledRequest<T>(operation: () => Promise<T>): Promise<T> {
    // Pre-check throttling
    if (this.monitor.shouldThrottle()) {
      const waitTime = this.monitor.getWaitTime();
      console.log(`Proactively throttling. Waiting ${waitTime}ms...`);
      await new Promise(r => setTimeout(r, waitTime));
    }

    this.monitor.recordRequest();
    return operation();
  }

  async getWorkOrders(params?: any) {
    return this.throttledRequest(() => this.client.getWorkOrders(params));
  }

  // Add other methods similarly...
}
```

### Step 5: Batch Operations with Rate Limiting

```typescript
// src/utils/batch.ts

interface BatchConfig {
  batchSize: number;
  delayBetweenBatches: number;
  maxConcurrent: number;
}

async function processBatch<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  config: Partial<BatchConfig> = {}
): Promise<R[]> {
  const { batchSize = 10, delayBetweenBatches = 500, maxConcurrent = 5 } = config;

  const results: R[] = [];

  // Process in batches
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);

    console.log(`Processing batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(items.length / batchSize)}...`);

    // Process batch items with limited concurrency
    const queue = new PQueue({ concurrency: maxConcurrent });
    const batchPromises = batch.map(item =>
      queue.add(() => withExponentialBackoff(() => processor(item)))
    );

    const batchResults = await Promise.all(batchPromises);
    results.push(...batchResults);

    // Delay between batches
    if (i + batchSize < items.length) {
      await new Promise(r => setTimeout(r, delayBetweenBatches));
    }
  }

  return results;
}

// Example: Create multiple work orders with rate limiting
async function createMultipleWorkOrders(
  client: MaintainXClient,
  workOrdersData: Partial<WorkOrder>[]
): Promise<WorkOrder[]> {
  return processBatch(
    workOrdersData,
    data => client.createWorkOrder(data),
    {
      batchSize: 5,
      delayBetweenBatches: 1000,
      maxConcurrent: 3,
    }
  );
}
```

## Output

- Resilient API calls with automatic retry
- Proper pagination handling
- Request queuing and throttling
- Rate limit monitoring

## Error Handling

| Scenario | Strategy |
|----------|----------|
| 429 Rate Limited | Exponential backoff with jitter |
| Retry-After header | Honor the specified wait time |
| Burst requests | Use request queue |
| Large data sets | Use pagination with delays |

## Best Practices

1. **Start conservative**: Begin with lower limits and increase gradually
2. **Use pagination**: Never try to fetch all data in one request
3. **Add delays**: Include delays between batch operations
4. **Monitor usage**: Track request counts and adjust
5. **Handle errors gracefully**: Always implement retry logic

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [p-queue Documentation](https://github.com/sindresorhus/p-queue)
- [Rate Limiting Best Practices](https://www.merge.dev/blog/api-rate-limit-best-practices)

## Next Steps

For security configuration, see `maintainx-security-basics`.
