# Apollo Performance Tuning - Implementation Guide

> Full implementation details and code examples for the `apollo-performance-tuning` skill.

# Apollo Performance Tuning

## Overview
Optimize Apollo.io API performance through caching, connection pooling, request optimization, and efficient data handling.

## Performance Benchmarks

| Operation | Target Latency | Acceptable | Poor |
|-----------|---------------|------------|------|
| People Search | < 500ms | 500-1500ms | > 1500ms |
| Person Enrichment | < 1000ms | 1-3s | > 3s |
| Org Enrichment | < 800ms | 800ms-2s | > 2s |
| Bulk Operations | < 5s/100 | 5-15s/100 | > 15s/100 |

## 1. Connection Pooling

```typescript
// src/lib/apollo/http-agent.ts
import https from 'https';
import { Agent } from 'https';

// Reuse TCP connections
const httpsAgent = new Agent({
  keepAlive: true,
  keepAliveMsecs: 30000,
  maxSockets: 10,
  maxFreeSockets: 5,
  timeout: 30000,
});

export const apolloClient = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  httpsAgent,
  timeout: 30000,
  headers: {
    'Connection': 'keep-alive',
  },
});
```

## 2. Response Caching

```typescript
// src/lib/apollo/cache.ts
import { LRUCache } from 'lru-cache';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

class ApolloCache {
  private cache: LRUCache<string, CacheEntry<any>>;

  constructor() {
    this.cache = new LRUCache({
      max: 1000, // Max entries
      ttl: 5 * 60 * 1000, // 5 minutes default
      updateAgeOnGet: true,
    });
  }

  generateKey(operation: string, params: any): string {
    return `${operation}:${JSON.stringify(params)}`;
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key) as CacheEntry<T> | undefined;
    return entry?.data || null;
  }

  set<T>(key: string, data: T, ttlMs?: number): void {
    this.cache.set(key, { data, timestamp: Date.now() }, { ttl: ttlMs });
  }

  invalidate(pattern: string): void {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }

  getStats() {
    return {
      size: this.cache.size,
      hitRate: this.cache.calculatedSize,
    };
  }
}

export const apolloCache = new ApolloCache();

// Cached wrapper
export async function cachedRequest<T>(
  key: string,
  fetchFn: () => Promise<T>,
  ttlMs: number = 300000 // 5 min default
): Promise<T> {
  const cached = apolloCache.get<T>(key);
  if (cached) {
    return cached;
  }

  const result = await fetchFn();
  apolloCache.set(key, result, ttlMs);
  return result;
}
```

### Cache Strategy by Endpoint

```typescript
// src/lib/apollo/cached-client.ts
const CACHE_CONFIG = {
  // Long cache - data rarely changes
  'organizations/enrich': 24 * 60 * 60 * 1000, // 24 hours
  'organizations/search': 60 * 60 * 1000, // 1 hour

  // Medium cache - occasional updates
  'people/search': 15 * 60 * 1000, // 15 minutes
  'people/match': 30 * 60 * 1000, // 30 minutes

  // Short cache - frequently updated
  'emailer_campaigns': 5 * 60 * 1000, // 5 minutes

  // No cache - real-time data
  'auth/health': 0,
};

export async function apolloRequest<T>(
  endpoint: string,
  params: any,
  method: 'GET' | 'POST' = 'POST'
): Promise<T> {
  const ttl = CACHE_CONFIG[endpoint] || 0;

  if (ttl === 0) {
    return apollo.request({ method, url: `/${endpoint}`, data: params });
  }

  const cacheKey = apolloCache.generateKey(endpoint, params);
  return cachedRequest(
    cacheKey,
    () => apollo.request({ method, url: `/${endpoint}`, data: params }),
    ttl
  );
}
```

## 3. Request Optimization

### Minimize Payload Size
```typescript
// Request only needed fields
const optimizedSearch = await apollo.searchPeople({
  q_organization_domains: ['stripe.com'],
  per_page: 25,
  // Only request fields you need
  person_seniorities: ['vp', 'director'], // Filter upfront
});

// Transform response immediately to reduce memory
const contacts = response.people.map(p => ({
  id: p.id,
  name: p.name,
  email: p.email,
  title: p.title,
  // Don't store unused fields
}));
```

### Parallel Requests with Concurrency Limit
```typescript
// src/lib/apollo/parallel.ts
import pLimit from 'p-limit';

const limit = pLimit(5); // Max 5 concurrent requests

export async function parallelEnrich(domains: string[]): Promise<Organization[]> {
  const results = await Promise.all(
    domains.map(domain =>
      limit(() => apolloRequest('organizations/enrich', { domain }))
    )
  );

  return results.filter(Boolean);
}
```

