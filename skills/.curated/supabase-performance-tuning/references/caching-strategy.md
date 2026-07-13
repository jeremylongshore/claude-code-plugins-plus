# Caching Strategy

## Caching Strategy

### Response Caching

```typescript
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, any>({
  max: 1000,
  ttl: 30000, // 1 minute
  updateAgeOnGet: true,
});

async function cachedSupabaseRequest<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl?: number
): Promise<T> {
  const cached = cache.get(key);
  if (cached) return cached as T;

  const result = await fetcher();
  cache.set(key, result, { ttl });
  return result;
}
```

### Redis Caching (Distributed)

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function cachedWithRedis<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlSeconds = 60
): Promise<T> {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const result = await fetcher();
  await redis.setex(key, ttlSeconds, JSON.stringify(result));
  return result;
}
```
