---
name: adobe-load-scale
description: |
  Implement load testing, auto-scaling, and capacity planning for Adobe API
  integrations with k6 scripts targeting Firefly, PDF Services, and
  Photoshop APIs, plus Kubernetes HPA configuration.
  Trigger with phrases like "adobe load test", "adobe scale",
  "adobe performance test", "adobe capacity", "adobe benchmark".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Load & Scale

## Overview

Load testing and scaling strategies for Adobe API integrations. Adobe APIs are async and relatively slow (5-30s per operation), requiring different load testing approaches than typical REST APIs.

## Prerequisites

- k6 load testing tool installed (`npm install -g k6` or `brew install k6`)
- Adobe Developer Console credentials for testing (separate from production)
- Kubernetes cluster with HPA configured (for auto-scaling)
- Understanding of your Adobe API rate limits

## Instructions

### Step 1: k6 Load Test for Firefly API

```javascript
// adobe-firefly-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('adobe_errors');
const fireflyDuration = new Trend('firefly_duration');

export const options = {
  stages: [
    { duration: '1m', target: 2 },    // Warm up (Adobe APIs are slow)
    { duration: '3m', target: 5 },    // Steady state
    { duration: '2m', target: 10 },   // Stress (watch for 429s)
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<30000'],  // 30s — Firefly is async/slow
    adobe_errors: ['rate<0.05'],         // < 5% error rate
  },
};

// Pre-generate token (shared across VUs)
const TOKEN = __ENV.ADOBE_ACCESS_TOKEN;
const CLIENT_ID = __ENV.ADOBE_CLIENT_ID;

export default function () {
  const response = http.post(
    'https://firefly-api.adobe.io/v3/images/generate',
    JSON.stringify({
      prompt: `Load test image ${Date.now()}`,
      n: 1,
      size: { width: 512, height: 512 },  // Smallest size for speed
    }),
    {
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'x-api-key': CLIENT_ID,
        'Content-Type': 'application/json',
      },
      timeout: '60s',
    }
  );

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'status is not 429': (r) => r.status !== 429,
  });

  errorRate.add(!success);
  fireflyDuration.add(response.timings.duration);

  if (response.status === 429) {
    const retryAfter = parseInt(response.headers['Retry-After'] || '30');
    console.log(`Rate limited, waiting ${retryAfter}s`);
    sleep(retryAfter);
  } else {
    sleep(3); // Respect rate limits between requests
  }
}
```

### Step 2: k6 Load Test for PDF Services

```javascript
// adobe-pdf-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 3 },
    { duration: '5m', target: 10 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<15000'],  // PDF ops are faster than Firefly
    http_req_failed: ['rate<0.02'],
  },
};

export default function () {
  // Test your app's PDF endpoint (which calls Adobe PDF Services internally)
  const response = http.post(
    `${__ENV.APP_URL}/api/extract-pdf`,
    http.file(open('./test-fixtures/sample-5page.pdf', 'b'), 'test.pdf'),
    { timeout: '30s' }
  );

  check(response, {
    'extraction successful': (r) => r.status === 200,
    'has text content': (r) => JSON.parse(r.body).text?.length > 0,
  });

  sleep(2);
}
```

### Step 3: Run Load Tests

```bash
# 1. Generate access token for load test
export ADOBE_ACCESS_TOKEN=$(curl -s -X POST \
  'https://ims-na1.adobelogin.com/ims/token/v3' \
  -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}" | jq -r '.access_token')

# 2. Run Firefly load test
k6 run --env ADOBE_ACCESS_TOKEN=${ADOBE_ACCESS_TOKEN} \
  --env ADOBE_CLIENT_ID=${ADOBE_CLIENT_ID} \
  adobe-firefly-load.js

# 3. Run PDF Services load test
k6 run --env APP_URL=https://staging.yourapp.com \
  adobe-pdf-load.js

# 4. Export results to InfluxDB for Grafana dashboards
k6 run --out influxdb=http://localhost:8086/k6 adobe-firefly-load.js
```

### Step 4: Kubernetes Auto-Scaling

```yaml
# k8s/adobe-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: adobe-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: adobe-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
    # Scale on pending Adobe jobs (custom metric from Prometheus)
    - type: Pods
      pods:
        metric:
          name: adobe_pending_jobs
        target:
          type: AverageValue
          averageValue: 5
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300  # Slow scale-down (Adobe jobs are long)
```

### Step 5: Capacity Planning

```typescript
// Adobe-specific capacity considerations:
// 1. Each Firefly request blocks for 5-30s — need many concurrent workers
// 2. PDF Services is faster (2-10s) but has monthly transaction limits
// 3. Photoshop API jobs are async — workers poll and block on I/O
// 4. IMS token generation is shared — cache aggressively

interface AdobeCapacityPlan {
  api: string;
  peakRps: number;
  avgLatencyMs: number;
  concurrencyNeeded: number;  // peakRps * avgLatencyMs / 1000
  podsNeeded: number;         // concurrencyNeeded / connectionsPerPod
  monthlyTransactions: number;
  tierNeeded: string;
}

function planCapacity(metrics: {
  peakRps: number;
  avgLatencyMs: number;
  connectionsPerPod: number;
}): AdobeCapacityPlan {
  const concurrency = metrics.peakRps * metrics.avgLatencyMs / 1000;
  const pods = Math.ceil(concurrency / metrics.connectionsPerPod);

  return {
    api: 'firefly',
    peakRps: metrics.peakRps,
    avgLatencyMs: metrics.avgLatencyMs,
    concurrencyNeeded: Math.ceil(concurrency),
    podsNeeded: pods,
    monthlyTransactions: metrics.peakRps * 3600 * 8 * 22, // 8h/day, 22 days
    tierNeeded: pods > 5 ? 'Enterprise' : 'Pro',
  };
}

// Example: 2 RPS peak, 10s avg latency, 5 connections per pod
// concurrency = 2 * 10 = 20 concurrent requests
// pods = 20 / 5 = 4 pods minimum
```

## Output

- k6 load test scripts for Firefly and PDF Services
- Kubernetes HPA with Adobe-aware scaling metrics
- Capacity planning model accounting for async API latency
- Benchmark results template for documentation

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| All requests 429 in k6 | Rate limit exceeded | Reduce VU count; add sleep |
| k6 timeout | Adobe API > 60s | Increase k6 request timeout |
| HPA not scaling | Custom metric not exposed | Verify Prometheus metric exists |
| Token expires mid-test | Long test duration | Token valid 24h; pre-generate |

## Resources

- [k6 Documentation](https://k6.io/docs/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Firefly Async API](https://developer.adobe.com/firefly-services/docs/firefly-api/guides/how-tos/using-async-apis)

## Next Steps

For reliability patterns, see `adobe-reliability-patterns`.
