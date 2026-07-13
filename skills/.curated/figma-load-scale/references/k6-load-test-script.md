# Step 1: k6 Load Test Script

Deep-dive reference for the `figma-load-scale` skill — extracted from the 'Step 1: k6 Load Test Script' step of the workflow.

```javascript
// figma-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const figmaErrors = new Rate('figma_errors');
const figmaLatency = new Trend('figma_latency', true);

export const options = {
  scenarios: {
    // Test 1: Find your rate limit ceiling
    rate_limit_probe: {
      executor: 'constant-arrival-rate',
      rate: 10,           // 10 requests per second
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 5,
      maxVUs: 20,
    },
  },
  thresholds: {
    figma_errors: ['rate<0.10'],        // Less than 10% errors
    figma_latency: ['p(95)<3000'],      // P95 under 3 seconds
    http_req_duration: ['p(99)<5000'],  // P99 under 5 seconds
  },
};

const PAT = __ENV.FIGMA_PAT;
const FILE_KEY = __ENV.FIGMA_FILE_KEY;

export default function () {
  // Use a lightweight endpoint for rate limit testing
  const res = http.get(
    `https://api.figma.com/v1/files/${FILE_KEY}?depth=1`,
    {
      headers: { 'X-Figma-Token': PAT },
      tags: { endpoint: 'files' },
    }
  );

  figmaLatency.add(res.timings.duration);

  const isError = res.status !== 200;
  figmaErrors.add(isError);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'not rate limited': (r) => r.status !== 429,
    'latency < 2s': (r) => r.timings.duration < 2000,
  });

  if (res.status === 429) {
    const retryAfter = parseInt(res.headers['Retry-After'] || '60');
    console.log(`Rate limited. Retry-After: ${retryAfter}s`);
    sleep(retryAfter);
  } else {
    sleep(0.1); // 100ms between requests
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
