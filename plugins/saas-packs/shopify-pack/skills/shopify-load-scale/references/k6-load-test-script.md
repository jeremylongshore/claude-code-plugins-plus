# k6 Load Test Script for Shopify

Load test script that tracks Shopify-specific metrics: throttle state, query costs, and error rates. Automatically paces requests to stay within rate limits.

```javascript
// shopify-load-test.js
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Counter, Trend } from "k6/metrics";

// Custom metrics
const shopifyErrors = new Rate("shopify_errors");
const throttledRequests = new Counter("shopify_throttled");
const queryCost = new Trend("shopify_query_cost");

export const options = {
  stages: [
    { duration: "1m", target: 2 },    // Warm up — 2 VUs
    { duration: "3m", target: 5 },    // Normal load
    { duration: "2m", target: 10 },   // Peak load
    { duration: "1m", target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<2000"],  // 95% under 2s
    shopify_errors: ["rate<0.05"],      // < 5% error rate
    shopify_throttled: ["count<10"],    // < 10 throttled requests
  },
};

const STORE = __ENV.SHOPIFY_STORE;
const TOKEN = __ENV.SHOPIFY_ACCESS_TOKEN;
// Use a recent stable API version (e.g., 2025-04)
const API_VERSION = __ENV.SHOPIFY_API_VERSION || "2025-04";

export default function () {
  const query = JSON.stringify({
    query: `{
      products(first: 10) {
        edges {
          node { id title status totalInventory }
        }
      }
    }`,
  });

  const res = http.post(
    `https://${STORE}/admin/api/${API_VERSION}/graphql.json`,
    query,
    {
      headers: {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": TOKEN,
      },
    }
  );

  const body = JSON.parse(res.body);

  // Track GraphQL-level throttling (returns 200 with THROTTLED error)
  const isThrottled = body.errors?.some(
    (e) => e.extensions?.code === "THROTTLED"
  );

  if (isThrottled) {
    throttledRequests.add(1);
    // Wait for restore rate to refill
    const available = body.extensions?.cost?.throttleStatus?.currentlyAvailable || 0;
    const restoreRate = body.extensions?.cost?.throttleStatus?.restoreRate || 50;
    const waitTime = Math.max(1, (100 - available) / restoreRate);
    sleep(waitTime);
    return;
  }

  // Track query cost
  if (body.extensions?.cost?.actualQueryCost) {
    queryCost.add(body.extensions.cost.actualQueryCost);
  }

  check(res, {
    "status is 200": (r) => r.status === 200,
    "no errors": () => !body.errors,
    "has products": () => body.data?.products?.edges?.length > 0,
  });

  shopifyErrors.add(res.status !== 200 || !!body.errors);

  // Pace requests to stay within rate limits
  // Standard: 50 points/sec restore, queries ~10 points each
  sleep(0.5); // ~2 queries/sec per VU
}
```
