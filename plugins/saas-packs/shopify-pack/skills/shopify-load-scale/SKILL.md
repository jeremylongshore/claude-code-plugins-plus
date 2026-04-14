---
name: shopify-load-scale
description: |
  Load test Shopify integrations respecting API rate limits, plan capacity with
  k6, and scale for Shopify Plus burst events (flash sales, BFCM).
  Use when preparing for high-traffic events, benchmarking API throughput, or sizing infrastructure for Shopify webhook volume.
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

k6 script with Shopify-specific custom metrics (throttle tracking, query cost trends, error rates) and automatic request pacing.

See [k6 Load Test Script](references/k6-load-test-script.md) for the complete test script.

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

Pre-BFCM preparation including cache pre-warming, Storefront API offloading, bulk inventory sync, and Kubernetes HPA configuration for webhook processing.

See [BFCM Preparation](references/bfcm-preparation.md) for application-level and infrastructure scaling patterns.

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

curl -sf "https://$STORE/admin/api/${SHOPIFY_API_VERSION:-2025-04}/graphql.json" \
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
