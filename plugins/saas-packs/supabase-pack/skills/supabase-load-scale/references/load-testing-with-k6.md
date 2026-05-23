# Load Testing With K6

## Load Testing with k6

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
