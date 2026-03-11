# MaintainX Performance Tuning - Implementation Guide

> Full implementation details and code examples for the `maintainx-performance-tuning` skill.

# MaintainX Performance Tuning

## Overview

Optimize your MaintainX integration for maximum performance with caching, efficient queries, and connection pooling.

## Prerequisites

- MaintainX integration working
- Redis or in-memory cache available
- Performance metrics baseline

## Performance Metrics Baseline

| Operation | Target | Acceptable |
|-----------|--------|------------|
| List work orders | <500ms | <1000ms |
| Get single work order | <200ms | <500ms |
| Create work order | <500ms | <1000ms |
| Paginated fetch (100 items) | <1000ms | <2000ms |

## Instructions

### Step 1: Response Caching

```typescript
// src/cache/cache-manager.ts
import { Redis } from 'ioredis';

interface CacheConfig {
  ttlSeconds: number;
  prefix: string;
}

class CacheManager {
  private redis: Redis;
  private prefix: string;

  constructor(redisUrl: string, prefix = 'maintainx') {
    this.redis = new Redis(redisUrl);
    this.prefix = prefix;
  }

  private key(key: string): string {
    return `${this.prefix}:${key}`;
  }

  async get<T>(key: string): Promise<T | null> {
    const data = await this.redis.get(this.key(key));
    if (!data) return null;

    return JSON.parse(data) as T;
  }

  async set<T>(key: string, value: T, ttlSeconds = 300): Promise<void> {
    await this.redis.set(
      this.key(key),
      JSON.stringify(value),
      'EX',
      ttlSeconds
    );
  }

  async delete(key: string): Promise<void> {
    await this.redis.del(this.key(key));
  }

  async invalidatePattern(pattern: string): Promise<void> {
    const keys = await this.redis.keys(this.key(pattern));
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
}

// Cached API client wrapper
class CachedMaintainXClient {
  private client: MaintainXClient;
  private cache: CacheManager;

  constructor(client: MaintainXClient, cache: CacheManager) {
    this.client = client;
    this.cache = cache;
  }

  async getWorkOrder(id: string): Promise<WorkOrder> {
    const cacheKey = `workorder:${id}`;

    // Check cache first
    const cached = await this.cache.get<WorkOrder>(cacheKey);
    if (cached) {
      console.log(`Cache hit: ${cacheKey}`);
      return cached;
    }

    // Fetch from API
    const workOrder = await this.client.getWorkOrder(id);

    // Cache for 5 minutes
    await this.cache.set(cacheKey, workOrder, 300);

    return workOrder;
  }

  async getWorkOrders(params?: WorkOrderQueryParams): Promise<WorkOrderListResponse> {
    // Cache list queries for shorter duration
    const cacheKey = `workorders:${JSON.stringify(params || {})}`;

    const cached = await this.cache.get<WorkOrderListResponse>(cacheKey);
    if (cached) {
      return cached;
    }

    const response = await this.client.getWorkOrders(params);
    await this.cache.set(cacheKey, response, 60);  // 1 minute

    return response;
  }

  async createWorkOrder(data: CreateWorkOrderInput): Promise<WorkOrder> {
    const workOrder = await this.client.createWorkOrder(data);

    // Invalidate list cache
    await this.cache.invalidatePattern('workorders:*');

    return workOrder;
  }

  // Invalidate cache when data changes
  async invalidateWorkOrder(id: string): Promise<void> {
    await this.cache.delete(`workorder:${id}`);
    await this.cache.invalidatePattern('workorders:*');
  }
}
```

### Step 2: Connection Pooling

