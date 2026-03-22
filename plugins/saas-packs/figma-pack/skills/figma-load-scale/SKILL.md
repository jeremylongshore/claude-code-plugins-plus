---
name: figma-load-scale
description: |
  Load test Figma API integrations and plan for scale.
  Use when benchmarking API throughput, testing rate limit behavior,
  or planning capacity for high-volume Figma integrations.
  Trigger with phrases like "figma load test", "figma scale",
  "figma benchmark", "figma capacity", "figma throughput".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Load & Scale

## Overview
Test and plan for the throughput limits of your Figma API integration. Figma's rate limits use a leaky bucket algorithm -- this skill helps you find the bucket size for your plan tier and design your integration to stay within it.

## Prerequisites
- k6 load testing tool (`brew install k6` or `apt install k6`)
- Figma test PAT (do not load test with production token)
- A test Figma file (not your production design system)

## Instructions

### Step 1: k6 Load Test Script
```javascript
// figma-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const figmaErrors = new Rate('figma_errors');
const figmaLatency = new Trend('figma_latency', true);

export const options = {
  scenarios: {
    // Test 1: Find your rate limit ceiling
    rate_limit_probe: {
      executor: 'constant-arrival-rate',
      rate: 10,           // 10 requests per second
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 5,
      maxVUs: 20,
    },
  },
  thresholds: {
    figma_errors: ['rate<0.10'],        // Less than 10% errors
    figma_latency: ['p(95)<3000'],      // P95 under 3 seconds
    http_req_duration: ['p(99)<5000'],  // P99 under 5 seconds
  },
};

const PAT = __ENV.FIGMA_PAT;
const FILE_KEY = __ENV.FIGMA_FILE_KEY;

export default function () {
  // Use a lightweight endpoint for rate limit testing
  const res = http.get(
    `https://api.figma.com/v1/files/${FILE_KEY}?depth=1`,
    {
      headers: { 'X-Figma-Token': PAT },
      tags: { endpoint: 'files' },
    }
  );

  figmaLatency.add(res.timings.duration);

  const isError = res.status !== 200;
  figmaErrors.add(isError);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'not rate limited': (r) => r.status !== 429,
    'latency < 2s': (r) => r.timings.duration < 2000,
  });

  if (res.status === 429) {
    const retryAfter = parseInt(res.headers['Retry-After'] || '60');
    console.log(`Rate limited. Retry-After: ${retryAfter}s`);
    sleep(retryAfter);
  } else {
    sleep(0.1); // 100ms between requests
  }
}
```

### Step 2: Run Load Tests
```bash
# Probe rate limits
k6 run \
  --env FIGMA_PAT="${FIGMA_PAT}" \
  --env FIGMA_FILE_KEY="${FIGMA_FILE_KEY}" \
  figma-load-test.js

# Export results to JSON for analysis
k6 run \
  --env FIGMA_PAT="${FIGMA_PAT}" \
  --env FIGMA_FILE_KEY="${FIGMA_FILE_KEY}" \
  --out json=results.json \
  figma-load-test.js
```

### Step 3: Capacity Planning
```typescript
interface FigmaCapacityPlan {
  planTier: string;
  measuredLimitPerMinute: number;
  currentUsagePerMinute: number;
  headroomPercent: number;
  recommendation: string;
}

function planCapacity(
  measuredLimit: number,
  currentUsage: number,
  planTier: string
): FigmaCapacityPlan {
  const headroom = ((measuredLimit - currentUsage) / measuredLimit) * 100;

  let recommendation: string;
  if (headroom > 50) {
    recommendation = 'Adequate capacity. Monitor monthly.';
  } else if (headroom > 20) {
    recommendation = 'Approaching limits. Implement caching and batching.';
  } else {
    recommendation = 'Near capacity. Upgrade plan or reduce request volume.';
  }

  return {
    planTier,
    measuredLimitPerMinute: measuredLimit,
    currentUsagePerMinute: currentUsage,
    headroomPercent: Math.round(headroom),
    recommendation,
  };
}
```

### Step 4: Scaling Strategies
```typescript
// Strategy 1: Request coalescing
// Multiple callers requesting the same file get a single API call
class RequestCoalescer {
  private pending = new Map<string, Promise<any>>();

  async get(key: string, fetcher: () => Promise<any>): Promise<any> {
    if (this.pending.has(key)) {
      return this.pending.get(key)!;
    }

    const promise = fetcher().finally(() => this.pending.delete(key));
    this.pending.set(key, promise);
    return promise;
  }
}

const coalescer = new RequestCoalescer();

// 10 simultaneous requests for the same file = 1 API call
const results = await Promise.all(
  Array(10).fill(null).map(() =>
    coalescer.get(fileKey, () => figmaClient.getFile(fileKey))
  )
);

// Strategy 2: Stagger requests across time
import PQueue from 'p-queue';

const figmaQueue = new PQueue({
  concurrency: 3,
  interval: 1000,
  intervalCap: 5, // Max 5 requests per second
});

// Strategy 3: Pre-fetch during off-peak hours
// Run design token sync at 3 AM, cache results for the day
```

### Step 5: Benchmark Report Template
```markdown
## Figma API Benchmark Report
**Date:** YYYY-MM-DD
**Plan:** [Starter/Pro/Org/Enterprise]
**Seat:** [Full/Collab/Viewer]

### Rate Limit Findings
| Endpoint | Measured Limit/min | First 429 At | Retry-After |
|----------|-------------------|--------------|-------------|
| GET /v1/files/:key?depth=1 | ~30 | Request #31 | 60s |
| GET /v1/files/:key/nodes | ~30 | Request #32 | 60s |
| GET /v1/images/:key | ~20 | Request #21 | 60s |

### Latency
| Endpoint | P50 | P95 | P99 |
|----------|-----|-----|-----|
| /v1/files (depth=1) | 200ms | 500ms | 1200ms |
| /v1/files (full) | 800ms | 2000ms | 4000ms |
| /v1/images | 300ms | 800ms | 1500ms |

### Recommendations
- Cache file metadata (changes infrequently)
- Use webhooks instead of polling
- Batch node IDs in single requests
- Use `depth=1` unless full tree is needed
```

## Output
- k6 load test measuring actual rate limits
- Capacity plan with headroom analysis
- Scaling strategies implemented
- Benchmark report documented

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| All requests 429'd | Rate too aggressive | Start lower, ramp gradually |
| Inconsistent limits | Shared rate limit bucket | Other services using same token |
| k6 connection errors | Too many parallel VUs | Reduce `preAllocatedVUs` |
| Results vary between runs | Leaky bucket state | Wait 5min between test runs |

## Resources
- [k6 Documentation](https://grafana.com/docs/k6/)
- [Figma Rate Limits](https://developers.figma.com/docs/rest-api/rate-limits/)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For reliability patterns, see `figma-reliability-patterns`.
