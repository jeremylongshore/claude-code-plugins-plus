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
tags: [saas, apollo, api, performance]

---
# Apollo Performance Tuning

## Overview
Optimize Apollo.io API performance through response caching, connection pooling, bulk operations, parallel fetching, and result slimming. Key insight: **search is free but slow (~500ms), enrichment costs credits** — cache aggressively and batch enrichment calls.

## Prerequisites
- Valid Apollo API key
- Node.js 18+

## Instructions

### Step 1: Connection Pooling
Reuse TCP connections to avoid TLS handshake overhead on every request.

```typescript
// src/apollo/optimized-client.ts
import axios from 'axios';
import https from 'https';

const httpsAgent = new https.Agent({
  keepAlive: true,
  maxSockets: 10,
  maxFreeSockets: 5,
  timeout: 30_000,
});

export const optimizedClient = axios.create({
  baseURL: 'https://api.apollo.io/api/v1',
  headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! },
  httpsAgent,
  timeout: 15_000,
});
```

### Step 2: Response Caching with Per-Endpoint TTLs
```typescript
// src/apollo/cache.ts
import { LRUCache } from 'lru-cache';

// Different TTLs based on data volatility
const CACHE_TTLS: Record<string, number> = {
  '/organizations/enrich': 24 * 60 * 60 * 1000,    // 24h — company data rarely changes
  '/people/match': 4 * 60 * 60 * 1000,              // 4h — contact data changes occasionally
  '/mixed_people/api_search': 15 * 60 * 1000,       // 15min — search results are dynamic
  '/mixed_companies/search': 30 * 60 * 1000,         // 30min — company search
  '/contact_stages': 60 * 60 * 1000,                 // 1h — stages rarely change
};

const cache = new LRUCache<string, { data: any; at: number }>({
  max: 5000,
  maxSize: 50 * 1024 * 1024,
  sizeCalculation: (v) => JSON.stringify(v).length,
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

  if (cached && Date.now() - cached.at < ttl) return cached.data;

  const data = await requestFn();
  cache.set(key, { data, at: Date.now() });
  return data;
}

export function getCacheStats() {
  return { entries: cache.size, sizeBytes: cache.calculatedSize };
}
```

### Step 3: Use Bulk Endpoints Over Single Calls
Apollo's bulk enrichment endpoint handles 10 records per call vs 1. Massive performance gain.

```typescript
// src/apollo/bulk-ops.ts
import { optimizedClient } from './optimized-client';
import PQueue from 'p-queue';

const queue = new PQueue({ concurrency: 3, intervalCap: 2, interval: 1000 });

// Enrich 100 people: 100 individual calls = 100 requests @ 500ms = 50s
// Batch of 10: 10 bulk calls @ 600ms = 6s (8x faster, same credits)
export async function batchEnrich(
  details: Array<{ email?: string; linkedin_url?: string; first_name?: string; last_name?: string; organization_domain?: string }>,
): Promise<any[]> {
  const results: any[] = [];

  for (let i = 0; i < details.length; i += 10) {
    const batch = details.slice(i, i + 10);
    const result = await queue.add(async () => {
      const { data } = await optimizedClient.post('/people/bulk_match', {
        details: batch,
        reveal_personal_emails: false,
        reveal_phone_number: false,
      });
      return data.matches ?? [];
    });
    results.push(...(result ?? []));
  }

  return results;
}
```

### Step 4: Parallel Search with Concurrency Control
```typescript
export async function parallelSearch(
  domains: string[],
  concurrency: number = 5,
): Promise<Map<string, any[]>> {
  const searchQueue = new PQueue({ concurrency });
  const results = new Map<string, any[]>();

  await searchQueue.addAll(
    domains.map((domain) => async () => {
      const data = await cachedRequest(
        '/mixed_people/api_search',
        () => optimizedClient.post('/mixed_people/api_search', {
          q_organization_domains_list: [domain],
          person_seniorities: ['vp', 'director', 'c_suite'],
          per_page: 25,
        }).then((r) => r.data),
        { domain },
      );
      results.set(domain, data.people ?? []);
    }),
  );

  return results;
}
```

### Step 5: Slim Response Payloads
Apollo returns large person objects (~2KB each). Extract only needed fields to reduce memory.

```typescript
interface SlimPerson {
  id: string;
  name: string;
  title: string;
  email?: string;
  company: string;
  seniority: string;
}

function slimPerson(raw: any): SlimPerson {
  return {
    id: raw.id,
    name: raw.name,
    title: raw.title,
    email: raw.email,
    company: raw.organization?.name ?? '',
    seniority: raw.seniority ?? '',
  };
}

// Use immediately after API call to free memory
const { data } = await optimizedClient.post('/mixed_people/api_search', { ... });
const slim = data.people.map(slimPerson);  // ~200 bytes each instead of ~2KB
```

### Step 6: Benchmark Your Endpoints
```typescript
async function benchmark() {
  const endpoints = [
    { name: 'People Search', fn: () => optimizedClient.post('/mixed_people/api_search',
        { q_organization_domains_list: ['apollo.io'], per_page: 1 }) },
    { name: 'Org Enrich', fn: () => optimizedClient.get('/organizations/enrich',
        { params: { domain: 'apollo.io' } }) },
    { name: 'Auth Health', fn: () => optimizedClient.get('/auth/health') },
  ];

  for (const ep of endpoints) {
    const times: number[] = [];
    for (let i = 0; i < 5; i++) {
      const start = Date.now();
      try { await ep.fn(); } catch {}
      times.push(Date.now() - start);
    }
    const avg = Math.round(times.reduce((a, b) => a + b) / times.length);
    const p95 = times.sort((a, b) => a - b)[Math.floor(times.length * 0.95)];
    console.log(`${ep.name}: avg=${avg}ms, p95=${p95}ms`);
  }
}
```

## Output
- Connection pooling with `keepAlive` and configurable `maxSockets`
- LRU cache with per-endpoint TTLs (24h org, 4h contact, 15m search)
- Bulk enrichment via `/people/bulk_match` (10x fewer requests)
- Parallel search with `p-queue` concurrency control
- Response slimming reducing memory from ~2KB to ~200B per person
- Benchmarking script measuring avg and p95 latency

## Error Handling
| Issue | Resolution |
|-------|------------|
| High latency | Enable connection pooling, check for stale cache |
| Cache misses | Increase TTL for stable data (org enrichment) |
| Rate limits with parallelism | Reduce p-queue concurrency |
| Memory growth | Lower LRU max entries, slim response payloads |

## Resources
- [Bulk People Enrichment](https://docs.apollo.io/reference/bulk-people-enrichment)
- [Node.js HTTPS Agent](https://nodejs.org/api/https.html#class-httpsagent)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
Proceed to `apollo-cost-tuning` for cost optimization.