```typescript
// src/api/connection-pool.ts
import axios, { AxiosInstance } from 'axios';
import https from 'https';
import http from 'http';

function createOptimizedClient(): AxiosInstance {
  // HTTP agent with keep-alive
  const httpsAgent = new https.Agent({
    keepAlive: true,
    keepAliveMsecs: 30000,
    maxSockets: 50,
    maxFreeSockets: 10,
    timeout: 30000,
  });

  const httpAgent = new http.Agent({
    keepAlive: true,
    keepAliveMsecs: 30000,
    maxSockets: 50,
    maxFreeSockets: 10,
    timeout: 30000,
  });

  return axios.create({
    baseURL: 'https://api.getmaintainx.com/v1',
    timeout: 30000,
    httpsAgent,
    httpAgent,
    headers: {
      'Authorization': `Bearer ${process.env.MAINTAINX_API_KEY}`,
      'Content-Type': 'application/json',
      'Connection': 'keep-alive',
    },
    // Response compression
    decompress: true,
  });
}

export { createOptimizedClient };
```

### Step 3: Efficient Pagination

```typescript
// src/utils/efficient-pagination.ts

interface EfficientPaginationOptions {
  batchSize: number;
  maxConcurrent: number;
  delayBetweenBatches: number;
}

// Stream-based pagination for memory efficiency
async function* streamWorkOrders(
  client: MaintainXClient,
  params: WorkOrderQueryParams = {},
  options: Partial<EfficientPaginationOptions> = {}
): AsyncGenerator<WorkOrder, void, unknown> {
  const { batchSize = 100 } = options;
  let cursor: string | undefined;

  do {
    const response = await client.getWorkOrders({
      ...params,
      cursor,
      limit: batchSize,
    });

    for (const workOrder of response.workOrders) {
      yield workOrder;
    }

    cursor = response.nextCursor || undefined;
  } while (cursor);
}

// Parallel fetch with cursor prefetch
async function fetchAllWorkOrdersOptimized(
  client: MaintainXClient,
  params: WorkOrderQueryParams = {}
): Promise<WorkOrder[]> {
  const allWorkOrders: WorkOrder[] = [];
  let cursor: string | undefined;
  let prefetchPromise: Promise<WorkOrderListResponse> | null = null;

  do {
    // Use prefetched response if available
    let response: WorkOrderListResponse;
    if (prefetchPromise) {
      response = await prefetchPromise;
    } else {
      response = await client.getWorkOrders({ ...params, cursor, limit: 100 });
    }

    allWorkOrders.push(...response.workOrders);
    cursor = response.nextCursor || undefined;

    // Prefetch next page while processing current
    if (cursor) {
      prefetchPromise = client.getWorkOrders({ ...params, cursor, limit: 100 });
    } else {
      prefetchPromise = null;
    }
  } while (cursor);

  return allWorkOrders;
}

// Usage with memory-efficient streaming
async function processLargeDataset(client: MaintainXClient) {
  let processed = 0;

  for await (const workOrder of streamWorkOrders(client, { status: 'DONE' })) {
    // Process one at a time - no memory buildup
    await processWorkOrder(workOrder);
    processed++;

    if (processed % 100 === 0) {
      console.log(`Processed ${processed} work orders`);
    }
  }
}
```

### Step 4: Request Deduplication

```typescript
// src/utils/deduplication.ts

class RequestDeduplicator {
  private pending: Map<string, Promise<any>> = new Map();

  async dedupe<T>(key: string, operation: () => Promise<T>): Promise<T> {
    // Check for in-flight request
    if (this.pending.has(key)) {
      console.log(`Deduplicating request: ${key}`);
      return this.pending.get(key) as Promise<T>;
    }

    // Create new request
    const promise = operation().finally(() => {
      this.pending.delete(key);
    });

    this.pending.set(key, promise);
    return promise;
  }
}

// Usage in client
class DeduplicatedMaintainXClient {
  private client: MaintainXClient;
  private deduper: RequestDeduplicator;

  constructor(client: MaintainXClient) {
    this.client = client;
    this.deduper = new RequestDeduplicator();
  }

  async getWorkOrder(id: string): Promise<WorkOrder> {
    return this.deduper.dedupe(
      `workorder:${id}`,
      () => this.client.getWorkOrder(id)
    );
  }

  async getAsset(id: string): Promise<Asset> {
    return this.deduper.dedupe(
      `asset:${id}`,
      () => this.client.getAsset(id)
    );
  }
}
```

