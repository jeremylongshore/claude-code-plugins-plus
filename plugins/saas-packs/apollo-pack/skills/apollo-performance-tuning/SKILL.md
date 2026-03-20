---
name: apollo-performance-tuning
description: |
  Optimize Apollo.io API performance.
  Use when improving API response times, reducing latency,
  or optimizing bulk operations.
  Trigger with phrases like "apollo performance", "optimize apollo",
  "apollo slow", "apollo latency", "speed up apollo".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Performance Tuning

## Overview
Optimize Apollo.io API performance through response caching, connection pooling, request field selection, parallel fetching, and bulk operation strategies for the REST API (`https://api.apollo.io/v1`).

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Enable Connection Pooling
```typescript
// src/apollo/optimized-client.ts
import axios from 'axios';
import http from 'http';
import https from 'https';

// Reuse TCP connections instead of opening a new one per request
const httpAgent = new http.Agent({ keepAlive: true, maxSockets: 10 });
const httpsAgent = new https.Agent({ keepAlive: true, maxSockets: 10 });

export const optimizedClient = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  headers: { 'Content-Type': 'application/json' },
  params: { api_key: process.env.APOLLO_API_KEY },
  httpAgent,
  httpsAgent,
  timeout: 15_000,
});
```

### Step 2: Add LRU Cache with TTL
```typescript
// src/apollo/cache.ts
import { LRUCache } from 'lru-cache';

interface CacheEntry<T> {
  data: T;
  cachedAt: number;
}

// Different TTLs per endpoint type
const CACHE_TTLS: Record<string, number> = {
  '/organizations/enrich': 24 * 60 * 60 * 1000,  // 24h — company data changes rarely
  '/people/match': 4 * 60 * 60 * 1000,            // 4h — contact data changes occasionally
  '/people/search': 15 * 60 * 1000,                // 15min — search results are dynamic
};

const cache = new LRUCache<string, CacheEntry<any>>({
  max: 5000,
  maxSize: 50 * 1024 * 1024,  // 50MB max
  sizeCalculation: (value) => JSON.stringify(value).length,
});

function cacheKey(endpoint: string, params: any): string {
  return `${endpoint}:${JSON.stringify(params)}`;
}

export async function cachedRequest<T>(
  endpoint: string,
  requestFn: () => Promise<T>,
  params: any,
): Promise<T> {
  const key = cacheKey(endpoint, params);
  const ttl = CACHE_TTLS[endpoint] ?? 15 * 60 * 1000;

  const cached = cache.get(key);
  if (cached && Date.now() - cached.cachedAt < ttl) {
    return cached.data;
  }

  const data = await requestFn();
  cache.set(key, { data, cachedAt: Date.now() });
  return data;
}

export function getCacheStats() {
  return {
    size: cache.size,
    calculatedSize: cache.calculatedSize,
    hitRate: `Inspect cache.get calls for hit/miss ratio`,
  };
}
```

### Step 3: Implement Parallel Fetching with Concurrency Control
```typescript
// src/apollo/parallel.ts
import PQueue from 'p-queue';

const queue = new PQueue({ concurrency: 5 });

export async function parallelEnrich(
  domains: string[],
): Promise<Map<string, any>> {
  const results = new Map<string, any>();

  await queue.addAll(
    domains.map((domain) => async () => {
      const data = await cachedRequest(
        '/organizations/enrich',
        () => optimizedClient.get('/organizations/enrich', { params: { domain } }).then((r) => r.data),
        { domain },
      );
      results.set(domain, data.organization);
    }),
  );

  return results;
}

// Enrich 100 domains at 5 concurrent, with caching
// const orgs = await parallelEnrich(domainList);
```

### Step 4: Minimize Response Payload
```typescript
// Apollo API does not support field selection directly,
// so minimize payload on the client side by extracting only needed fields.

interface SlimPerson {
  id: string;
  name: string;
  title: string;
  email: string;
  company: string;
}

function slimPersonResult(raw: any): SlimPerson {
  return {
    id: raw.id,
    name: raw.name,
    title: raw.title,
    email: raw.email,
    company: raw.organization?.name ?? '',
  };
}

async function searchSlim(domain: string): Promise<SlimPerson[]> {
  const { data } = await optimizedClient.post('/people/search', {
    q_organization_domains: [domain],
    per_page: 100,
  });
  return data.people.map(slimPersonResult);
}
```

### Step 5: Benchmark and Monitor Performance
```typescript
// src/scripts/benchmark.ts
async function benchmark() {
  const endpoints = [
    { name: 'People Search', fn: () => optimizedClient.post('/people/search', { q_organization_domains: ['apollo.io'], per_page: 1 }) },
    { name: 'Org Enrich', fn: () => optimizedClient.get('/organizations/enrich', { params: { domain: 'apollo.io' } }) },
    { name: 'People Match', fn: () => optimizedClient.post('/people/match', { email: 'test@apollo.io' }) },
  ];

  for (const ep of endpoints) {
    const times: number[] = [];
    for (let i = 0; i < 5; i++) {
      const start = Date.now();
      try { await ep.fn(); } catch { /* ignore errors for benchmarking */ }
      times.push(Date.now() - start);
    }

    const avg = Math.round(times.reduce((a, b) => a + b, 0) / times.length);
    const p95 = times.sort((a, b) => a - b)[Math.floor(times.length * 0.95)];
    console.log(`${ep.name}: avg=${avg}ms, p95=${p95}ms`);
  }
}
```

## Output
- Connection pooling with `keepAlive` and configurable `maxSockets`
- LRU cache with per-endpoint TTLs (24h for orgs, 4h for contacts, 15m for search)
- Parallel enrichment queue with `p-queue` concurrency control
- Response payload slimming functions for memory efficiency
- Benchmarking script measuring avg and p95 latency per endpoint

## Error Handling
| Issue | Resolution |
|-------|------------|
| High latency | Enable connection pooling, check DNS resolution time |
| Cache misses | Increase TTL for stable data, check cache key generation |
| Rate limits | Reduce p-queue concurrency, add `intervalCap` |
| Memory issues | Lower LRU cache `max` and `maxSize`, stream large results |

## Examples

### Before/After Comparison
```typescript
// Without optimization: sequential, no caching
// 100 org enrichments = 100 requests * ~500ms = 50 seconds

// With optimization: parallel (5x), cached (24h TTL)
// 100 org enrichments = 20 batches * ~500ms = 10 seconds (first run)
// Subsequent runs: cache hits = ~1ms each
const results = await parallelEnrich(hundredDomains);
console.log(`Enriched ${results.size} orgs with caching`);
```

## Resources
- [Node.js HTTP Agent (Connection Pooling)](https://nodejs.org/api/http.html#class-httpagent)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [p-queue Concurrency Control](https://github.com/sindresorhus/p-queue)

## Next Steps
Proceed to `apollo-cost-tuning` for cost optimization.
