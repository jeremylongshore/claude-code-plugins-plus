# Linear Performance Tuning - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Query Optimization

**Minimize Field Selection:**
```typescript
// BAD: Fetching unnecessary fields
const issues = await client.issues();
for (const issue of issues.nodes) {
  // Only using id and title, but fetching everything
  console.log(issue.id, issue.title);
}

// GOOD: Request only needed fields
const query = `
  query MinimalIssues($first: Int!) {
    issues(first: $first) {
      nodes {
        id
        title
      }
    }
  }
`;
```

**Avoid N+1 Queries:**
```typescript
// BAD: N+1 queries
const issues = await client.issues();
for (const issue of issues.nodes) {
  const state = await issue.state; // Separate query per issue!
  console.log(issue.title, state?.name);
}

// GOOD: Use connections and batch loading
const query = `
  query IssuesWithState($first: Int!) {
    issues(first: $first) {
      nodes {
        id
        title
        state {
          name
        }
      }
    }
  }
`;
```

### Step 2: Implement Caching Layer
```typescript
// lib/cache.ts
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL);

interface CacheOptions {
  ttlSeconds: number;
  keyPrefix?: string;
}

export class LinearCache {
  private keyPrefix: string;
  private defaultTtl: number;

  constructor(options: CacheOptions = { ttlSeconds: 300 }) {
    this.keyPrefix = options.keyPrefix || "linear";
    this.defaultTtl = options.ttlSeconds;
  }

  private key(key: string): string {
    return `${this.keyPrefix}:${key}`;
  }

  async get<T>(key: string): Promise<T | null> {
    const data = await redis.get(this.key(key));
    return data ? JSON.parse(data) : null;
  }

  async set<T>(key: string, value: T, ttl = this.defaultTtl): Promise<void> {
    await redis.setex(this.key(key), ttl, JSON.stringify(value));
  }

  async getOrFetch<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl = this.defaultTtl
  ): Promise<T> {
    const cached = await this.get<T>(key);
    if (cached) return cached;

    const data = await fetcher();
    await this.set(key, data, ttl);
    return data;
  }

  async invalidate(pattern: string): Promise<void> {
    const keys = await redis.keys(this.key(pattern));
    if (keys.length) {
      await redis.del(...keys);
    }
  }
}

export const cache = new LinearCache({ ttlSeconds: 300 });
```

### Step 3: Cached Client Wrapper
```typescript
// lib/cached-client.ts
import { LinearClient } from "@linear/sdk";
import { cache } from "./cache";

export class CachedLinearClient {
  private client: LinearClient;

  constructor(apiKey: string) {
    this.client = new LinearClient({ apiKey });
  }

  async getTeams() {
    return cache.getOrFetch(
      "teams",
      async () => {
        const teams = await this.client.teams();
        return teams.nodes.map(t => ({ id: t.id, name: t.name, key: t.key }));
      },
      3600 // Teams rarely change, cache for 1 hour
    );
  }

  async getWorkflowStates(teamKey: string) {
    return cache.getOrFetch(
      `states:${teamKey}`,
      async () => {
        const teams = await this.client.teams({
          filter: { key: { eq: teamKey } },
        });
        const states = await teams.nodes[0].states();
        return states.nodes.map(s => ({
          id: s.id,
          name: s.name,
          type: s.type,
        }));
      },
      3600 // States rarely change
    );
  }

  async getIssue(identifier: string, maxAge = 60) {
    return cache.getOrFetch(
      `issue:${identifier}`,
      async () => {
        const issue = await this.client.issue(identifier);
        const state = await issue.state;
        return {
          id: issue.id,
          identifier: issue.identifier,
          title: issue.title,
          state: state?.name,
          priority: issue.priority,
        };
      },
      maxAge
    );
  }

  // Invalidate cache when we know data changed
  async createIssue(input: any) {
    const result = await this.client.createIssue(input);
    await cache.invalidate("issues:*");
    return result;
  }
}
```

