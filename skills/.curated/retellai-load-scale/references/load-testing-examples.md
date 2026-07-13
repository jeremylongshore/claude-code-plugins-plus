# Load Testing Examples

## Basic k6 Load Test Script

```javascript
// retellai-load-test.js
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
    'https://api.retellai.com/v1/resource',
    JSON.stringify({ test: true }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${__ENV.RETELLAI_API_KEY}`,
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

## Run Commands

```bash
# Install k6
brew install k6  # macOS
# or: sudo apt install k6  # Linux

# Run test
k6 run --env RETELLAI_API_KEY=${RETELLAI_API_KEY} retellai-load-test.js

# Run with output to InfluxDB
k6 run --out influxdb=http://localhost:8086/k6 retellai-load-test.js
```

## Connection Pooling

```typescript
import { Pool } from 'generic-pool';

const retellaiPool = Pool.create({
  create: async () => {
    return new RetellAIClient({
      apiKey: process.env.RETELLAI_API_KEY!,
    });
  },
  destroy: async (client) => {
    await client.close();
  },
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
});

async function withRetellAIClient<T>(
  fn: (client: RetellAIClient) => Promise<T>
): Promise<T> {
  const client = await retellaiPool.acquire();
  try {
    return await fn(client);
  } finally {
    retellaiPool.release(client);
  }
}
```

## Capacity Estimation

```typescript
interface CapacityEstimate {
  currentRPS: number;
  maxRPS: number;
  headroom: number;
  scaleRecommendation: string;
}

function estimateRetellAICapacity(
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
## Retell AI Performance Benchmark
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

## Quick Commands

```bash
# Quick k6 test
k6 run --vus 10 --duration 30s retellai-load-test.js

# Check current capacity
# (use the estimateRetellAICapacity function from above)

# Scale HPA manually
set -euo pipefail
kubectl scale deployment retellai-integration --replicas=5
kubectl get hpa retellai-integration-hpa
```
