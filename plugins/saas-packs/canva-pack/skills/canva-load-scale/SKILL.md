---
name: canva-load-scale
description: |
  Implement Canva Connect API load testing, auto-scaling, and capacity planning.
  Use when running performance tests, planning capacity around Canva rate limits,
  or scaling Canva integrations for production workloads.
  Trigger with phrases like "canva load test", "canva scale",
  "canva performance test", "canva capacity", "canva k6", "canva benchmark".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Load & Scale

## Overview

Load test and scale Canva Connect API integrations. Since Canva enforces per-user rate limits, scaling means distributing load across users, not increasing per-user throughput.

## Canva Rate Limit Constraints

| Operation | Per-User Limit | Implication |
|-----------|---------------|-------------|
| Create design | 20/min | Max 1,200 designs/hr per user |
| List designs | 100/min | Generous for reads |
| Create export | 75/5min (500/24hr) | Max 500 exports/day per user |
| Integration export | 750/5min (5,000/24hr) | Shared across all users |
| Upload asset | 30/min | Max 1,800/hr per user |
| Autofill | 60/min | Max 3,600/hr per user |

**Key insight:** The integration-wide export limit of 5,000/day across ALL users is the most constraining for high-volume scenarios.

## k6 Load Test

```javascript
// canva-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('canva_error_rate');
const exportDuration = new Trend('canva_export_duration');

export const options = {
  scenarios: {
    design_operations: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '1m', target: 5 },    // Ramp up slowly
        { duration: '3m', target: 5 },    // Steady state
        { duration: '1m', target: 10 },   // Test rate limits
        { duration: '3m', target: 10 },   // Sustained load
        { duration: '1m', target: 0 },    // Ramp down
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<2000'],       // P95 < 2s
    canva_error_rate: ['rate<0.05'],          // < 5% errors
    canva_export_duration: ['p(95)<30000'],   // Exports < 30s
  },
};

const BASE = 'https://api.canva.com/rest/v1';
const TOKEN = __ENV.CANVA_ACCESS_TOKEN;
const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json',
};

export default function () {
  // 1. List designs (high rate limit — safe to call frequently)
  const listRes = http.get(`${BASE}/designs?limit=5`, { headers });
  check(listRes, { 'list 200': (r) => r.status === 200 });
  errorRate.add(listRes.status !== 200);

  if (listRes.status === 429) {
    const retryAfter = parseInt(listRes.headers['Retry-After'] || '60');
    sleep(retryAfter);
    return;
  }

  // 2. Create a design (20/min limit)
  const createRes = http.post(`${BASE}/designs`, JSON.stringify({
    design_type: { type: 'custom', width: 100, height: 100 },
    title: `k6 test ${Date.now()}`,
  }), { headers });

  check(createRes, { 'create 200': (r) => r.status === 200 });
  errorRate.add(createRes.status !== 200);

  if (createRes.status === 200) {
    const designId = createRes.json('design.id');

    // 3. Export (75/5min limit — most constrained)
    const exportStart = Date.now();
    const exportRes = http.post(`${BASE}/exports`, JSON.stringify({
      design_id: designId,
      format: { type: 'png' },
    }), { headers });

    if (exportRes.status === 200) {
      const jobId = exportRes.json('job.id');

      // Poll for completion
      let status = 'in_progress';
      while (status === 'in_progress') {
        sleep(2);
        const pollRes = http.get(`${BASE}/exports/${jobId}`, { headers });
        status = pollRes.json('job.status');
      }

      exportDuration.add(Date.now() - exportStart);
    }
  }

  sleep(3); // Stay under rate limits
}
```

### Run Load Test

```bash
k6 run --env CANVA_ACCESS_TOKEN="${CANVA_ACCESS_TOKEN}" canva-load-test.js

# With Grafana/InfluxDB output
k6 run --out influxdb=http://localhost:8086/k6 canva-load-test.js
```

## Scaling Architecture

```
Users requesting designs
       │
       ▼
┌─────────────┐
│   Load      │
│   Balancer  │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  App Pod 1  │     │  App Pod N  │
│  (per-user  │ ... │  (per-user  │
│   tokens)   │     │   tokens)   │
└──────┬──────┘     └──────┬──────┘
       │                    │
       ▼                    ▼
┌─────────────────────────────────┐
│        Rate Limiter Queue       │
│   (respects per-user + global   │
│    Canva rate limits)           │
└──────────────┬──────────────────┘
               │
               ▼
        api.canva.com
         /rest/v1/*
```

## Capacity Planning

```typescript
function estimateCanvaCapacity(users: number): {
  designsPerDay: number;
  exportsPerDay: number;
  constrainingFactor: string;
} {
  const perUserExportDaily = 500;
  const integrationExportDaily = 5000;

  const totalUserExports = users * perUserExportDaily;
  const effectiveExports = Math.min(totalUserExports, integrationExportDaily);

  return {
    designsPerDay: users * 1200 * 8,  // 20/min * 60 * 8 work hours
    exportsPerDay: effectiveExports,
    constrainingFactor: effectiveExports === integrationExportDaily
      ? `Integration-wide limit: ${integrationExportDaily}/day (hit at ${Math.ceil(integrationExportDaily / perUserExportDaily)} users)`
      : `Per-user limit: ${perUserExportDaily}/day per user`,
  };
}

// Example
const cap = estimateCanvaCapacity(20);
console.log(`Exports/day: ${cap.exportsPerDay}`);
console.log(`Constraint: ${cap.constrainingFactor}`);
// Exports/day: 5000 (integration limit)
// Constraint: Integration-wide limit: 5000/day (hit at 10 users)
```

## HPA Configuration

```yaml
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
  maxReplicas: 10
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
          name: canva_export_queue_depth
        target:
          type: AverageValue
          averageValue: 50
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| k6 all 429s | Rate limit hit | Increase sleep between iterations |
| Integration quota hit | > 5000 exports/day | Contact Canva for limit increase |
| Export timeouts | Complex designs | Increase poll timeout |
| Inconsistent results | Cold start | Add warm-up phase |

## Resources

- [Canva API Rate Limits](https://www.canva.dev/docs/connect/api-requests-responses/)
- [k6 Documentation](https://k6.io/docs/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

## Next Steps

For reliability patterns, see `canva-reliability-patterns`.
