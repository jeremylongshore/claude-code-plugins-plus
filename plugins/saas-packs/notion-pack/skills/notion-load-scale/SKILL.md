---
name: notion-load-scale
description: |
  Implement Notion load testing, throughput optimization, and scaling strategies.
  Use when testing integration performance at scale, optimizing for Notion's
  rate limits, or planning capacity for high-volume Notion operations.
  Trigger with phrases like "notion load test", "notion scale",
  "notion performance test", "notion capacity", "notion benchmark".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Load & Scale

## Overview
Load testing and scaling strategies for Notion integrations, working within the 3 requests/second rate limit. Includes throughput benchmarks, k6 load scripts, and scaling patterns.

## Prerequisites
- `@notionhq/client` installed
- k6 load testing tool (optional)
- Test database in Notion (dedicated for load tests)

## Instructions

### Step 1: Understand Notion's Throughput Limits
```
Rate limit: 3 requests/second average (per integration token)
Burst: Some bursts allowed above average
Page size: Max 100 results per query
Block append: Max 100 blocks per request
No bulk create: Pages must be created one at a time

Theoretical maximums per hour:
  - Reads (query/retrieve): ~10,800 (3/s × 3,600s)
  - Pages queried: ~1,080,000 (10,800 × 100 per page)
  - Pages created: ~10,800 (one at a time, 3/s)
  - Blocks appended: ~1,080,000 (10,800 × 100 per batch)
```

### Step 2: Throughput Benchmark
```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function benchmarkThroughput(dbId: string, durationMs = 30_000) {
  const results = {
    queries: 0,
    pagesRead: 0,
    errors: 0,
    rateLimits: 0,
    startTime: Date.now(),
    latencies: [] as number[],
  };

  const endTime = Date.now() + durationMs;

  while (Date.now() < endTime) {
    const start = performance.now();
    try {
      const response = await notion.databases.query({
        database_id: dbId,
        page_size: 100,
      });
      results.queries++;
      results.pagesRead += response.results.length;
      results.latencies.push(performance.now() - start);
    } catch (error: any) {
      results.errors++;
      if (error.code === 'rate_limited') {
        results.rateLimits++;
        // Wait for rate limit to clear
        const retryAfter = parseInt(error.headers?.['retry-after'] ?? '1');
        await new Promise(r => setTimeout(r, retryAfter * 1000));
      }
    }
  }

  const durationSec = (Date.now() - results.startTime) / 1000;
  const sorted = results.latencies.sort((a, b) => a - b);

  console.log('=== Notion Throughput Benchmark ===');
  console.log(`Duration: ${durationSec.toFixed(1)}s`);
  console.log(`Queries: ${results.queries} (${(results.queries / durationSec).toFixed(1)}/s)`);
  console.log(`Pages read: ${results.pagesRead}`);
  console.log(`Errors: ${results.errors} (${results.rateLimits} rate limits)`);
  console.log(`Latency P50: ${Math.round(sorted[Math.floor(sorted.length * 0.5)])}ms`);
  console.log(`Latency P95: ${Math.round(sorted[Math.floor(sorted.length * 0.95)])}ms`);
  console.log(`Latency P99: ${Math.round(sorted[Math.floor(sorted.length * 0.99)])}ms`);

  return results;
}
```

### Step 3: k6 Load Test Script
```javascript
// notion-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('notion_errors');
const queryLatency = new Trend('notion_query_latency');

export const options = {
  scenarios: {
    steady_rate: {
      executor: 'constant-arrival-rate',
      rate: 3,              // 3 requests per second (Notion limit)
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 5,
      maxVUs: 10,
    },
  },
  thresholds: {
    notion_errors: ['rate<0.05'],          // < 5% error rate
    notion_query_latency: ['p(95)<2000'],  // P95 < 2s
  },
};

const DB_ID = __ENV.NOTION_TEST_DB_ID;
const TOKEN = __ENV.NOTION_TOKEN;

export default function () {
  const res = http.post(
    `https://api.notion.com/v1/databases/${DB_ID}/query`,
    JSON.stringify({ page_size: 10 }),
    {
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
      },
      timeout: '30s',
    }
  );

  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'has results': (r) => JSON.parse(r.body).results !== undefined,
  });

  errorRate.add(!success);
  queryLatency.add(res.timings.duration);

  if (res.status === 429) {
    const retryAfter = parseInt(res.headers['Retry-After'] || '1');
    sleep(retryAfter);
  }
}
```

```bash
# Run k6 test
k6 run \
  --env NOTION_TOKEN=${NOTION_TOKEN} \
  --env NOTION_TEST_DB_ID=${NOTION_TEST_DB_ID} \
  notion-load-test.js
