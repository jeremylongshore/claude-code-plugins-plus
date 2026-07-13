# Shopify Metrics Definitions

Prometheus metric definitions for Shopify-specific observability: query cost, rate limits, API duration, webhooks, and errors.

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
