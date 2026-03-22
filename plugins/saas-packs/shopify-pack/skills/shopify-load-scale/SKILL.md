---
name: shopify-load-scale
description: |
  Load test Shopify integrations respecting API rate limits, plan capacity with
  k6, and scale for Shopify Plus burst events (flash sales, BFCM).
  Trigger with phrases like "shopify load test", "shopify scale",
  "shopify BFCM", "shopify flash sale", "shopify capacity", "shopify k6 test".
allowed-tools: Read, Write, Edit, Bash(k6:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Load & Scale

## Overview

Load test Shopify app integrations while respecting API rate limits. Plan capacity for high-traffic events like Black Friday / Cyber Monday (BFCM).

## Prerequisites

- k6 load testing tool installed (`brew install k6`)
- Test store with API access (never load test production)
- Understanding of Shopify rate limits per plan

## Instructions

### Step 1: Understand Capacity Constraints

Your app's throughput is bounded by Shopify's rate limits, not your infrastructure:

| Plan | GraphQL Points | Restore Rate | Max Sustained QPS | Burst Capacity |
|------|---------------|-------------|-------------------|----------------|
| Standard | 1,000 | 50/sec | ~10 queries/sec | 1,000 points burst |
| Shopify Plus | 2,000 | 100/sec | ~20 queries/sec | 2,000 points burst |

A typical product query costs 10-50 points. At 50 points/query, Standard supports ~1 query/second sustained.

### Step 2: k6 Load Test Script

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
const API_VERSION = "2024-10";

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

### Step 3: Run Load Test

```bash
# Against a test store — NEVER production
k6 run \
  --env SHOPIFY_STORE=dev-store.myshopify.com \
  --env SHOPIFY_ACCESS_TOKEN=shpat_test_token \
  shopify-load-test.js

# Output results to InfluxDB for Grafana dashboards
k6 run --out influxdb=http://localhost:8086/k6 shopify-load-test.js
```

### Step 4: BFCM / Flash Sale Preparation

```typescript
// Pre-BFCM checklist for Shopify apps

// 1. Pre-fetch and cache product data before the sale starts
async function prewarmCache(productIds: string[]): Promise<void> {
  console.log(`Pre-warming cache for ${productIds.length} products`);
  for (const id of productIds) {
    await cachedQuery(`product:${id}`, () =>
      shopifyQuery(shop, PRODUCT_QUERY, { id })
    );
    await new Promise((r) => setTimeout(r, 100)); // Pace for rate limits
  }
}

// 2. Use Storefront API for customer-facing queries (separate rate limits)
// Admin API rate limits are shared across all apps
// Storefront API has its own higher limits

// 3. Use bulk operations to sync inventory before the event
// Don't rely on real-time inventory queries during peak traffic

// 4. Queue webhook processing — don't process inline during peak
async function handleOrderWebhook(payload: any): Promise<void> {
  // Queue for later processing instead of immediate API calls
  await queue.add("process-order", payload, {
    attempts: 5,
    backoff: { type: "exponential", delay: 5000 },
  });
}
```

### Step 5: Scaling Your App (Not Shopify's Limits)

Your infrastructure must handle the webhook volume:

```yaml
# BFCM webhook volume estimates:
# 100 orders/hour → 100 orders/create webhooks/hour
# 1,000 orders/hour → 1,000 webhooks/hour (Plus stores during BFCM)
# Each webhook must respond 200 within 5 seconds

# Kubernetes HPA for webhook processing
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shopify-webhook-processor
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shopify-webhook-processor
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Pods
      pods:
        metric:
          name: webhook_queue_depth
        target:
          type: AverageValue
          averageValue: "50"
```

## Output

- Load test script calibrated to Shopify rate limits
- Performance baseline documented
- BFCM preparation checklist completed
- Infrastructure scaling configured for webhook volume

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| k6 shows high error rate | Hitting rate limits | Reduce VUs, increase sleep between requests |
| All requests THROTTLED | Exceeding 50 points/sec | Space queries further apart |
| Webhooks backing up | Slow processing | Respond 200 immediately, queue processing |
| Cache stampede on sale start | All caches expire at once | Stagger cache TTLs, pre-warm |

## Examples

### Quick Capacity Estimate

```bash
# How many queries can you sustain?
# Standard plan: 50 points/sec restore
# Your query costs: check with debug header

curl -sf "https://$STORE/admin/api/2024-10/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Shopify-GraphQL-Cost-Debug: 1" \
  -d '{"query": "{ products(first: 10) { edges { node { id title } } } }"}' \
  | jq '"Query cost: \(.extensions.cost.actualQueryCost) points. Max sustained: \(50 / .extensions.cost.actualQueryCost) queries/sec"'
```

## Resources

- [Shopify Rate Limits](https://shopify.dev/docs/api/usage/rate-limits)
- [Shopify Plus Rate Limits](https://shopify.dev/changelog/increased-admin-api-rate-limits-for-shopify-plus)
- [k6 Documentation](https://k6.io/docs/)
- [BFCM Preparation Guide](https://www.shopify.com/blog/bfcm-checklist)

## Next Steps

For reliability patterns, see `shopify-reliability-patterns`.