### Step 4: Request Batching
```typescript
// lib/batcher.ts
interface BatchRequest<T> {
  key: string;
  resolve: (value: T) => void;
  reject: (error: Error) => void;
}

class RequestBatcher<T> {
  private queue: BatchRequest<T>[] = [];
  private timeout: NodeJS.Timeout | null = null;
  private batchSize: number;
  private delayMs: number;
  private batchFetcher: (keys: string[]) => Promise<Map<string, T>>;

  constructor(options: {
    batchSize?: number;
    delayMs?: number;
    batchFetcher: (keys: string[]) => Promise<Map<string, T>>;
  }) {
    this.batchSize = options.batchSize || 50;
    this.delayMs = options.delayMs || 10;
    this.batchFetcher = options.batchFetcher;
  }

  async load(key: string): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({ key, resolve, reject });
      this.scheduleFlush();
    });
  }

  private scheduleFlush(): void {
    if (this.queue.length >= this.batchSize) {
      this.flush();
      return;
    }

    if (!this.timeout) {
      this.timeout = setTimeout(() => this.flush(), this.delayMs);
    }
  }

  private async flush(): Promise<void> {
    if (this.timeout) {
      clearTimeout(this.timeout);
      this.timeout = null;
    }

    const batch = this.queue.splice(0, this.batchSize);
    if (batch.length === 0) return;

    try {
      const keys = batch.map(r => r.key);
      const results = await this.batchFetcher(keys);

      for (const request of batch) {
        const result = results.get(request.key);
        if (result !== undefined) {
          request.resolve(result);
        } else {
          request.reject(new Error(`Not found: ${request.key}`));
        }
      }
    } catch (error) {
      for (const request of batch) {
        request.reject(error as Error);
      }
    }
  }
}

// Usage
const issueBatcher = new RequestBatcher<any>({
  batchFetcher: async (identifiers) => {
    const issues = await client.issues({
      filter: { identifier: { in: identifiers } },
    });
    return new Map(issues.nodes.map(i => [i.identifier, i]));
  },
});

// These will be batched into a single request
const [issue1, issue2, issue3] = await Promise.all([
  issueBatcher.load("ENG-1"),
  issueBatcher.load("ENG-2"),
  issueBatcher.load("ENG-3"),
]);
```

### Step 5: Connection Pooling
```typescript
// lib/client-pool.ts
import { LinearClient } from "@linear/sdk";

class ClientPool {
  private clients: LinearClient[] = [];
  private maxClients: number;
  private currentIndex = 0;

  constructor(apiKey: string, maxClients = 5) {
    this.maxClients = maxClients;
    for (let i = 0; i < maxClients; i++) {
      this.clients.push(new LinearClient({ apiKey }));
    }
  }

  getClient(): LinearClient {
    const client = this.clients[this.currentIndex];
    this.currentIndex = (this.currentIndex + 1) % this.maxClients;
    return client;
  }
}

export const clientPool = new ClientPool(process.env.LINEAR_API_KEY!);
```

### Step 6: Query Complexity Monitoring
```typescript
// lib/complexity-monitor.ts
interface QueryStats {
  complexity: number;
  duration: number;
  timestamp: Date;
}

class ComplexityMonitor {
  private stats: QueryStats[] = [];
  private maxStats = 1000;

  record(complexity: number, duration: number): void {
    this.stats.push({
      complexity,
      duration,
      timestamp: new Date(),
    });

    if (this.stats.length > this.maxStats) {
      this.stats = this.stats.slice(-this.maxStats);
    }
  }

  getAverageComplexity(): number {
    if (this.stats.length === 0) return 0;
    return this.stats.reduce((a, b) => a + b.complexity, 0) / this.stats.length;
  }

  getSlowQueries(thresholdMs = 1000): QueryStats[] {
    return this.stats.filter(s => s.duration > thresholdMs);
  }

  getComplexQueries(threshold = 1000): QueryStats[] {
    return this.stats.filter(s => s.complexity > threshold);
  }
}

export const monitor = new ComplexityMonitor();
```

## Performance Checklist

- [ ] Only request needed fields
- [ ] Use batch queries for multiple items
- [ ] Implement caching for static data
- [ ] Add cache invalidation on writes
- [ ] Monitor query complexity
- [ ] Use pagination for large datasets
- [ ] Avoid N+1 query patterns