### Batch Processing
```typescript
// src/lib/apollo/batch.ts
export async function batchSearch(
  criteria: SearchCriteria[],
  batchSize: number = 10
): Promise<Person[]> {
  const results: Person[] = [];

  for (let i = 0; i < criteria.length; i += batchSize) {
    const batch = criteria.slice(i, i + batchSize);

    // Process batch in parallel
    const batchResults = await Promise.all(
      batch.map(c => apollo.searchPeople(c))
    );

    results.push(...batchResults.flatMap(r => r.people));

    // Rate limit between batches
    if (i + batchSize < criteria.length) {
      await new Promise(r => setTimeout(r, 100));
    }
  }

  return results;
}
```

## 4. Query Optimization

### Use Specific Filters
```typescript
// BAD: Broad search, then filter client-side
const allPeople = await apollo.searchPeople({
  q_organization_domains: ['stripe.com'],
  per_page: 100,
});
const engineers = allPeople.people.filter(p =>
  p.title?.toLowerCase().includes('engineer')
);

// GOOD: Filter at API level
const engineers = await apollo.searchPeople({
  q_organization_domains: ['stripe.com'],
  person_titles: ['engineer', 'developer', 'software'],
  per_page: 100,
});
```

### Pagination Strategy
```typescript
// src/lib/apollo/pagination.ts
export async function efficientPagination(
  searchParams: any,
  maxResults: number = 1000
): Promise<Person[]> {
  const results: Person[] = [];
  let page = 1;
  const perPage = 100; // Max allowed

  while (results.length < maxResults) {
    const response = await apollo.searchPeople({
      ...searchParams,
      page,
      per_page: perPage,
    });

    results.push(...response.people);

    // Stop if no more results
    if (response.people.length < perPage) {
      break;
    }

    // Stop if we've reached total
    if (page * perPage >= response.pagination.total_entries) {
      break;
    }

    page++;

    // Small delay to avoid rate limits
    await new Promise(r => setTimeout(r, 50));
  }

  return results.slice(0, maxResults);
}
```

## 5. Performance Monitoring

```typescript
// src/lib/apollo/metrics.ts
import { Histogram, Counter } from 'prom-client';

const requestDuration = new Histogram({
  name: 'apollo_request_duration_seconds',
  help: 'Duration of Apollo API requests',
  labelNames: ['endpoint', 'status'],
  buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10],
});

const requestCounter = new Counter({
  name: 'apollo_requests_total',
  help: 'Total Apollo API requests',
  labelNames: ['endpoint', 'status'],
});

const cacheHitCounter = new Counter({
  name: 'apollo_cache_hits_total',
  help: 'Apollo cache hits',
  labelNames: ['endpoint'],
});

export function instrumentedRequest<T>(
  endpoint: string,
  requestFn: () => Promise<T>
): Promise<T> {
  const end = requestDuration.startTimer({ endpoint });

  return requestFn()
    .then(result => {
      end({ status: 'success' });
      requestCounter.inc({ endpoint, status: 'success' });
      return result;
    })
    .catch(error => {
      end({ status: 'error' });
      requestCounter.inc({ endpoint, status: 'error' });
      throw error;
    });
}
```

### Performance Dashboard Query
```typescript
// Example Grafana queries
const grafanaQueries = {
  avgLatency: 'histogram_quantile(0.95, rate(apollo_request_duration_seconds_bucket[5m]))',
  requestRate: 'rate(apollo_requests_total[5m])',
  errorRate: 'rate(apollo_requests_total{status="error"}[5m]) / rate(apollo_requests_total[5m])',
  cacheHitRate: 'rate(apollo_cache_hits_total[5m]) / rate(apollo_requests_total[5m])',
};
```

## Performance Checklist

- [ ] Connection pooling enabled (keep-alive)
- [ ] Response caching implemented
- [ ] Cache TTLs tuned per endpoint
- [ ] Parallel requests with concurrency limit
- [ ] Minimal data requested (no unused fields)
- [ ] Server-side filtering vs client-side
- [ ] Efficient pagination strategy
- [ ] Metrics and monitoring enabled
- [ ] Performance baseline established

## Output
- Connection pooling configuration
- LRU cache with TTL per endpoint
- Parallel request patterns
- Query optimization techniques
- Performance monitoring setup

## Error Handling
| Issue | Resolution |
|-------|------------|
| High latency | Check network, enable caching |
| Cache misses | Tune TTL, check key generation |
| Rate limits | Reduce concurrency, add delays |
| Memory issues | Limit cache size, stream results |

## Resources
- [Node.js HTTP Agent](https://nodejs.org/api/http.html#class-httpagent)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [Prometheus Metrics](https://prometheus.io/docs/concepts/metric_types/)

## Next Steps
Proceed to `apollo-cost-tuning` for cost optimization.
