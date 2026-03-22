---
name: canva-load-scale
description: |
  Implement Canva load testing, auto-scaling, and capacity planning strategies.
  Use when running performance tests, configuring horizontal scaling,
  or planning capacity for Canva integrations.
  Trigger with phrases like "canva load test", "canva scale",
  "canva performance test", "canva capacity", "canva k6", "canva benchmark".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, canva]
---

# Canva Load & Scale

## Overview
Load testing, scaling strategies, and capacity planning for Canva integrations.

## Prerequisites
- k6 load testing tool installed
- Kubernetes cluster with HPA configured
- Prometheus for metrics collection
- Test environment API keys

## Load Testing with k6

### Basic Load Test
```javascript
// canva-load-test.js
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
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const response = http.post(
    'https://api.canva.com/v1/resource',
    JSON.stringify({ test: true }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${__ENV.CANVA_API_KEY}`,
      },
    }
  );

  check(response, {
    'status is 200': (r) => r.status === 200,
    'latency < 500ms': (r) => r.timings.duration < 500,
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
k6 run --env CANVA_API_KEY=${CANVA_API_KEY} canva-load-test.js

# Run with output to InfluxDB
k6 run --out influxdb=http://localhost:8086/k6 canva-load-test.js
```

## Scaling Patterns

### Horizontal Scaling
```yaml
# kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: canva-integration-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: canva-integration
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
          name: canva_queue_depth
        target:
          type: AverageValue
          averageValue: 100
```

### Connection Pooling
```typescript
import { Pool } from 'generic-pool';

const canvaPool = Pool.create({
  create: async () => {
    return new CanvaClient({
      apiKey: process.env.CANVA_API_KEY!,
    });
  },
  destroy: async (client) => {
    await client.close();
  },
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
});

async function withCanvaClient<T>(
  fn: (client: CanvaClient) => Promise<T>
): Promise<T> {
  const client = await canvaPool.acquire();
  try {
    return await fn(client);
  } finally {
    canvaPool.release(client);
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
| P95 Latency | > 1000ms | > 3000ms |

### Capacity Calculation
```typescript
interface CapacityEstimate {
  currentRPS: number;
  maxRPS: number;
  headroom: number;
  scaleRecommendation: string;
}

function estimateCanvaCapacity(
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

## Benchmark Results Template

```markdown
## Canva Performance Benchmark
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

## Instructions

### Step 1: Create Load Test Script
Write k6 test script with appropriate thresholds.

### Step 2: Configure Auto-Scaling
Set up HPA with CPU and custom metrics.

### Step 3: Run Load Test
Execute test and collect metrics.

### Step 4: Analyze and Document
Record results in benchmark template.

## Output
- Load test script created
- HPA configured
- Benchmark results documented
- Capacity recommendations defined

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| k6 timeout | Rate limited | Reduce RPS |
| HPA not scaling | Wrong metrics | Verify metric name |
| Connection refused | Pool exhausted | Increase pool size |
| Inconsistent results | Warm-up needed | Add ramp-up phase |

## Examples

### Quick k6 Test
```bash
k6 run --vus 10 --duration 30s canva-load-test.js
```

### Check Current Capacity
```typescript
const metrics = await getSystemMetrics();
const capacity = estimateCanvaCapacity(metrics);
console.log('Headroom:', capacity.headroom + '%');
console.log('Recommendation:', capacity.scaleRecommendation);
```

### Scale HPA Manually
```bash
kubectl scale deployment canva-integration --replicas=5
kubectl get hpa canva-integration-hpa
```

## Resources
- [k6 Documentation](https://k6.io/docs/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Canva Rate Limits](https://docs.canva.com/rate-limits)

## Next Steps
For reliability patterns, see `canva-reliability-patterns`.