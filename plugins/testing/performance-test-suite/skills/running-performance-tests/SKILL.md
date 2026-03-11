---
name: running-performance-tests
description: |
  Execute load testing, stress testing, and performance benchmarking.
  Use when performing specialized testing.
  Trigger with phrases like "run load tests", "test performance", or "benchmark the system".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:perf-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Performance Test Suite

## Overview

Execute load testing, stress testing, and performance benchmarking to identify bottlenecks, establish baseline metrics, and verify SLA compliance. Supports k6 (recommended), Artillery, Apache JMeter, Locust (Python), and autocannon (Node.js). Measures response times, throughput, error rates, and resource utilization under various load profiles including ramp-up, sustained load, spike, and soak tests.

## Prerequisites

- Performance testing tool installed (`k6`, `artillery`, `locust`, `jmeter`, or `autocannon`)
- Target application deployed in a production-like environment (not local dev)
- Baseline performance metrics or SLA targets (e.g., p95 < 200ms, 99.9% availability)
- Monitoring stack accessible (Grafana, CloudWatch, Datadog) for resource metrics during tests
- Test data sufficient to avoid cache-only responses

## Instructions

1. Define performance test scenarios based on production traffic patterns:
   - **Load test**: Simulate expected peak traffic (e.g., 500 concurrent users for 10 minutes).
   - **Stress test**: Ramp beyond expected capacity to find the breaking point.
   - **Spike test**: Sudden burst of traffic (0 to 1000 users in 10 seconds).
   - **Soak test**: Sustained moderate load for extended duration (1-4 hours) to detect memory leaks.
2. Create test scripts targeting critical endpoints:
   - Identify the top 5-10 most-hit API endpoints from production access logs.
   - Include both read (GET) and write (POST/PUT/DELETE) operations.
   - Simulate realistic user behavior with think time between requests.
   - Use parameterized data to avoid cache-only hits (randomize query parameters, user IDs).
3. Configure load profiles:
   - Define virtual user (VU) ramp-up stages (e.g., 10 VUs for 1 minute, then 50 VUs for 5 minutes).
   - Set test duration appropriate to the scenario (load: 10-15 min, soak: 1-4 hours).
   - Configure request timeouts matching production settings.
4. Execute the performance test:
   - Run from a machine with sufficient network bandwidth and CPU.
   - Avoid running from the same host as the application under test.
   - Monitor application metrics (CPU, memory, DB connections) during execution.
5. Analyze results against SLA thresholds:
   - p50, p90, p95, p99 response times.
   - Requests per second (throughput).
   - Error rate (target: < 0.1% for load test, higher tolerance for stress test).
   - Resource utilization (CPU < 80%, memory < 85% at peak load).
6. Identify and document bottlenecks:
   - Slow database queries (check slow query logs).
   - CPU-bound operations (profiling data).
   - Memory leaks (growing RSS over soak test).
   - Connection pool exhaustion (database or HTTP client).
7. Generate a performance report with visualizations and recommendations.

## Output

- Performance test scripts (k6 `.js`, Artillery `.yml`, or Locust `.py` files)
- Execution results with response time percentiles, throughput, and error rates
- Performance report comparing results against SLA thresholds
- Bottleneck analysis with specific recommendations
- CI integration configuration for automated performance regression detection

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Connection reset by peer | Server or load balancer dropping connections under load | Check max connections settings; increase connection pool size; verify keep-alive configuration |
| Timeouts spike at certain VU count | Application thread pool or database connection pool exhausted | Profile connection usage; increase pool size; add connection queuing; optimize slow queries |
| Inconsistent results between runs | Cache warming, garbage collection pauses, or noisy neighbor effects | Run a warm-up phase before measurement; use dedicated test infrastructure; average across 3 runs |
| Load generator CPU maxed out | Single machine cannot generate sufficient load | Distribute load generation across multiple machines; use cloud-based load generation services |
| All requests return cached responses | Test data not sufficiently varied | Randomize request parameters; use unique IDs per request; disable CDN caching for test environment |

## Examples

**k6 load test script:**
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up
    { duration: '5m', target: 50 },   // Sustained load
    { duration: '2m', target: 200 },  // Stress
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('https://api.test.com/products');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time OK': (r) => r.timings.duration < 300,
  });
  sleep(1); // Think time
}
```

**Artillery test configuration:**
```yaml
config:
  target: "https://api.test.com"
  phases:
    - duration: 120
      arrivalRate: 10
      name: "Warm up"
    - duration: 300
      arrivalRate: 50
      name: "Sustained load"
  ensure:
    p95: 200
    maxErrorRate: 1
scenarios:
  - flow:
      - get:
          url: "/api/products"
      - think: 1
      - post:
          url: "/api/cart"
          json: { productId: "{{ $randomString() }}" }
```

## Resources

- k6 documentation: https://grafana.com/docs/k6/latest/
- Artillery: https://www.artillery.io/docs
- Locust (Python): https://docs.locust.io/
- Apache JMeter: https://jmeter.apache.org/
- autocannon (Node.js): https://github.com/mcollina/autocannon
- Performance testing best practices: https://grafana.com/blog/2024/01/30/load-testing-best-practices/
