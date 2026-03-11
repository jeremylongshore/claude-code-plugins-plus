# Documenso Observability - Implementation Guide

## Metrics Collection

### Step 1: Core Metrics Definition

```typescript
// src/observability/metrics.ts
import { Counter, Histogram, Gauge, Registry } from "prom-client";

// Create custom registry
const registry = new Registry();

// Request metrics
const requestCounter = new Counter({
  name: "documenso_requests_total",
  help: "Total number of Documenso API requests",
  labelNames: ["operation", "status"],
  registers: [registry],
});

const requestDuration = new Histogram({
  name: "documenso_request_duration_seconds",
  help: "Documenso API request duration in seconds",
  labelNames: ["operation"],
  buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

// Document metrics
const documentsCreated = new Counter({
  name: "documenso_documents_created_total",
  help: "Total documents created",
  registers: [registry],
});

const documentsCompleted = new Counter({
  name: "documenso_documents_completed_total",
  help: "Total documents completed",
  registers: [registry],
});

const activeDocuments = new Gauge({
  name: "documenso_active_documents",
  help: "Number of documents pending signatures",
  registers: [registry],
});

// Error metrics
const errorCounter = new Counter({
  name: "documenso_errors_total",
  help: "Total Documenso errors",
  labelNames: ["operation", "error_code"],
  registers: [registry],
});

const rateLimitHits = new Counter({
  name: "documenso_rate_limit_hits_total",
  help: "Total rate limit (429) responses",
  registers: [registry],
});

export {
  registry,
  requestCounter,
  requestDuration,
  documentsCreated,
  documentsCompleted,
  activeDocuments,
  errorCounter,
  rateLimitHits,
};
```

### Step 2: Instrumented Client Wrapper

```typescript
// src/observability/instrumented-client.ts
import { Documenso } from "@documenso/sdk-typescript";
import {
  requestCounter,
  requestDuration,
  errorCounter,
  rateLimitHits,
} from "./metrics";

export function createInstrumentedClient(
  baseClient: Documenso
): Documenso {
  return new Proxy(baseClient, {
    get(target, prop) {
      const value = (target as any)[prop];

      if (typeof value === "object" && value !== null) {
        // Proxy nested objects (documents, templates, etc.)
        return new Proxy(value, {
          get(nestedTarget, nestedProp) {
            const method = (nestedTarget as any)[nestedProp];

            if (typeof method === "function") {
              return async (...args: any[]) => {
                const operation = `${String(prop)}.${String(nestedProp)}`;
                const timer = requestDuration.startTimer({ operation });

                try {
                  const result = await method.apply(nestedTarget, args);
                  requestCounter.inc({ operation, status: "success" });
                  return result;
                } catch (error: any) {
                  const status =
                    error.statusCode === 429 ? "rate_limited" : "error";
                  requestCounter.inc({ operation, status });

                  if (error.statusCode === 429) {
                    rateLimitHits.inc();
                  }

                  errorCounter.inc({
                    operation,
                    error_code: String(error.statusCode ?? "unknown"),
                  });

                  throw error;
                } finally {
                  timer();
                }
              };
            }
            return method;
          },
        });
      }
      return value;
    },
  });
}
```

### Step 3: Metrics Endpoint

```typescript
// src/api/metrics.ts
import express from "express";
import { registry } from "../observability/metrics";

const router = express.Router();

router.get("/metrics", async (req, res) => {
  try {
    res.set("Content-Type", registry.contentType);
    res.end(await registry.metrics());
  } catch (error) {
    res.status(500).end();
  }
});

export default router;
```

## Structured Logging

### Step 4: Logger Configuration

```typescript
// src/observability/logger.ts
import pino from "pino";

const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
  base: {
    service: "signing-service",
    environment: process.env.NODE_ENV,
  },
  redact: {
    paths: [
      "apiKey",
      "signingToken",
      "signingUrl",
      "*.apiKey",
      "*.signingToken",
      "req.headers.authorization",
    ],
    remove: true,
  },
});

// Create child loggers for different modules
export const documensoLogger = logger.child({ module: "documenso" });
export const webhookLogger = logger.child({ module: "webhook" });
export const jobLogger = logger.child({ module: "jobs" });

export default logger;
```

### Step 5: Request Logging

```typescript
// src/observability/request-logger.ts
import { documensoLogger } from "./logger";

export function logDocumensoRequest(
  operation: string,
  params: Record<string, any>,
  result: "success" | "error",
  duration: number,
  error?: Error
): void {
  const logData = {
    operation,
    params: sanitizeParams(params),
    result,
    durationMs: duration,
  };

  if (result === "success") {
    documensoLogger.info(logData, `Documenso ${operation} succeeded`);
  } else {
    documensoLogger.error(
      { ...logData, error: error?.message },
      `Documenso ${operation} failed`
    );
  }
}

function sanitizeParams(params: Record<string, any>): Record<string, any> {
  const sanitized = { ...params };

  // Remove sensitive fields
  delete sanitized.apiKey;
  delete sanitized.file; // Don't log file contents

  // Truncate large fields
  if (sanitized.recipients) {
    sanitized.recipients = sanitized.recipients.map((r: any) => ({
      email: r.email,
      role: r.role,
    }));
  }

  return sanitized;
}
```

