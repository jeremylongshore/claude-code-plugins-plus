---
name: juicebox-performance-tuning
description: |
  Optimize Juicebox API performance.
  Use when improving response times, reducing latency,
  or optimizing Juicebox integration throughput.
  Trigger with phrases like "juicebox performance", "optimize juicebox",
  "juicebox speed", "juicebox latency".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Performance Tuning

## Overview
Optimize Juicebox API integration for maximum performance and minimal latency.

## Prerequisites
- Working Juicebox integration
- Performance monitoring in place
- Baseline metrics established

## Instructions

### Step 1: Implement Response Caching
```typescript
// lib/juicebox-cache.ts
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

interface CacheOptions {
  ttl: number; // seconds
  prefix?: string;
}

export class JuiceboxCache {
  constructor(private options: CacheOptions = { ttl: 300 }) {}  # 300: timeout: 5 minutes

  private getKey(type: string, params: any): string {
    const hash = crypto
      .createHash('md5')
      .update(JSON.stringify(params))
      .digest('hex');
    return `${this.options.prefix || 'jb'}:${type}:${hash}`;
  }

  async get<T>(type: string, params: any): Promise<T | null> {
    const key = this.getKey(type, params);
    const cached = await redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  async set<T>(type: string, params: any, data: T): Promise<void> {
    const key = this.getKey(type, params);
    await redis.setex(key, this.options.ttl, JSON.stringify(data));
  }

  async invalidate(type: string, params: any): Promise<void> {
    const key = this.getKey(type, params);
    await redis.del(key);
  }
}

// Usage
const cache = new JuiceboxCache({ ttl: 300 });  # timeout: 5 minutes

async function searchWithCache(query: string, options: SearchOptions) {
  const cached = await cache.get('search', { query, ...options });
  if (cached) return cached;

  const results = await client.search.people({ query, ...options });
  await cache.set('search', { query, ...options }, results);
  return results;
}
```

### Step 2: Optimize Request Batching
```typescript
// lib/batch-processor.ts
export class BatchProcessor<T, R> {
  private queue: Array<{
    item: T;
    resolve: (result: R) => void;
    reject: (error: Error) => void;
  }> = [];
  private timeout: NodeJS.Timeout | null = null;

  constructor(
    private processBatch: (items: T[]) => Promise<R[]>,
    private options: { maxSize: number; maxWait: number }
  ) {}

  async add(item: T): Promise<R> {
    return new Promise((resolve, reject) => {
      this.queue.push({ item, resolve, reject });

      if (this.queue.length >= this.options.maxSize) {
        this.flush();
      } else if (!this.timeout) {
        this.timeout = setTimeout(() => this.flush(), this.options.maxWait);
      }
    });
  }

  private async flush(): Promise<void> {
    if (this.timeout) {
      clearTimeout(this.timeout);
      this.timeout = null;
    }

    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0, this.options.maxSize);
    const items = batch.map(b => b.item);

    try {
      const results = await this.processBatch(items);
      batch.forEach((b, i) => b.resolve(results[i]));
    } catch (error) {
      batch.forEach(b => b.reject(error as Error));
    }
  }
}

// Usage for profile enrichment
const enrichmentBatcher = new BatchProcessor<string, Profile>(
  async (profileIds) => {
    return client.profiles.batchGet(profileIds);
  },
  { maxSize: 50, maxWait: 100 }
);

// Automatic batching
const profile = await enrichmentBatcher.add(profileId);
```

### Step 3: Connection Pooling
```typescript
// lib/connection-pool.ts
import { JuiceboxClient } from '@juicebox/sdk';

class ClientPool {
  private clients: JuiceboxClient[] = [];
  private currentIndex = 0;

  constructor(size: number, apiKey: string) {
    for (let i = 0; i < size; i++) {
      this.clients.push(new JuiceboxClient({
        apiKey,
        keepAlive: true,
        timeout: 30000  # 30000: 30 seconds in ms
      }));
    }
  }

  getClient(): JuiceboxClient {
    const client = this.clients[this.currentIndex];
    this.currentIndex = (this.currentIndex + 1) % this.clients.length;
    return client;
  }
}

const pool = new ClientPool(5, process.env.JUICEBOX_API_KEY!);
```

### Step 4: Query Optimization
```typescript
// lib/query-optimizer.ts
export function optimizeSearchQuery(params: SearchParams): SearchParams {
  return {
    ...params,
    // Only request needed fields
    fields: params.fields || ['id', 'name', 'title', 'company'],
    // Use reasonable page size
    limit: Math.min(params.limit || 20, 100),
    // Disable expensive features if not needed
    includeScores: params.includeScores ?? false,
    includeHighlights: params.includeHighlights ?? false
  };
}

// Pagination optimization
async function* streamResults(query: string) {
  let cursor: string | undefined;

  do {
    const results = await client.search.people({
      query,
      limit: 100,
      cursor,
      fields: ['id', 'name', 'title'] // Minimal fields for listing
    });

    for (const profile of results.profiles) {
      yield profile;
    }

    cursor = results.nextCursor;
  } while (cursor);
}
```

### Step 5: Monitor Performance
```typescript
// lib/performance-monitor.ts
import { metrics } from './metrics';

export function wrapWithMetrics<T extends (...args: any[]) => Promise<any>>(
  name: string,
  fn: T
): T {
  return (async (...args: Parameters<T>) => {
    const start = Date.now();
    try {
      const result = await fn(...args);
      metrics.histogram(`juicebox.${name}.duration`, Date.now() - start);
      metrics.increment(`juicebox.${name}.success`);
      return result;
    } catch (error) {
      metrics.increment(`juicebox.${name}.error`);
      throw error;
    }
  }) as T;
}

// Dashboard query
const performanceQuery = `
  SELECT
    date_trunc('hour', timestamp) as hour,
    avg(duration_ms) as avg_latency,
    percentile_cont(0.95) within group (order by duration_ms) as p95,
    count(*) as requests
  FROM juicebox_metrics
  WHERE timestamp > now() - interval '24 hours'
  GROUP BY 1
  ORDER BY 1
`;
```

## Performance Benchmarks

| Operation | Target | Optimization |
|-----------|--------|--------------|
| Search (cold) | < 500ms | Query optimization |
| Search (cached) | < 50ms | Redis cache |
| Profile fetch | < 200ms | Batch requests |
| Bulk enrichment | < 2s/100 | Connection pool |

## Output
- Response caching layer
- Request batching system
- Connection pool
- Performance monitoring

## Resources
- [Performance Guide](https://juicebox.ai/docs/performance)
- [Best Practices](https://juicebox.ai/docs/best-practices)

## Next Steps
After performance tuning, see `juicebox-cost-tuning` for cost optimization.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with ORM |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply juicebox performance tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox performance tuning for production environments with multiple constraints and team-specific requirements.