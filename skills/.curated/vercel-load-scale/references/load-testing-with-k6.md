# Load Testing With K6

## Load Testing with k6

### Basic Load Test

```javascript
// vercel-load-test.js
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
    http_req_duration: ['p(95)<100'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const response = http.post(
    'https://api.vercel.com/v1/resource',
    JSON.stringify({ test: true }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${__ENV.VERCEL_API_KEY}`,
      },
    }
  );

  check(response, {
    'status is 200': (r) => r.status === 200,
    'latency < 100ms': (r) => r.timings.duration < 100,
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
k6 run --env VERCEL_API_KEY=${VERCEL_API_KEY} vercel-load-test.js

# Run with output to InfluxDB
k6 run --out influxdb=http://localhost:8086/k6 vercel-load-test.js
```