### Step 6: Webhook Logging

```typescript
// src/webhooks/logging.ts
import { webhookLogger } from "../observability/logger";

export function logWebhookReceived(
  event: string,
  documentId: string,
  validSignature: boolean
): void {
  webhookLogger.info(
    {
      event,
      documentId,
      validSignature,
      timestamp: new Date().toISOString(),
    },
    `Webhook received: ${event}`
  );
}

export function logWebhookProcessed(
  event: string,
  documentId: string,
  duration: number,
  success: boolean
): void {
  const level = success ? "info" : "error";
  webhookLogger[level](
    {
      event,
      documentId,
      durationMs: duration,
      success,
    },
    `Webhook ${success ? "processed" : "failed"}: ${event}`
  );
}
```

## Distributed Tracing

### Step 7: OpenTelemetry Setup

```typescript
// src/observability/tracing.ts
import { NodeSDK } from "@opentelemetry/sdk-node";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { Resource } from "@opentelemetry/resources";
import { SemanticResourceAttributes } from "@opentelemetry/semantic-conventions";

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: "signing-service",
    [SemanticResourceAttributes.SERVICE_VERSION]:
      process.env.APP_VERSION ?? "unknown",
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? "http://localhost:4318/v1/traces",
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

export function initTracing(): void {
  sdk.start();
  console.log("OpenTelemetry tracing initialized");
}

export function shutdownTracing(): Promise<void> {
  return sdk.shutdown();
}
```

### Step 8: Custom Spans for Documenso Operations

```typescript
// src/observability/spans.ts
import { trace, SpanStatusCode, Span } from "@opentelemetry/api";

const tracer = trace.getTracer("documenso-client");

export async function withDocumensoSpan<T>(
  operation: string,
  attributes: Record<string, string>,
  fn: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(
    `documenso.${operation}`,
    {
      attributes: {
        "documenso.operation": operation,
        ...attributes,
      },
    },
    async (span: Span) => {
      try {
        const result = await fn();
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error: any) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });
        span.recordException(error);
        throw error;
      } finally {
        span.end();
      }
    }
  );
}

// Usage example
async function createDocumentWithTracing(title: string) {
  return withDocumensoSpan(
    "documents.create",
    { "document.title": title },
    () => client.documents.createV0({ title })
  );
}
```

## Health Check Endpoint

```typescript
// src/api/health.ts
import express from "express";
import { getDocumensoClient } from "../documenso/client";

const router = express.Router();

interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  checks: {
    documenso: {
      status: string;
      latencyMs: number;
      error?: string;
    };
  };
}

router.get("/health", async (req, res) => {
  const health: HealthStatus = {
    status: "healthy",
    timestamp: new Date().toISOString(),
    checks: {
      documenso: {
        status: "unknown",
        latencyMs: 0,
      },
    },
  };

  // Check Documenso connectivity
  const start = Date.now();
  try {
    const client = getDocumensoClient();
    await client.documents.findV0({ perPage: 1 });
    health.checks.documenso = {
      status: "healthy",
      latencyMs: Date.now() - start,
    };
  } catch (error: any) {
    health.checks.documenso = {
      status: "unhealthy",
      latencyMs: Date.now() - start,
      error: error.message,
    };
    health.status = "unhealthy";
  }

  const statusCode = health.status === "unhealthy" ? 503 : 200;
  res.status(statusCode).json(health);
});

export default router;
```

## Alerting Rules

### Prometheus Alerting Rules

```yaml
# alerts/documenso.yml
groups:
  - name: documenso
    rules:
      - alert: DocumensoHighErrorRate
        expr: |
          sum(rate(documenso_errors_total[5m])) /
          sum(rate(documenso_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High Documenso error rate"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: DocumensoHighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(documenso_request_duration_seconds_bucket[5m])) by (le)
          ) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Documenso API latency"
          description: "P95 latency is {{ $value }}s"

      - alert: DocumensoRateLimited
        expr: |
          sum(rate(documenso_rate_limit_hits_total[5m])) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Documenso rate limiting detected"

      - alert: DocumensoServiceDown
        expr: up{job="signing-service"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Signing service is down"
```

## Grafana Dashboard

```json
{
  "title": "Documenso Integration",
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "sum(rate(documenso_requests_total[5m])) by (operation)"
        }
      ]
    },
    {
      "title": "Error Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "sum(rate(documenso_errors_total[5m])) by (error_code)"
        }
      ]
    },
    {
      "title": "P95 Latency",
      "type": "graph",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(documenso_request_duration_seconds_bucket[5m])) by (le, operation))"
        }
      ]
    },
    {
      "title": "Documents Created",
      "type": "stat",
      "targets": [
        {
          "expr": "sum(increase(documenso_documents_created_total[24h]))"
        }
      ]
    }
  ]
}
```
