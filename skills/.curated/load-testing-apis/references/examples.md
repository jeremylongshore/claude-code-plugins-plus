# API Load Testing Examples

## k6 Baseline Load Test

```javascript
// load-tests/scenarios/baseline.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '10m', target: 50 },
    { duration: '2m', target: 150 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
    http_reqs: ['rate>100'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';
const TOKEN = __ENV.API_TOKEN;

export default function () {
  const headers = { Authorization: `Bearer ${TOKEN}` };

  if (Math.random() < 0.7) {
    const res = http.get(`${BASE_URL}/api/products?page=1&limit=20`, { headers });
    check(res, { 'products 200': (r) => r.status === 200 });
  } else if (Math.random() < 0.67) {
    const id = Math.floor(Math.random() * 100) + 1;
    http.get(`${BASE_URL}/api/products/${id}`, { headers });
  } else {
    http.post(`${BASE_URL}/api/orders`,
      JSON.stringify({ productId: 1, quantity: 1 }),
      { headers: { ...headers, 'Content-Type': 'application/json' } });
  }
  sleep(Math.random() * 3 + 1);
}
```

## k6 Spike Test

```javascript
export const options = {
  stages: [
    { duration: '1m', target: 50 },
    { duration: '30s', target: 1000 },
    { duration: '2m', target: 1000 },
    { duration: '30s', target: 50 },
    { duration: '2m', target: 50 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.05'],
  },
};
```

## k6 Soak Test

```javascript
export const options = {
  stages: [
    { duration: '5m', target: 200 },
    { duration: '4h', target: 200 },
    { duration: '5m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};
```

## Artillery Configuration

```yaml
config:
  target: "http://localhost:3000"
  phases:
    - duration: 120
      arrivalRate: 10
      name: "Warm up"
    - duration: 600
      arrivalRate: 50
      name: "Sustained"
    - duration: 120
      arrivalRate: 150
      name: "Spike"
  defaults:
    headers:
      Authorization: "Bearer {{ $processEnvironment.API_TOKEN }}"
scenarios:
  - name: "Browse and purchase"
    flow:
      - get:
          url: "/api/products?page=1&limit=20"
          expect: [{ statusCode: 200 }]
      - think: 2
      - post:
          url: "/api/orders"
          json: { productId: "{{ $randomNumber(1, 50) }}", quantity: 1 }
          expect: [{ statusCode: 201 }]
```

## Running Tests

```bash
# k6 baseline
k6 run load-tests/scenarios/baseline.js \
  --env BASE_URL=http://staging.example.com \
  --env API_TOKEN=test_token_123

# Artillery
npx artillery run load-tests/scenarios/artillery-baseline.yml \
  --output reports/results.json
npx artillery report reports/results.json --output reports/report.html

# Quick wrk smoke test
wrk -t4 -c10 -d30s -H "Authorization: Bearer $TOKEN" http://localhost:3000/api/products
```

## Threshold Configuration

```json
{
  "slo": {
    "availability": 0.999,
    "latency": { "p50": 100, "p95": 500, "p99": 1000 },
    "throughput": { "minimum_rps": 100 },
    "error_rate": { "maximum": 0.01 }
  }
}
```

## Performance Report

```markdown
## Baseline (50 VUs, 10 min)
| Metric | Result | SLO | Status |
|--------|--------|-----|--------|
| p50 latency | 45ms | <100ms | PASS |
| p95 latency | 230ms | <500ms | PASS |
| p99 latency | 680ms | <1000ms | PASS |
| Error rate | 0.2% | <1% | PASS |
| Throughput | 340 rps | >100 rps | PASS |

## Bottleneck: Database connection pool
At 500+ VUs, p99 spikes to 4200ms. PostgreSQL max_connections saturated at 100.
Recommendation: Increase pool to 200, add PgBouncer.
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
