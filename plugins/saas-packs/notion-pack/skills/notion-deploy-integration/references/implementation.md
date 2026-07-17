# Production-Ready Application Modules

The four modules below make a Notion-integrated Node.js app safe for production:
a serverless-safe client singleton, a rate limiter for the 3 req/sec cap, a TTL
response cache, and a health check. Copy each into `src/` and import where noted.

## Notion client singleton (critical for serverless)

Serverless functions recycle containers unpredictably. Creating a new `Client` on every invocation wastes cold-start time and risks hitting rate limits. A module-level singleton reuses the client across warm invocations.

```typescript
// src/notion-client.ts — singleton for serverless environments
import { Client, LogLevel, isNotionClientError, APIErrorCode } from '@notionhq/client';

let client: Client | null = null;

export function getNotionClient(): Client {
  if (!client) {
    if (!process.env.NOTION_TOKEN) {
      throw new Error('NOTION_TOKEN environment variable is not set');
    }
    client = new Client({
      auth: process.env.NOTION_TOKEN,
      logLevel: process.env.NODE_ENV === 'production' ? LogLevel.WARN : LogLevel.DEBUG,
      timeoutMs: 30_000,
    });
  }
  return client;
}
```

## Rate limit handler (Notion enforces 3 requests/second)

Notion returns HTTP 429 with a `Retry-After` header when you exceed the rate limit. The SDK retries automatically, but production apps should add queuing to avoid cascading failures under load.

```typescript
// src/rate-limiter.ts — token bucket for 3 req/sec
export class NotionRateLimiter {
  private queue: Array<{ resolve: () => void }> = [];
  private activeRequests = 0;
  private readonly maxPerSecond = 3;

  async acquire(): Promise<void> {
    if (this.activeRequests < this.maxPerSecond) {
      this.activeRequests++;
      return;
    }
    return new Promise((resolve) => {
      this.queue.push({ resolve });
    });
  }

  release(): void {
    this.activeRequests--;
    if (this.queue.length > 0) {
      const next = this.queue.shift()!;
      this.activeRequests++;
      setTimeout(() => next.resolve(), 1000 / this.maxPerSecond);
    }
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    await this.acquire();
    try {
      return await fn();
    } finally {
      this.release();
    }
  }
}

export const rateLimiter = new NotionRateLimiter();
```

## Response cache (reduce API calls in production)

Notion data that changes infrequently (database schemas, user lists, page metadata) should be cached to stay well under the rate limit.

```typescript
// src/cache.ts — TTL cache for Notion responses
interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

export class NotionCache {
  private store = new Map<string, CacheEntry<unknown>>();
  private readonly defaultTtlMs: number;

  constructor(defaultTtlSeconds = 60) {
    this.defaultTtlMs = defaultTtlSeconds * 1000;
  }

  get<T>(key: string): T | null {
    const entry = this.store.get(key);
    if (!entry || Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return null;
    }
    return entry.data as T;
  }

  set<T>(key: string, data: T, ttlSeconds?: number): void {
    const ttlMs = ttlSeconds ? ttlSeconds * 1000 : this.defaultTtlMs;
    this.store.set(key, { data, expiresAt: Date.now() + ttlMs });
  }

  invalidate(pattern: string): void {
    for (const key of this.store.keys()) {
      if (key.includes(pattern)) this.store.delete(key);
    }
  }
}

export const notionCache = new NotionCache(60); // 60-second default TTL
```

## Health check endpoint (include in every deployment)

```typescript
// src/health.ts — verifies Notion API connectivity
import { getNotionClient } from './notion-client';
import { isNotionClientError } from '@notionhq/client';

export async function healthCheck(): Promise<{
  status: 'healthy' | 'degraded';
  notion: { connected: boolean; latencyMs: number; error?: string };
  timestamp: string;
}> {
  const timestamp = new Date().toISOString();
  const start = Date.now();

  try {
    const notion = getNotionClient();
    await notion.users.me({});
    return {
      status: 'healthy',
      notion: { connected: true, latencyMs: Date.now() - start },
      timestamp,
    };
  } catch (error) {
    const errorCode = isNotionClientError(error) ? error.code : 'unknown';
    return {
      status: 'degraded',
      notion: { connected: false, latencyMs: Date.now() - start, error: errorCode },
      timestamp,
    };
  }
}
```
