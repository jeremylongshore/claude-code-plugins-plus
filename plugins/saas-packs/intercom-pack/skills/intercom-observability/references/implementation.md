# Intercom Observability — Full Implementation

Complete, copy-pasteable implementation of every observability layer summarized in
`SKILL.md`. Each section is self-contained TypeScript / YAML you can drop into an
Intercom integration.

## Step 1: Prometheus Metrics for Intercom API Calls

```typescript
import { Registry, Counter, Histogram, Gauge } from "prom-client";

const registry = new Registry();

// Total API requests by endpoint and status
const intercomRequests = new Counter({
  name: "intercom_api_requests_total",
  help: "Total Intercom API requests",
  labelNames: ["endpoint", "method", "status"] as const,
  registers: [registry],
});

// Request duration by endpoint
const intercomDuration = new Histogram({
  name: "intercom_api_request_duration_seconds",
  help: "Intercom API request duration in seconds",
  labelNames: ["endpoint", "method"] as const,
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

// Error counter by type
const intercomErrors = new Counter({
  name: "intercom_api_errors_total",
  help: "Intercom API errors by type",
  labelNames: ["endpoint", "error_code", "status_code"] as const,
  registers: [registry],
});

// Rate limit remaining gauge
const intercomRateLimit = new Gauge({
  name: "intercom_rate_limit_remaining",
  help: "Intercom API rate limit remaining requests",
  registers: [registry],
});

// Webhook processing metrics
const webhookProcessed = new Counter({
  name: "intercom_webhooks_processed_total",
  help: "Intercom webhooks processed by topic",
  labelNames: ["topic", "status"] as const,
  registers: [registry],
});
```

## Step 2: Instrumented API Client Wrapper

```typescript
import { IntercomClient, IntercomError } from "intercom-client";

function instrumentedClient(client: IntercomClient): IntercomClient {
  return new Proxy(client, {
    get(target, prop) {
      const value = (target as any)[prop];
      if (typeof value === "object" && value !== null) {
        // Wrap service objects (contacts, conversations, etc.)
        return new Proxy(value, {
          get(serviceTarget, methodName) {
            const method = (serviceTarget as any)[methodName];
            if (typeof method !== "function") return method;

            return async (...args: any[]) => {
              const endpoint = `${String(prop)}.${String(methodName)}`;
              const timer = intercomDuration.startTimer({ endpoint, method: "API" });

              try {
                const result = await method.apply(serviceTarget, args);
                intercomRequests.inc({ endpoint, method: "API", status: "success" });
                return result;
              } catch (err) {
                if (err instanceof IntercomError) {
                  const statusCode = String(err.statusCode ?? "unknown");
                  const errorCode = err.body?.errors?.[0]?.code ?? "unknown";
                  intercomRequests.inc({ endpoint, method: "API", status: "error" });
                  intercomErrors.inc({ endpoint, error_code: errorCode, status_code: statusCode });

                  // Track rate limit from error response
                  if (err.statusCode === 429) {
                    intercomRateLimit.set(0);
                  }
                }
                throw err;
              } finally {
                timer();
              }
            };
          },
        });
      }
      return value;
    },
  });
}

// Usage
const rawClient = new IntercomClient({ token: process.env.INTERCOM_ACCESS_TOKEN! });
const client = instrumentedClient(rawClient);
```

## Step 3: Structured Logging

```typescript
import pino from "pino";

const logger = pino({
  name: "intercom",
  level: process.env.LOG_LEVEL || "info",
  serializers: {
    // Redact PII from logs
    contact: (contact: any) => ({
      id: contact.id,
      role: contact.role,
      // Never log email, name, phone
    }),
    err: pino.stdSerializers.err,
  },
});

// Intercom operation logger
function logIntercomOp(
  operation: string,
  details: Record<string, any>,
  durationMs: number
): void {
  logger.info({
    service: "intercom",
    operation,
    duration_ms: Math.round(durationMs),
    ...details,
  });
}

// Webhook logger
function logWebhook(
  topic: string,
  notificationId: string,
  status: "processed" | "failed" | "skipped",
  durationMs?: number
): void {
  logger.info({
    service: "intercom",
    type: "webhook",
    topic,
    notification_id: notificationId,
    status,
    duration_ms: durationMs ? Math.round(durationMs) : undefined,
  });
}
```

## Step 4: OpenTelemetry Tracing

```typescript
import { trace, SpanStatusCode, Span } from "@opentelemetry/api";

const tracer = trace.getTracer("intercom-integration");

async function tracedIntercomCall<T>(
  operationName: string,
  attributes: Record<string, string>,
  operation: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(
    `intercom.${operationName}`,
    { attributes },
    async (span: Span) => {
      try {
        const result = await operation();
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (err: any) {
        span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
        span.recordException(err);

        if (err instanceof IntercomError) {
          span.setAttribute("intercom.status_code", err.statusCode ?? 0);
          span.setAttribute("intercom.error_code", err.body?.errors?.[0]?.code ?? "unknown");
          span.setAttribute("intercom.request_id", err.body?.request_id ?? "");
        }

        throw err;
      } finally {
        span.end();
      }
    }
  );
}

// Usage
const contact = await tracedIntercomCall(
  "contacts.find",
  { "intercom.contact_id": contactId },
  () => client.contacts.find({ contactId })
);
```

## Step 5: Alert Rules

```yaml
# prometheus/intercom-alerts.yml
groups:
  - name: intercom_integration
    rules:
      - alert: IntercomHighErrorRate
        expr: |
          rate(intercom_api_errors_total[5m]) /
          rate(intercom_api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Intercom error rate > 5%"
          description: "{{ $value | humanizePercentage }} of requests failing"

      - alert: IntercomHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(intercom_api_request_duration_seconds_bucket[5m])
          ) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Intercom P95 latency > 3s"

      - alert: IntercomRateLimitLow
        expr: intercom_rate_limit_remaining < 1000
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Intercom rate limit < 1000 remaining"
          description: "Only {{ $value }} requests remaining before rate limit"

      - alert: IntercomAuthFailures
        expr: rate(intercom_api_errors_total{status_code="401"}[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Intercom authentication failures detected"

      - alert: IntercomWebhookFailures
        expr: |
          rate(intercom_webhooks_processed_total{status="failed"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Intercom webhook processing failures"
```

## Step 6: Metrics Endpoint

```typescript
// Expose Prometheus metrics
app.get("/metrics", async (req, res) => {
  res.set("Content-Type", registry.contentType);
  res.send(await registry.metrics());
});
```

## Key Metrics Summary

| Metric | Type | Alert Threshold |
|--------|------|----------------|
| `intercom_api_requests_total` | Counter | N/A (baseline) |
| `intercom_api_request_duration_seconds` | Histogram | P95 > 3s |
| `intercom_api_errors_total` | Counter | > 5% error rate |
| `intercom_rate_limit_remaining` | Gauge | < 1000 |
| `intercom_webhooks_processed_total` | Counter | Failed > 10% |
