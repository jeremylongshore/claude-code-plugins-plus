---
name: perplexity-load-scale
description: |
  Load test Perplexity Sonar API integrations and plan capacity.
  Use when running performance tests, planning for traffic growth,
  or benchmarking Perplexity latency under load.
  Trigger with phrases like "perplexity load test", "perplexity scale",
  "perplexity performance test", "perplexity capacity", "perplexity benchmark".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, testing, performance, scaling]

---
# Perplexity Load & Scale

## Overview
Load testing and capacity planning for Perplexity Sonar API. Key constraint: Perplexity rate limits at 50 RPM (default tier), and every request performs a live web search with variable latency. Load testing must respect these limits to avoid burning through credits.

## Capacity Constraints

| Constraint | Default Limit | Impact |
|-----------|--------------|--------|
| RPM (requests per minute) | 50 | Hard ceiling on throughput |
| Context window | 127K tokens | Limits conversation history |
| `sonar` latency | 1-3s | Throughput: ~20-50 concurrent |
| `sonar-pro` latency | 3-8s | Throughput: ~6-16 concurrent |
| `search_domain_filter` | 20 domains max | Per-request limit |

## Prerequisites
- k6 load testing tool installed
- Separate Perplexity API key for load testing
- Budget approval (load tests cost money)

## Instructions

### Step 1: k6 Load Test Script
```javascript
// perplexity-load-test.js
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const errorRate = new Rate("perplexity_errors");
const citationCount = new Trend("perplexity_citations");

export const options = {
  stages: [
    { duration: "1m", target: 5 },    // Ramp to 5 VUs
    { duration: "3m", target: 5 },    // Steady at 5 VUs
    { duration: "1m", target: 15 },   // Ramp to 15 VUs
    { duration: "3m", target: 15 },   // Steady at 15 VUs
    { duration: "1m", target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<10000"],  // 10s P95 for sonar
    perplexity_errors: ["rate<0.05"],    // <5% error rate
  },
};

const queries = [
  "What is TypeScript?",
  "Latest Node.js features",
  "Python vs JavaScript for web development",
  "Current state of AI in healthcare",
  "Best practices for REST API design",
];

export default function () {
  const query = queries[Math.floor(Math.random() * queries.length)];

  const response = http.post(
    "https://api.perplexity.ai/chat/completions",
    JSON.stringify({
      model: "sonar",
      messages: [{ role: "user", content: query }],
      max_tokens: 200,
    }),
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${__ENV.PERPLEXITY_API_KEY}`,
      },
      timeout: "15s",
    }
  );

  const success = check(response, {
    "status is 200": (r) => r.status === 200,
    "has content": (r) => {
      try { return JSON.parse(r.body).choices[0].message.content.length > 0; }
      catch { return false; }
    },
  });

  errorRate.add(!success);

  if (response.status === 200) {
    try {
      const body = JSON.parse(response.body);
      citationCount.add(body.citations?.length || 0);
    } catch {}
  }

  // Critical: stay within 50 RPM
  sleep(1.5 + Math.random());
}
```

### Step 2: Run Load Test
```bash
set -euo pipefail
# Minimal test (5 queries, verify setup)
k6 run --vus 1 --duration 30s \
  --env PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY \
  perplexity-load-test.js

# Full test (respecting 50 RPM)
k6 run --env PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY \
  perplexity-load-test.js
```

### Step 3: Capacity Estimation
```typescript
interface CapacityEstimate {
  maxRPM: number;
  avgLatencyMs: number;
  maxConcurrent: number;
  dailyCapacity: number;
  estimatedDailyCost: number;
}

function estimateCapacity(
  rpm: number,
  avgLatency: number,
  model: "sonar" | "sonar-pro"
): CapacityEstimate {
  const costPerRequest = model === "sonar-pro" ? 0.02 : 0.005;

  return {
    maxRPM: rpm,
    avgLatencyMs: avgLatency,
    maxConcurrent: Math.floor((rpm / 60) * (avgLatency / 1000)),
    dailyCapacity: rpm * 60 * 24,
    estimatedDailyCost: rpm * 60 * 24 * costPerRequest,
  };
}

// Example: 50 RPM, 2s avg latency, sonar
const capacity = estimateCapacity(50, 2000, "sonar");
// { maxRPM: 50, maxConcurrent: 1, dailyCapacity: 72000, estimatedDailyCost: $360 }
```

### Step 4: Request Queue for Scale
```typescript
import PQueue from "p-queue";

// Queue that respects 50 RPM
const searchQueue = new PQueue({
  concurrency: 5,
  interval: 60_000,
  intervalCap: 45,  // 45 RPM (safety margin below 50)
});

async function scalableSearch(query: string) {
  return searchQueue.add(() =>
    perplexity.chat.completions.create({
      model: "sonar",
      messages: [{ role: "user", content: query }],
      max_tokens: 500,
    })
  );
}

// Queue status for monitoring
function queueStatus() {
  return {
    pending: searchQueue.pending,
    size: searchQueue.size,
    isPaused: searchQueue.isPaused,
  };
}
```

### Step 5: Scaling Strategy

| Scale | Queries/Day | Architecture | Cost/Day |
|-------|-------------|-------------|----------|
| Small | <1,000 | Direct API calls | <$5 |
| Medium | 1K-10K | Queue + cache (30%+ hit rate) | $5-$50 |
| Large | 10K-100K | Multi-key + cache + queue | $50-$500 |
| Enterprise | 100K+ | Contact Perplexity for custom limits | Custom |

For Medium+ scale, caching is mandatory. A 50% cache hit rate halves your API costs and doubles effective throughput.

## Benchmark Results Template
```markdown
## Perplexity Load Test Report
**Date:** YYYY-MM-DD | **Model:** sonar | **Duration:** 10 min

| Metric | Value |
|--------|-------|
| Total Requests | |
| Success Rate | |
| P50 Latency | |
| P95 Latency | |
| P99 Latency | |
| Avg Citations/Response | |
| Max Sustained RPM | |
| Estimated Cost | |
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 during load test | Exceeding 50 RPM | Reduce VUs, increase sleep |
| Inconsistent latency | Web search variability | Normal; use P95 not avg |
| k6 timeout | sonar-pro queries >15s | Increase timeout to 30s |
| High cost from test | Too many queries | Use `max_tokens: 50` for load tests |

## Output
- k6 load test script calibrated for Perplexity rate limits
- Capacity estimation calculator
- Request queue for sustained throughput
- Scaling strategy by volume tier

## Resources
- [k6 Documentation](https://k6.io/docs/)
- [Perplexity Rate Limits](https://docs.perplexity.ai/guides/rate-limits)

## Next Steps
For reliability patterns, see `perplexity-reliability-patterns`.
