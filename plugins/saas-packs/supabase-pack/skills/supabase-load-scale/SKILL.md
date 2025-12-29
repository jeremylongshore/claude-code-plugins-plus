---
name: supabase-load-scale
description: |
  Supabase load testing, scaling, and capacity planning.
  Use when load testing or planning capacity for Supabase integration.
  Trigger with phrases like "supabase load test", "supabase scale",
  "supabase performance test", "supabase capacity".
allowed-tools: Read, Write, Edit, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Load & Scale

## Overview
Load testing, scaling strategies, and capacity planning for Supabase integrations.

## Prerequisites
- supabase-install-auth completed
- k6 or similar load testing tool installed
- Kubernetes cluster (for HPA testing)
- Metrics and monitoring configured

## Instructions

### Step 1: Load Testing with k6

### Basic Load Test
```javascript
// supabase-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up
    { duration: '5m', target: 10 },   // Steady state
    { duration: '2m', target: 50 },   // Ramp to peak
    { duration: '5m', target: 50 },   // Stress test
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const response = http.post(
    'https://api.supabase.com/v1/resource',
    JSON.stringify({ test: true }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${__ENV.SUPABASE_API_KEY}`,
      },
    }
  );

  check(response, {
    'status is 200': (r) => r.status === 200,
    'latency < 200ms': (r) => r.timings.duration < 200,
  });

  sleep(1);
}
```

### Run Load Test
```bash
# Install k6
brew install k6  # macOS
# or: sudo apt install k6  # Linux

# Run test
k6 run --env SUPABASE_API_KEY=${SUPABASE_API_KEY} supabase-load-test.js

# Run with output to InfluxDB
k6 run --out influxdb=http://localhost:8086/k6 supabase-load-test.js
```

## Scaling Patterns

### Horizontal Scaling
```yaml
# kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: supabase-integration-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: supabase-integration
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: supabase_queue_depth
        target:
          type: AverageValue
          averageValue: 100
```

### Connection Pooling
```typescript
import { Pool } from 'generic-pool';

const supabasePool = Pool.create({
  create: async () => {
    return new SupabaseClient({
      apiKey: process.env.SUPABASE_API_KEY!,
    });
  },
  destroy: async (client) => {
    await client.close();
  },
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
});

async function withSupabaseClient<T>(
  fn: (client: SupabaseClient) => Promise<T>
): Promise<T> {
  const client = await supabasePool.acquire();
  try {
    return await fn(client);
  } finally {
    supabasePool.release(client);
  }
}
```

## Capacity Planning

### Metrics to Monitor
| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Utilization | > 70% | > 85% |
| Memory Usage | > 75% | > 90% |
| Request Queue Depth | > 100 | > 500 |
| Error Rate | > 1% | > 5% |
| P95 Latency | > 500ms | > 2000ms |

### Capacity Calculation
```typescript
interface CapacityEstimate {
  currentRPS: number;
  maxRPS: number;
  headroom: number;
  scaleRecommendation: string;
}

function estimateSupabaseCapacity(
  metrics: SystemMetrics
): CapacityEstimate {
  const currentRPS = metrics.requestsPerSecond;
  const avgLatency = metrics.p50Latency;
  const cpuUtilization = metrics.cpuPercent;

  // Estimate max RPS based on current performance
  const maxRPS = currentRPS / (cpuUtilization / 100) * 0.7; // 70% target
  const headroom = ((maxRPS - currentRPS) / currentRPS) * 100;

  return {
    currentRPS,
    maxRPS: Math.floor(maxRPS),
    headroom: Math.round(headroom),
    scaleRecommendation: headroom < 30
      ? 'Scale up soon'
      : headroom < 50
      ? 'Monitor closely'
      : 'Adequate capacity',
  };
}
```

### Step 2: Benchmark Results Template

```markdown
## Supabase Performance Benchmark
**Date:** YYYY-MM-DD
**Environment:** [staging/production]
**SDK Version:** X.Y.Z

### Test Configuration
- Duration: 10 minutes
- Ramp: 10 → 100 → 10 VUs
- Target endpoint: /v1/resource

### Results
| Metric | Value |
|--------|-------|
| Total Requests | 50,000 |
| Success Rate | 99.9% |
| P50 Latency | 120ms |
| P95 Latency | 350ms |
| P99 Latency | 800ms |
| Max RPS Achieved | 150 |

### Observations
- [Key finding 1]
- [Key finding 2]

### Recommendations
- [Scaling recommendation]
```

## Output
- Load test results with latency percentiles
- Scaling configuration (HPA, connection pooling)
- Capacity estimates with headroom
- Benchmark documentation for future reference

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Test timeout | Endpoint too slow | Increase k6 timeout, check Supabase |
| Connection refused | Pod not ready | Wait for readiness, check HPA |
| Rate limit hit | Too aggressive ramp | Reduce VUs, add delays |
| Memory OOM | Pool too large | Reduce connection pool size |

## Examples

### Grafana Dashboard Queries

```promql
# RPS by endpoint
sum(rate(http_requests_total{service="supabase"}[1m])) by (endpoint)

# P95 latency
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service="supabase"}[5m])) by (le))

# Connection pool utilization
supabase_pool_connections_active / supabase_pool_connections_max
```

## Resources
- [k6 Documentation](https://k6.io/docs/)
- [Supabase Rate Limits](https://supabase.com/docs/rate-limits)
- [Kubernetes HPA Guide](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

## Next Steps
For reliability patterns, see `supabase-reliability-patterns`.