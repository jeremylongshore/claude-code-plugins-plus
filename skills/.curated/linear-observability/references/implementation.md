# Linear Observability - Implementation Details

## Metrics Collection (Prometheus)

```typescript
// lib/metrics.ts
import { Counter, Histogram, Gauge, Registry } from "prom-client";

const registry = new Registry();

export const linearRequestsTotal = new Counter({
  name: "linear_api_requests_total",
  help: "Total Linear API requests",
  labelNames: ["operation", "status"],
  registers: [registry],
});

export const linearRequestDuration = new Histogram({
  name: "linear_api_request_duration_seconds",
  help: "Linear API request duration in seconds",
  labelNames: ["operation"],
  buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

export const linearComplexityCost = new Histogram({
  name: "linear_api_complexity_cost",
  help: "Linear API query complexity cost",
  labelNames: ["operation"],
  buckets: [10, 50, 100, 250, 500, 1000, 2500],
  registers: [registry],
});

export const linearRateLimitRemaining = new Gauge({
  name: "linear_rate_limit_remaining",
  help: "Remaining Linear API rate limit",
  registers: [registry],
});

export const linearWebhooksReceived = new Counter({
  name: "linear_webhooks_received_total",
  help: "Total Linear webhooks received",
  labelNames: ["type", "action"],
  registers: [registry],
});

export const linearWebhookProcessingDuration = new Histogram({
  name: "linear_webhook_processing_duration_seconds",
  help: "Linear webhook processing duration",
  labelNames: ["type"],
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5],
  registers: [registry],
});

export const linearCacheHits = new Counter({
  name: "linear_cache_hits_total",
  help: "Total Linear cache hits",
  registers: [registry],
});

export const linearCacheMisses = new Counter({
  name: "linear_cache_misses_total",
  help: "Total Linear cache misses",
  registers: [registry],
});

export { registry };
```

## Instrumented Client Wrapper

```typescript
// lib/instrumented-client.ts
import { LinearClient } from "@linear/sdk";

export function createInstrumentedClient(apiKey: string): LinearClient {
  return new LinearClient({
    apiKey,
    fetch: async (url, init) => {
      const operation = extractOperationName(init?.body);
      const timer = linearRequestDuration.startTimer({ operation });

      try {
        const response = await fetch(url, init);
        const remaining = response.headers.get("x-ratelimit-remaining");
        const complexity = response.headers.get("x-complexity-remaining");
        if (remaining) linearRateLimitRemaining.set(parseInt(remaining));
        if (complexity) linearComplexityRemaining.set(parseInt(complexity));

        linearRequestsTotal.inc({ operation, status: response.ok ? "success" : "error" });
        timer();
        return response;
      } catch (error) {
        linearRequestsTotal.inc({ operation, status: "error" });
        timer();
        throw error;
      }
    },
  });
}

function extractOperationName(body: BodyInit | undefined): string {
  if (!body || typeof body !== "string") return "unknown";
  try {
    const parsed = JSON.parse(body);
    const match = parsed.query?.match(/(?:query|mutation)\s+(\w+)/);
    return match?.[1] || "anonymous";
  } catch { return "unknown"; }
}
```

## Structured Logging

```typescript
// lib/logger.ts
import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  base: { service: "linear-integration", environment: process.env.NODE_ENV },
});

export const linearLogger = logger.child({ component: "linear" });

export function logApiCall(operation: string, duration: number, success: boolean) {
  linearLogger.info({ event: "api_call", operation, duration_ms: duration, success });
}

export function logWebhook(type: string, action: string, id: string) {
  linearLogger.info({ event: "webhook_received", webhook_type: type, webhook_action: action, entity_id: id });
}

export function logError(error: Error, context: Record<string, unknown>) {
  linearLogger.error({ event: "error", error_message: error.message, error_stack: error.stack, ...context });
}
```

## Health Check Endpoint

```typescript
export async function healthCheck(client: LinearClient): Promise<HealthStatus> {
  const checks = { linear_api: { status: "unknown" }, cache: { status: "unknown" }, rate_limit: { status: "unknown" } };

  const start = Date.now();
  try {
    await client.viewer;
    checks.linear_api = { status: "healthy", latency_ms: Date.now() - start };
  } catch (error) {
    checks.linear_api = { status: "unhealthy", error: error.message };
  }

  const metrics = await registry.getMetricsAsJSON();
  const rateLimitMetric = metrics.find(m => m.name === "linear_rate_limit_remaining");
  if (rateLimitMetric) {
    const remaining = rateLimitMetric.values?.[0]?.value || 0;
    const percentage = (remaining / 1500) * 100;
    checks.rate_limit = {
      status: percentage > 10 ? "healthy" : percentage > 5 ? "degraded" : "unhealthy",
      remaining, percentage: Math.round(percentage),
    };
  }

  const statuses = Object.values(checks).map(c => c.status);
  let status = "healthy";
  if (statuses.includes("unhealthy")) status = "unhealthy";
  else if (statuses.includes("degraded")) status = "degraded";

  return { status, checks, timestamp: new Date().toISOString() };
}
```

## Alerting Rules (Prometheus)

```yaml
groups:
  - name: linear-integration
    rules:
      - alert: LinearHighErrorRate
        expr: sum(rate(linear_api_requests_total{status="error"}[5m])) / sum(rate(linear_api_requests_total[5m])) > 0.05
        for: 5m
        labels: { severity: warning }
        annotations: { summary: "Linear API error rate > 5%" }

      - alert: LinearRateLimitLow
        expr: linear_rate_limit_remaining < 100
        for: 2m
        labels: { severity: warning }
        annotations: { summary: "Only {{ $value }} requests remaining" }

      - alert: LinearSlowResponses
        expr: histogram_quantile(0.95, rate(linear_api_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels: { severity: warning }
        annotations: { summary: "95th percentile response time > 2s" }
```

## Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Linear Integration",
    "panels": [
      { "title": "API Request Rate", "type": "graph", "targets": [{ "expr": "sum(rate(linear_api_requests_total[5m])) by (status)" }] },
      { "title": "Request Latency (p95)", "type": "gauge", "targets": [{ "expr": "histogram_quantile(0.95, rate(linear_api_request_duration_seconds_bucket[5m]))" }] },
      { "title": "Rate Limit Remaining", "type": "stat", "targets": [{ "expr": "linear_rate_limit_remaining" }] },
      { "title": "Webhooks by Type", "type": "piechart", "targets": [{ "expr": "sum(linear_webhooks_received_total) by (type)" }] }
    ]
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