### Step 5: Batch Data Loading

```typescript
// src/utils/dataloader.ts
import DataLoader from 'dataloader';

// Batch load work orders
const workOrderLoader = new DataLoader<string, WorkOrder>(
  async (ids: readonly string[]) => {
    console.log(`Batch loading ${ids.length} work orders`);

    // Fetch all in parallel (or single batch request if API supports)
    const workOrders = await Promise.all(
      ids.map(id => client.getWorkOrder(id))
    );

    // Return in same order as input
    return workOrders;
  },
  {
    maxBatchSize: 20,
    batchScheduleFn: (callback) => setTimeout(callback, 10),  // 10ms batching window
    cache: true,
  }
);

// Batch load assets
const assetLoader = new DataLoader<string, Asset>(
  async (ids: readonly string[]) => {
    const assets = await Promise.all(
      ids.map(id => client.getAsset(id))
    );
    return assets;
  }
);

// Usage: multiple calls get batched
async function loadWorkOrdersWithAssets(workOrderIds: string[]) {
  // These will be batched into fewer API calls
  const workOrders = await Promise.all(
    workOrderIds.map(id => workOrderLoader.load(id))
  );

  // Load associated assets
  const assetIds = workOrders
    .map(wo => wo.assetId)
    .filter(Boolean) as string[];

  const assets = await Promise.all(
    assetIds.map(id => assetLoader.load(id))
  );

  return { workOrders, assets };
}
```

### Step 6: Performance Monitoring

```typescript
// src/monitoring/performance.ts
import { performance } from 'perf_hooks';

interface PerformanceMetric {
  operation: string;
  duration: number;
  timestamp: Date;
  success: boolean;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];

  async measure<T>(
    operation: string,
    fn: () => Promise<T>
  ): Promise<T> {
    const start = performance.now();
    let success = true;

    try {
      return await fn();
    } catch (error) {
      success = false;
      throw error;
    } finally {
      const duration = performance.now() - start;

      this.metrics.push({
        operation,
        duration,
        timestamp: new Date(),
        success,
      });

      // Log slow operations
      if (duration > 1000) {
        console.warn(`Slow operation: ${operation} took ${duration.toFixed(0)}ms`);
      }
    }
  }

  getStats(operation?: string): any {
    const filtered = operation
      ? this.metrics.filter(m => m.operation === operation)
      : this.metrics;

    if (filtered.length === 0) return null;

    const durations = filtered.map(m => m.duration);

    return {
      count: filtered.length,
      avg: durations.reduce((a, b) => a + b, 0) / durations.length,
      min: Math.min(...durations),
      max: Math.max(...durations),
      p95: percentile(durations, 95),
      p99: percentile(durations, 99),
      successRate: filtered.filter(m => m.success).length / filtered.length,
    };
  }
}

function percentile(arr: number[], p: number): number {
  const sorted = [...arr].sort((a, b) => a - b);
  const index = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[index];
}

// Usage
const monitor = new PerformanceMonitor();

const workOrders = await monitor.measure(
  'getWorkOrders',
  () => client.getWorkOrders({ limit: 100 })
);

console.log('Performance stats:', monitor.getStats('getWorkOrders'));
```

## Output

- Caching layer implemented
- Connection pooling configured
- Efficient pagination patterns
- Request deduplication
- DataLoader for batch loading
- Performance monitoring

## Performance Checklist

- [ ] Response caching configured
- [ ] Connection pooling enabled
- [ ] Pagination uses streaming where appropriate
- [ ] Duplicate requests deduplicated
- [ ] Batch loading for related data
- [ ] Performance metrics collected
- [ ] Slow operations identified and optimized

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [DataLoader Documentation](https://github.com/graphql/dataloader)
- [Node.js Performance Best Practices](https://nodejs.org/en/docs/guides/dont-block-the-event-loop)

## Next Steps

For cost optimization, see `maintainx-cost-tuning`.
