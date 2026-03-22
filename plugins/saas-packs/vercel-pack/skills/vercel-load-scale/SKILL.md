---
name: vercel-load-scale
description: |
  Load test and scale Vercel deployments with concurrency tuning and capacity planning.
  Use when running performance tests, planning for traffic spikes,
  or optimizing serverless function scaling on Vercel.
  Trigger with phrases like "vercel load test", "vercel scale",
  "vercel performance test", "vercel capacity", "vercel benchmark".
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(vercel:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, testing, performance, scaling]

---
# Vercel Load & Scale

## Overview
Load test Vercel deployments to identify scaling limits, cold start impact, and concurrency thresholds. Covers k6/autocannon test scripts, Vercel's auto-scaling model, Fluid Compute concurrency, and capacity planning.

## Prerequisites
- Load testing tool: k6, autocannon, or artillery
- Test environment deployment (never load test production without approval)
- Access to Vercel Analytics for monitoring during tests

## Instructions

### Step 1: Understand Vercel's Scaling Model
Vercel serverless functions scale automatically:

| Behavior | Details |
|----------|---------|
| Scale-up | New function instances spawn on demand |
| Scale-down | Idle instances shut down after ~15 minutes |
| Cold starts | First request to a new instance pays initialization cost |
| Concurrency | Each instance handles one request at a time (by default) |
| Fluid Compute | Pro/Enterprise: multiple requests per instance |

**Concurrency limits by plan:**

| Plan | Max Concurrent Functions |
|------|------------------------|
| Hobby | 10 |
| Pro | 1,000 |
| Enterprise | 100,000 |

### Step 2: Basic Load Test with autocannon
```bash
# Install autocannon
npm install -g autocannon

# Test with 50 concurrent connections for 30 seconds
autocannon -c 50 -d 30 https://my-app-preview.vercel.app/api/endpoint

# Output includes:
# Latency: avg, p50, p99, max
# Requests/sec: avg, min, max
# Errors: timeouts, non-2xx responses
```

### Step 3: k6 Load Test Script
```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const coldStartRate = new Rate('cold_starts');
const latency = new Trend('api_latency');

export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Warm up
    { duration: '3m', target: 50 },   // Ramp to 50 users
    { duration: '2m', target: 100 },  // Peak load
    { duration: '1m', target: 0 },    // Cool down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],  // P95 < 2s
    errors: ['rate<0.01'],              // Error rate < 1%
  },
};

export default function () {
  const res = http.get('https://my-app-preview.vercel.app/api/endpoint');

  check(res, {
    'status is 200': (r) => r.status === 200,
    'latency < 2s': (r) => r.timings.duration < 2000,
  });

  errorRate.add(res.status !== 200);
  latency.add(res.timings.duration);

  // Track cold starts if your API returns this header
  if (res.headers['X-Cold-Start'] === 'true') {
    coldStartRate.add(1);
  }

  sleep(1);
}
```

```bash
# Run the load test
k6 run load-test.js

# Run with output to JSON for analysis
k6 run --out json=results.json load-test.js
```

### Step 4: Cold Start Stress Test
```javascript
// cold-start-test.js — specifically test cold start behavior
import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  scenarios: {
    // Scenario 1: Sustained load (warm instances)
    sustained: {
      executor: 'constant-arrival-rate',
      rate: 10,
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 20,
    },
    // Scenario 2: Spike (forces new cold starts)
    spike: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      stages: [
        { target: 200, duration: '10s' },  // Sudden spike
        { target: 10, duration: '1m' },     // Return to normal
      ],
      preAllocatedVUs: 300,
      startTime: '2m',  // Start after sustained phase
    },
  },
};

export default function () {
  const res = http.get('https://my-app-preview.vercel.app/api/endpoint');
  // Log cold start timing for analysis
}
```

### Step 5: Fluid Compute Concurrency Tuning
```json
// vercel.json — configure concurrency for Fluid Compute (Pro/Enterprise)
{
  "functions": {
    "api/high-throughput.ts": {
      "memory": 1024,
      "maxDuration": 30,
      "concurrency": 10
    }
  }
}
```

With Fluid Compute concurrency, a single function instance handles multiple requests:
- Reduces cold starts (fewer instances needed)
- Reduces cost (shared memory across requests)
- Best for I/O-bound functions (waiting on DB/API calls)
- Not ideal for CPU-bound functions (computation blocks other requests)

### Step 6: Capacity Planning
```
Capacity Planning Formula:

  Required instances = Peak RPS * Avg Response Time (seconds)

  Example:
  - Peak: 500 requests/second
  - Avg response: 200ms (0.2s)
  - Required: 500 * 0.2 = 100 concurrent instances

  With Fluid Compute (concurrency=10):
  - Required: 500 * 0.2 / 10 = 10 concurrent instances

  Plan check:
  - Hobby (10 concurrent): NOT sufficient
  - Pro (1000 concurrent): Sufficient with headroom
```

## Load Test Results Template

```markdown
## Load Test Report — [Date]

### Configuration
- Target: https://my-app-preview.vercel.app/api/endpoint
- Tool: k6 v0.50
- Duration: 7 minutes (ramp up → peak → cool down)
- Peak concurrent users: 100

### Results
| Metric | Value |
|--------|-------|
| Total requests | 12,450 |
| Success rate | 99.8% |
| P50 latency | 45ms |
| P95 latency | 320ms |
| P99 latency | 1,200ms |
| Max latency | 3,400ms |
| Cold start % | 8% |
| Avg cold start duration | 650ms |
| Throttled (429) | 0 |

### Recommendations
1. Cold start: 650ms avg — consider Edge Functions for latency-critical paths
2. P99 spike: caused by cold starts — Fluid Compute concurrency would help
3. No throttling at 100 concurrent — Pro plan (1000 limit) is sufficient
```

## Output
- Load test scripts for sustained and spike traffic scenarios
- Cold start frequency and duration measured
- Concurrency limits tested and validated
- Capacity plan with scaling recommendations
- Benchmark results documented

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `FUNCTION_THROTTLED` (429) | Exceeded concurrent limit | Reduce test concurrency or upgrade plan |
| Vercel blocks load test | Not from approved IP | Contact Vercel support before load testing |
| High P99 but low P50 | Cold starts on spikes | Use Fluid Compute concurrency or Edge Functions |
| All requests timeout | Function region far from test origin | Set `regions` in vercel.json closer to test source |
| Inconsistent results | Shared infrastructure variability | Run multiple test rounds, use median results |

## Resources
- [Vercel Function Limits](https://vercel.com/docs/functions/limitations)
- [Concurrency Scaling](https://vercel.com/docs/functions/concurrency-scaling)
- [Fluid Compute](https://vercel.com/docs/functions/usage-and-pricing)
- [k6 Documentation](https://k6.io/docs/)
- [Vercel Load Testing Policy](https://vercel.com/kb/guide/what-s-vercel-s-policy-regarding-load-testing-deployments)

## Next Steps
For reliability patterns, see `vercel-reliability-patterns`.