```

### Step 4: Scaling Patterns

**Pattern A: Multiple Integration Tokens**
```typescript
// Each integration token gets its own 3 req/s limit
// Use separate integrations for independent workloads

const readers = [
  new Client({ auth: process.env.NOTION_TOKEN_READ_1 }),
  new Client({ auth: process.env.NOTION_TOKEN_READ_2 }),
];

// Round-robin across clients
let clientIndex = 0;
function getNextClient(): Client {
  const client = readers[clientIndex % readers.length];
  clientIndex++;
  return client;
}

// 6 req/s total with 2 tokens
```

**Pattern B: Read-Through Cache**
```typescript
import { LRUCache } from 'lru-cache';

const pageCache = new LRUCache<string, any>({ max: 1000, ttl: 300_000 }); // 5 min TTL

async function getPage(pageId: string): Promise<any> {
  const cached = pageCache.get(pageId);
  if (cached) return cached; // Zero API cost for cache hits

  const page = await notion.pages.retrieve({ page_id: pageId });
  pageCache.set(pageId, page);
  return page;
}

// For high-read workloads, cache hit rates of 80%+ reduce effective
// API usage from 3 req/s to < 1 req/s of actual API calls
```

**Pattern C: Queue-Based Write Batching**
```typescript
import PQueue from 'p-queue';

const writeQueue = new PQueue({
  concurrency: 1,         // Serialize writes
  interval: 350,          // ~3/second
  intervalCap: 1,
});

// Enqueue writes — they execute at controlled rate
async function schedulePageCreate(dbId: string, properties: any) {
  return writeQueue.add(() =>
    notion.pages.create({ parent: { database_id: dbId }, properties })
  );
}

// Monitor queue depth
setInterval(() => {
  if (writeQueue.size > 100) {
    console.warn(`Write queue depth: ${writeQueue.size} — consider increasing rate`);
  }
}, 5000);
```

### Step 5: Capacity Planning
```typescript
function planCapacity(requirements: {
  readsPerMinute: number;
  writesPerMinute: number;
  cacheHitRate: number; // 0-1
}) {
  const effectiveReads = requirements.readsPerMinute * (1 - requirements.cacheHitRate);
  const totalReqPerMinute = effectiveReads + requirements.writesPerMinute;
  const reqPerSecond = totalReqPerMinute / 60;
  const tokensNeeded = Math.ceil(reqPerSecond / 3);

  console.log('Capacity Plan:');
  console.log(`  Raw reads/min: ${requirements.readsPerMinute}`);
  console.log(`  Cache hit rate: ${(requirements.cacheHitRate * 100).toFixed(0)}%`);
  console.log(`  Effective reads/min: ${Math.round(effectiveReads)}`);
  console.log(`  Writes/min: ${requirements.writesPerMinute}`);
  console.log(`  Total req/s: ${reqPerSecond.toFixed(1)}`);
  console.log(`  Integration tokens needed: ${tokensNeeded}`);
  console.log(`  Headroom: ${((tokensNeeded * 3 - reqPerSecond) / (tokensNeeded * 3) * 100).toFixed(0)}%`);
}

// Example
planCapacity({ readsPerMinute: 500, writesPerMinute: 50, cacheHitRate: 0.8 });
```

## Output
- Throughput benchmark results with latency percentiles
- k6 load test for sustained rate testing
- Scaling patterns for exceeding single-token limits
- Capacity planning tool

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Sustained 429s | Exceeding 3 req/s | Add PQueue throttling |
| k6 all errors | Wrong token or DB ID | Verify env vars |
| Latency spikes | Notion server load | Expected variance, use P95 not max |
| Queue growing | Write rate > 3/s | Add more integration tokens |

## Examples

### Quick Benchmark
```bash
# Time 10 sequential API calls
time for i in $(seq 1 10); do
  curl -s -o /dev/null -w "%{time_total}s\n" \
    https://api.notion.com/v1/users/me \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28"
done
```

## Resources
- [Notion Request Limits](https://developers.notion.com/reference/request-limits)
- [k6 Documentation](https://k6.io/docs/)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For reliability patterns, see `notion-reliability-patterns`.
