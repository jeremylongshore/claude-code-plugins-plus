# Gamma Performance Tuning - Implementation Details

## Client Configuration Optimization

```typescript
import { GammaClient } from '@gamma/sdk';

const gamma = new GammaClient({
  apiKey: process.env.GAMMA_API_KEY,
  timeout: 30000,
  keepAlive: true,
  maxSockets: 10,
  retries: 3,
  retryDelay: 1000,
  retryCondition: (err) => err.status >= 500 || err.status === 429,
  compression: true,
});
```

## Response Caching

```typescript
import NodeCache from 'node-cache';

const cache = new NodeCache({ stdTTL: 300, checkperiod: 60 });

async function getCachedPresentation(id: string) {
  const cacheKey = `presentation:${id}`;
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  const presentation = await gamma.presentations.get(id);
  cache.set(cacheKey, presentation);
  return presentation;
}

gamma.on('presentation.updated', (event) => {
  cache.del(`presentation:${event.data.id}`);
});
```

## Parallel Request Optimization

```typescript
import pLimit from 'p-limit';

const limit = pLimit(5);

async function getParallel(ids: string[]) {
  return Promise.all(
    ids.map(id => limit(() => gamma.presentations.get(id)))
  );
}

// Batch API if available
async function getBatch(ids: string[]) {
  return gamma.presentations.getBatch(ids);
}
```

## Lazy Loading and Pagination

```typescript
async function* getAllPresentations() {
  let cursor: string | undefined;
  do {
    const page = await gamma.presentations.list({ limit: 100, cursor });
    for (const presentation of page.items) {
      yield presentation;
    }
    cursor = page.nextCursor;
  } while (cursor);
}
```

## Request Optimization

```typescript
// Only request needed fields
const presentation = await gamma.presentations.get(id, {
  fields: ['id', 'title', 'url', 'updatedAt'],
});

// Use async pattern for creation
const { id, statusUrl } = await gamma.presentations.create({
  title: 'My Presentation',
  prompt: 'AI content',
  returnImmediately: true,
});
```

## Connection Pooling

```typescript
import http from 'http';
import https from 'https';

const httpAgent = new http.Agent({
  keepAlive: true,
  maxSockets: 25,
  maxFreeSockets: 10,
  timeout: 60000,
});

const httpsAgent = new https.Agent({
  keepAlive: true,
  maxSockets: 25,
  maxFreeSockets: 10,
  timeout: 60000,
});

const gamma = new GammaClient({
  apiKey: process.env.GAMMA_API_KEY,
  httpAgent,
  httpsAgent,
});
```

## Monitoring Setup

```typescript
import { performance } from 'perf_hooks';

async function timedRequest<T>(name: string, fn: () => Promise<T>): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    const duration = performance.now() - start;
    metrics.recordLatency(name, duration);
    return result;
  } catch (err) {
    const duration = performance.now() - start;
    console.log(`[PERF] ${name} FAILED: ${duration.toFixed(2)}ms`);
    throw err;
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
