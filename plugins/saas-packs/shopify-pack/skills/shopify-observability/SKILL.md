---
name: shopify-observability
description: |
  Set up observability for Shopify app integrations with query cost tracking,
  rate limit monitoring, webhook delivery metrics, and structured logging.
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

```typescript
import { Registry, Counter, Histogram, Gauge } from "prom-client";

const registry = new Registry();

// GraphQL query cost tracking
const queryCostHistogram = new Histogram({
  name: "shopify_graphql_query_cost",
  help: "Shopify GraphQL actual query cost",
  labelNames: ["operation", "shop"],
  buckets: [1, 10, 50, 100, 250, 500, 1000],
  registers: [registry],
});

// Rate limit headroom
const rateLimitGauge = new Gauge({
  name: "shopify_rate_limit_available",
  help: "Shopify rate limit points currently available",
  labelNames: ["shop", "api_type"],
  registers: [registry],
});

// REST bucket state
const restBucketGauge = new Gauge({
  name: "shopify_rest_bucket_used",
  help: "REST API leaky bucket current fill level",
  labelNames: ["shop"],
  registers: [registry],
});

// API request duration
const apiDuration = new Histogram({
  name: "shopify_api_duration_seconds",
  help: "Shopify API call duration",
  labelNames: ["operation", "status", "api_type"],
  buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10],
  registers: [registry],
});

// Webhook processing
const webhookCounter = new Counter({
  name: "shopify_webhooks_total",
  help: "Shopify webhooks received",
  labelNames: ["topic", "status"], // status: success, error, invalid_hmac
  registers: [registry],
});

// API errors by type
const apiErrors = new Counter({
  name: "shopify_api_errors_total",
  help: "Shopify API errors by type",
  labelNames: ["error_type", "status_code"],
  registers: [registry],
});
```

### Step 2: Instrumented GraphQL Client

```typescript
async function instrumentedGraphqlQuery<T>(
  shop: string,
  operation: string,
  query: string,
  variables?: Record<string, unknown>
): Promise<T> {
  const timer = apiDuration.startTimer({ operation, api_type: "graphql" });

  try {
    const client = getGraphqlClient(shop);
    const response = await client.request(query, { variables });

    // Record cost metrics from Shopify's response
    const cost = response.extensions?.cost;
    if (cost) {
      queryCostHistogram.observe(
        { operation, shop },
        cost.actualQueryCost || cost.requestedQueryCost
      );
      rateLimitGauge.set(
        { shop, api_type: "graphql" },
        cost.throttleStatus.currentlyAvailable
      );
    }

    timer({ status: "success" });
    return response.data as T;
  } catch (error: any) {
    const statusCode = error.response?.code || "unknown";
    const errorType =
      error.body?.errors?.[0]?.extensions?.code === "THROTTLED"
        ? "throttled"
        : statusCode === 401
        ? "auth"
        : "api_error";

    apiErrors.inc({ error_type: errorType, status_code: String(statusCode) });
    timer({ status: "error" });
    throw error;
  }
}
```

### Step 3: REST API Header Tracking

```typescript
function trackRestHeaders(shop: string, headers: Record<string, string>): void {
  // Parse X-Shopify-Shop-Api-Call-Limit: "32/40"
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

```typescript
app.post("/webhooks", express.raw({ type: "application/json" }), (req, res) => {
  const topic = req.headers["x-shopify-topic"] as string;
  const shop = req.headers["x-shopify-shop-domain"] as string;

  // Track HMAC validation
  if (!verifyHmac(req.body, req.headers["x-shopify-hmac-sha256"]!)) {
    webhookCounter.inc({ topic, status: "invalid_hmac" });
    return res.status(401).send();
  }

  res.status(200).send("OK");

  // Track processing
  const start = Date.now();
  processWebhook(topic, shop, JSON.parse(req.body.toString()))
    .then(() => {
      webhookCounter.inc({ topic, status: "success" });
      apiDuration.observe(
        { operation: `webhook:${topic}`, status: "success", api_type: "webhook" },
        (Date.now() - start) / 1000
      );
    })
    .catch((err) => {
      webhookCounter.inc({ topic, status: "error" });
      console.error(`Webhook ${topic} failed:`, err.message);
    });
});
```

### Step 5: Structured Logging

```typescript
import pino from "pino";

const logger = pino({
  name: "shopify-app",
  level: process.env.LOG_LEVEL || "info",
  serializers: {
    // Redact sensitive fields automatically
    shopifyRequest: (req: any) => ({
      shop: req.shop,
      operation: req.operation,
      queryCost: req.cost?.actualQueryCost,
      available: req.cost?.throttleStatus?.currentlyAvailable,
      // Never log: accessToken, apiSecret, customer PII
    }),
  },
});

// Log every Shopify API call with structured context
function logShopifyCall(operation: string, shop: string, cost: any, durationMs: number) {
  logger.info({
    msg: "shopify_api_call",
    operation,
    shop,
    queryCost: cost?.actualQueryCost,
    requestedCost: cost?.requestedQueryCost,
    availablePoints: cost?.throttleStatus?.currentlyAvailable,
    durationMs,
  });
}
```

### Step 6: Alert Rules

```yaml
# prometheus/shopify-alerts.yml
groups:
  - name: shopify
    rules:
      - alert: ShopifyRateLimitLow
        expr: shopify_rate_limit_available < 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Shopify rate limit below 100 points for {{ $labels.shop }}"

      - alert: ShopifyHighQueryCost
        expr: histogram_quantile(0.95, rate(shopify_graphql_query_cost_bucket[5m])) > 500
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 Shopify query cost > 500 points"

      - alert: ShopifyWebhookFailures
        expr: rate(shopify_webhooks_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Shopify webhook processing failures > 10%"

      - alert: ShopifyAPILatencyHigh
        expr: histogram_quantile(0.95, rate(shopify_api_duration_seconds_bucket[5m])) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Shopify API P95 latency > 3 seconds"
```

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

## Next Steps

For incident response, see `shopify-incident-runbook`.
