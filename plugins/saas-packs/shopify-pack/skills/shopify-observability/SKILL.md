---
name: shopify-observability
description: |
  Set up observability for Shopify app integrations with query cost tracking,
  rate limit monitoring, webhook delivery metrics, and structured logging.
  Use when instrumenting a Shopify app for production monitoring, setting up
  Prometheus metrics for API health, or configuring alerts for rate limit issues.
  Trigger with phrases like "shopify monitoring", "shopify metrics",
  "shopify observability", "monitor shopify API", "shopify alerts", "shopify dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Observability

## Overview

Instrument your Shopify app to track GraphQL query cost, rate limit consumption, webhook delivery success, and API latency. Shopify-specific metrics that generic monitoring misses.

## Prerequisites

- Prometheus or compatible metrics backend
- pino or similar structured logger
- Shopify API client with response interception

## Instructions

### Step 1: Shopify-Specific Metrics

Define Prometheus counters, histograms, and gauges for query cost, rate limit headroom, REST bucket state, API duration, webhook processing, and error classification.

See [Shopify Metrics Definitions](references/shopify-metrics-definitions.md) for the complete metric registrations.

### Step 2: Instrumented GraphQL Client

Wrap the Shopify GraphQL client to automatically record query cost from `extensions.cost`, update rate limit gauges, and classify errors (throttled, auth, API error).

See [Instrumented GraphQL Client](references/instrumented-graphql-client.md) for the complete implementation.

### Step 3: REST API Header Tracking

Parse `X-Shopify-Shop-Api-Call-Limit` headers (e.g., `"32/40"`) from REST responses to track leaky bucket fill level. Warn when bucket exceeds 80% capacity.

```typescript
function trackRestHeaders(shop: string, headers: Record<string, string>): void {
  const callLimit = headers["x-shopify-shop-api-call-limit"];
  if (callLimit) {
    const [used, max] = callLimit.split("/").map(Number);
    restBucketGauge.set({ shop }, used);
    if (used > max * 0.8) {
      console.warn(`[shopify] REST bucket at ${used}/${max} for ${shop}`);
    }
  }
}
```

### Step 4: Webhook Observability

Track HMAC validation results, processing success/failure, and duration for all incoming webhooks.

See [Webhook Observability](references/webhook-observability.md) for the complete Express middleware.

### Step 5: Structured Logging

Pino-based logger with automatic PII redaction and Shopify-specific context fields (query cost, available points, operation name).

See [Structured Logging](references/structured-logging.md) for the complete implementation.

### Step 6: Alert Rules

Prometheus alert rules for low rate limits, high query cost (P95 > 500), webhook failures (> 10%), and API latency (P95 > 3s).

See [Alert Rules](references/alert-rules.md) for the complete Prometheus configuration.

## Output

- GraphQL query cost tracking with per-operation metrics
- Rate limit monitoring for both REST and GraphQL
- Webhook delivery and processing metrics
- Structured logs with automatic PII redaction
- Alert rules for critical Shopify-specific conditions

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing cost data | Query error before response | Check error handling wraps correctly |
| High cardinality | Per-shop labels | Aggregate by plan tier instead |
| Alert storms | Aggressive thresholds | Tune based on baseline traffic |
| Webhook metrics missing | Not instrumented | Add counter to webhook handler |

## Examples

### Metrics Endpoint

```typescript
app.get("/metrics", async (req, res) => {
  res.set("Content-Type", registry.contentType);
  res.send(await registry.metrics());
});
```

## Resources

- [Shopify Rate Limit Headers](https://shopify.dev/docs/api/usage/rate-limits)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/instrumentation/js/)
