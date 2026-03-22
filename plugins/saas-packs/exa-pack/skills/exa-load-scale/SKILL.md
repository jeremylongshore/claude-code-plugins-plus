---
name: exa-load-scale
description: |
  Implement Exa load testing, capacity planning, and scaling strategies.
  Use when running performance tests, planning capacity for Exa integrations,
  or designing high-throughput search architectures.
  Trigger with phrases like "exa load test", "exa scale",
  "exa capacity", "exa k6", "exa benchmark", "exa throughput".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, testing, performance, scaling]

---
# Exa Load & Scale

## Overview
Load testing and capacity planning for Exa integrations. Key constraint: Exa's default rate limit is 10 QPS. Scaling strategies focus on caching, request queuing, parallel processing within rate limits, and search type selection for latency budgets.

## Prerequisites
- k6 load testing tool installed
- Test environment Exa API key (separate from production)
- Redis for result caching

## Capacity Reference

| Search Type | Typical Latency | Max Throughput (10 QPS) |
|-------------|----------------|-------------------------|
| `instant` | < 150ms | 10 req/s (600/min) |
| `fast` | < 425ms | 10 req/s (600/min) |
| `auto` | 300-1500ms | 10 req/s (600/min) |
| `neural` | 500-2000ms | 10 req/s (600/min) |
| `deep` | 2-5s | 10 req/s (600/min) |

**With caching (50% hit rate):** Effective throughput doubles to 20 req/s equivalent.

## Instructions

### Step 1: k6 Load Test Against Your Wrapper
```javascript
// exa-load-test.js
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "1m", target: 5 },    // Ramp up to 5 VUs
    { duration: "3m", target: 5 },    // Steady state
    { duration: "1m", target: 10 },   // Push toward rate limit
    { duration: "2m", target: 10 },   // Stress test
    { duration: "1m", target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<3000"],  // 3s P95 for neural search
    http_req_failed: ["rate<0.05"],     // < 5% error rate
  },
};

const queries = [
  "best practices for building RAG systems",
  "transformer architecture improvements 2025",
  "TypeScript 5.5 new features",
  "vector database comparison guide",
  "AI safety alignment research",
];

export default function () {
  const query = queries[Math.floor(Math.random() * queries.length)];

  const response = http.post(
    `${__ENV.APP_URL}/api/search`,
    JSON.stringify({ query, numResults: 3 }),
    {
      headers: { "Content-Type": "application/json" },
      timeout: "10s",
    }
  );

  check(response, {
    "status 200": (r) => r.status === 200,
    "has results": (r) => JSON.parse(r.body).results?.length > 0,
    "latency < 3s": (r) => r.timings.duration < 3000,
  });

  sleep(0.5 + Math.random()); // 0.5-1.5s between requests
}
```

```bash
# Run load test
k6 run --env APP_URL=http://localhost:3000 exa-load-test.js
```

### Step 2: Throughput Maximizer with Request Queue
```typescript
import Exa from "exa-js";
import PQueue from "p-queue";

const exa = new Exa(process.env.EXA_API_KEY);

// Stay under 10 QPS rate limit
const searchQueue = new PQueue({
  concurrency: 8,        // max concurrent requests
  interval: 1000,        // per second
  intervalCap: 10,       // Exa's QPS limit
});

async function highThroughputSearch(queries: string[]) {
  const results = [];

  for (const query of queries) {
    const promise = searchQueue.add(async () => {
      const result = await exa.searchAndContents(query, {
        type: "auto",
        numResults: 3,
        text: { maxCharacters: 500 },
      });
      return { query, results: result.results };
    });
    results.push(promise);
  }

  return Promise.all(results);
}

// Process 100 queries respecting rate limits
const queries = Array.from({ length: 100 }, (_, i) => `research topic ${i}`);
console.time("batch");
const results = await highThroughputSearch(queries);
console.timeEnd("batch");
// Expected: ~10-12 seconds (100 queries / 10 QPS)
```

### Step 3: Caching for Scale
```typescript
import { LRUCache } from "lru-cache";

// Cache eliminates repeat queries entirely
const cache = new LRUCache<string, any>({
  max: 10000,
  ttl: 3600 * 1000, // 1-hour TTL
});

async function scalableSearch(query: string, opts: any) {
  const key = `${query.toLowerCase().trim()}:${opts.type}:${opts.numResults}`;
  const cached = cache.get(key);
  if (cached) return cached;

  const result = await searchQueue.add(() =>
    exa.searchAndContents(query, opts)
  );
  cache.set(key, result);
  return result;
}

// With 50% cache hit rate:
// 100 unique queries → 50 API calls → 5 seconds instead of 10
```

### Step 4: Capacity Planning Calculator
```typescript
interface CapacityEstimate {
  dailySearches: number;
  peakQPS: number;
  cacheHitRate: number;
  effectiveQPS: number;
  withinLimits: boolean;
  recommendation: string;
}

function estimateCapacity(
  dailySearches: number,
  peakMultiplier = 3,
  expectedCacheHitRate = 0.5
): CapacityEstimate {
  const avgQPS = dailySearches / (24 * 3600);
  const peakQPS = avgQPS * peakMultiplier;
  const effectiveQPS = peakQPS * (1 - expectedCacheHitRate);
  const withinLimits = effectiveQPS <= 10; // Default Exa limit

  let recommendation = "Within default limits";
  if (effectiveQPS > 10 && effectiveQPS <= 50) {
    recommendation = "Contact hello@exa.ai for Enterprise rate limits";
  } else if (effectiveQPS > 50) {
    recommendation = "Requires Enterprise plan + aggressive caching + request queue";
  }

  return { dailySearches, peakQPS, cacheHitRate: expectedCacheHitRate, effectiveQPS, withinLimits, recommendation };
}

// Example: 50,000 searches/day
const estimate = estimateCapacity(50000);
console.log(estimate);
// { effectiveQPS: ~0.87, withinLimits: true, recommendation: "Within default limits" }
```

## Benchmark Results Template
```markdown
## Exa Performance Benchmark
**Date:** YYYY-MM-DD | **SDK:** exa-js X.Y.Z

| Metric | Value |
|--------|-------|
| Total Requests | N |
| Success Rate | X% |
| Cache Hit Rate | X% |
| P50 Latency | Xms |
| P95 Latency | Xms |
| Peak QPS (actual API calls) | X |
| 429 Rate Limit Errors | N |
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 errors in load test | Exceeding 10 QPS | Reduce concurrency, add cache |
| Inconsistent latency | Different search types | Standardize on one type per test |
| Timeout errors | Deep search under load | Use `fast` or `auto` for load tests |
| Cache miss rate high | Unique queries per request | Use a fixed query pool |

## Resources
- [Exa Rate Limits](https://docs.exa.ai/reference/rate-limits)
- [k6 Documentation](https://k6.io/docs/)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For reliability patterns, see `exa-reliability-patterns`.
