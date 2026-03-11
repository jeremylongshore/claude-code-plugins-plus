# MaintainX Observability - Implementation Guide

> Full implementation details and code examples for the `maintainx-observability` skill.

# MaintainX Observability

## Overview

Implement comprehensive observability (metrics, logging, tracing) for MaintainX integrations to ensure reliability and quick issue resolution.

## Prerequisites

- MaintainX integration deployed
- Monitoring platform (Datadog, Prometheus, CloudWatch)
- Log aggregation solution

## Three Pillars of Observability

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Observability Stack                               │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │     METRICS     │  │     LOGGING     │  │    TRACING      │     │
│  │                 │  │                 │  │                 │     │
│  │ - API latency   │  │ - Request logs  │  │ - Request flow  │     │
│  │ - Error rates   │  │ - Error details │  │ - Dependencies  │     │
│  │ - Throughput    │  │ - Audit trail   │  │ - Bottlenecks   │     │
│  │ - Cache hits    │  │ - Debug info    │  │ - Service map   │     │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘     │
│           │                    │                    │               │
│           └────────────────────┼────────────────────┘               │
│                                │                                    │
│                       ┌────────▼────────┐                          │
│                       │   DASHBOARDS    │                          │
│                       │   & ALERTS      │                          │
│                       └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Metrics Collection

```typescript
// src/observability/metrics.ts
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

// Create metrics registry
const registry = new Registry();

// API request metrics
const apiRequestsTotal = new Counter({
  name: 'maintainx_api_requests_total',
  help: 'Total number of MaintainX API requests',
  labelNames: ['endpoint', 'method', 'status'],
  registers: [registry],
});

const apiRequestDuration = new Histogram({
  name: 'maintainx_api_request_duration_seconds',
  help: 'MaintainX API request duration in seconds',
  labelNames: ['endpoint', 'method'],
  buckets: [0.1, 0.25, 0.5, 1, 2, 5, 10],
  registers: [registry],
});

const apiErrorsTotal = new Counter({
  name: 'maintainx_api_errors_total',
  help: 'Total number of MaintainX API errors',
  labelNames: ['endpoint', 'error_type', 'status_code'],
  registers: [registry],
});

// Cache metrics
const cacheHitsTotal = new Counter({
  name: 'maintainx_cache_hits_total',
  help: 'Total cache hits',
  labelNames: ['cache_type'],
  registers: [registry],
});

const cacheMissesTotal = new Counter({
  name: 'maintainx_cache_misses_total',
  help: 'Total cache misses',
  labelNames: ['cache_type'],
  registers: [registry],
});

// Rate limit metrics
const rateLimitRemaining = new Gauge({
  name: 'maintainx_rate_limit_remaining',
  help: 'Remaining API rate limit',
  registers: [registry],
});

// Business metrics
const workOrdersCreated = new Counter({
  name: 'maintainx_work_orders_created_total',
  help: 'Total work orders created via API',
  labelNames: ['priority'],
  registers: [registry],
});

// Instrumented client
class InstrumentedMaintainXClient {
  private client: MaintainXClient;

  async getWorkOrders(params?: any) {
    const timer = apiRequestDuration.startTimer({
      endpoint: '/workorders',
      method: 'GET',
    });

    try {
      const response = await this.client.getWorkOrders(params);

      apiRequestsTotal.inc({
        endpoint: '/workorders',
        method: 'GET',
        status: '200',
      });

      return response;
    } catch (error: any) {
      const status = error.response?.status || 'unknown';

      apiRequestsTotal.inc({
        endpoint: '/workorders',
        method: 'GET',
        status: String(status),
      });

      apiErrorsTotal.inc({
        endpoint: '/workorders',
        error_type: error.name,
        status_code: String(status),
      });

      throw error;
    } finally {
      timer();
    }
  }

  async createWorkOrder(data: any) {
    const response = await this.client.createWorkOrder(data);

    workOrdersCreated.inc({
      priority: data.priority || 'NONE',
    });

    return response;
  }
}

// Metrics endpoint
export function getMetricsEndpoint() {
  return async (req: Request, res: Response) => {
    res.set('Content-Type', registry.contentType);
    res.end(await registry.metrics());
  };
}
```

### Step 2: Structured Logging

```typescript
// src/observability/logger.ts
import winston from 'winston';

// Create structured logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'maintainx-integration',
    environment: process.env.NODE_ENV,
  },
  transports: [
    new winston.transports.Console(),
    // Add file or cloud transports as needed
  ],
});

// Log context for request tracing
interface LogContext {
  requestId: string;
  userId?: string;
  tenantId?: string;
  operation: string;
}

// Contextual logger
class ContextLogger {
  private context: LogContext;

  constructor(context: LogContext) {
    this.context = context;
  }

  info(message: string, meta?: any) {
    logger.info(message, { ...this.context, ...meta });
  }

  warn(message: string, meta?: any) {
    logger.warn(message, { ...this.context, ...meta });
  }

  error(message: string, error?: Error, meta?: any) {
    logger.error(message, {
      ...this.context,
      ...meta,
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : undefined,
    });
  }

  // API-specific logging
  apiRequest(endpoint: string, method: string, params?: any) {
    this.info('MaintainX API request', {
      endpoint,
      method,
      params: this.redactSensitive(params),
    });
  }

  apiResponse(endpoint: string, status: number, duration: number) {
    this.info('MaintainX API response', {
      endpoint,
      status,
      durationMs: duration,
    });
  }

  apiError(endpoint: string, error: Error, status?: number) {
    this.error('MaintainX API error', error, {
      endpoint,
      status,
    });
  }

  private redactSensitive(obj: any): any {
    if (!obj) return obj;

    const redacted = { ...obj };
    const sensitiveFields = ['apiKey', 'password', 'token', 'secret'];

    sensitiveFields.forEach(field => {
      if (redacted[field]) {
        redacted[field] = '[REDACTED]';
      }
    });

    return redacted;
  }
}

export { logger, ContextLogger };
```

### Step 3: Distributed Tracing

```typescript
// src/observability/tracing.ts
import { trace, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

// Initialize tracer
const provider = new NodeTracerProvider({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'maintainx-integration',
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.npm_package_version,
  }),
});

provider.register();

const tracer = trace.getTracer('maintainx-integration');

// Traced client
class TracedMaintainXClient {
  private client: MaintainXClient;

  async getWorkOrders(params?: any) {
    return tracer.startActiveSpan('maintainx.getWorkOrders', {
      kind: SpanKind.CLIENT,
      attributes: {
        'maintainx.endpoint': '/workorders',
        'maintainx.method': 'GET',
        'maintainx.params.limit': params?.limit,
      },
    }, async (span) => {
      try {
        const response = await this.client.getWorkOrders(params);

        span.setAttributes({
          'maintainx.response.count': response.workOrders.length,
          'maintainx.response.hasMore': !!response.nextCursor,
        });

        span.setStatus({ code: SpanStatusCode.OK });
        return response;
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
    });
  }

  async createWorkOrder(data: any) {
    return tracer.startActiveSpan('maintainx.createWorkOrder', {
      kind: SpanKind.CLIENT,
      attributes: {
        'maintainx.endpoint': '/workorders',
        'maintainx.method': 'POST',
        'maintainx.workorder.priority': data.priority,
      },
    }, async (span) => {
      try {
        const response = await this.client.createWorkOrder(data);

        span.setAttributes({
          'maintainx.workorder.id': response.id,
        });

        span.setStatus({ code: SpanStatusCode.OK });
        return response;
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
    });
  }
}
```

### Step 4: Health Checks

```typescript
// src/observability/health.ts

interface HealthCheck {
  name: string;
  check: () => Promise<boolean>;
  critical: boolean;
}

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: Record<string, { status: boolean; latencyMs: number }>;
}

class HealthChecker {
  private checks: HealthCheck[] = [];

  register(check: HealthCheck) {
    this.checks.push(check);
  }

  async getStatus(): Promise<HealthStatus> {
    const results: Record<string, { status: boolean; latencyMs: number }> = {};
    let hasCriticalFailure = false;
    let hasAnyFailure = false;

    for (const check of this.checks) {
      const start = Date.now();
      let status = false;

      try {
        status = await check.check();
      } catch (error) {
        status = false;
      }

      results[check.name] = {
        status,
        latencyMs: Date.now() - start,
      };

      if (!status) {
        hasAnyFailure = true;
        if (check.critical) {
          hasCriticalFailure = true;
        }
      }
    }

    return {
      status: hasCriticalFailure ? 'unhealthy' : hasAnyFailure ? 'degraded' : 'healthy',
      timestamp: new Date().toISOString(),
      checks: results,
    };
  }
}

// Register MaintainX health checks
const healthChecker = new HealthChecker();

healthChecker.register({
  name: 'maintainx_api',
  critical: true,
  check: async () => {
    const client = new MaintainXClient();
    await client.getUsers({ limit: 1 });
    return true;
  },
});

healthChecker.register({
  name: 'maintainx_cache',
  critical: false,
  check: async () => {
    // Check Redis connection
    const redis = getRedisClient();
    await redis.ping();
    return true;
  },
});

export { healthChecker, HealthStatus };
```

### Step 5: Alerting Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: maintainx-alerts
    rules:
      # High error rate
      - alert: MaintainXHighErrorRate
        expr: |
          sum(rate(maintainx_api_errors_total[5m])) /
          sum(rate(maintainx_api_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High MaintainX API error rate
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # High latency
      - alert: MaintainXHighLatency
        expr: |
          histogram_quantile(0.95, rate(maintainx_api_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High MaintainX API latency
          description: "P95 latency is {{ $value }}s (threshold: 2s)"

      # Rate limit approaching
      - alert: MaintainXRateLimitLow
        expr: maintainx_rate_limit_remaining < 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: MaintainX rate limit nearly exhausted
          description: "Only {{ $value }} requests remaining"

      # API unreachable
      - alert: MaintainXAPIDown
        expr: |
          up{job="maintainx-integration"} == 0 or
          absent(maintainx_api_requests_total)
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: MaintainX integration is down
          description: "No API requests recorded for 2 minutes"

      # Low cache hit rate
      - alert: MaintainXLowCacheHitRate
        expr: |
          sum(rate(maintainx_cache_hits_total[1h])) /
          (sum(rate(maintainx_cache_hits_total[1h])) + sum(rate(maintainx_cache_misses_total[1h]))) < 0.5
        for: 1h
        labels:
          severity: info
        annotations:
          summary: Low cache hit rate
          description: "Cache hit rate is {{ $value | humanizePercentage }}"
```

### Step 6: Dashboard Configuration

```json
{
  "dashboard": {
    "title": "MaintainX Integration Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(maintainx_api_requests_total[5m])) by (endpoint)",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(maintainx_api_errors_total[5m])) by (status_code)",
            "legendFormat": "HTTP {{status_code}}"
          }
        ]
      },
      {
        "title": "Latency P95",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(maintainx_api_request_duration_seconds_bucket[5m])) by (endpoint)",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(maintainx_cache_hits_total[1h])) / (sum(rate(maintainx_cache_hits_total[1h])) + sum(rate(maintainx_cache_misses_total[1h])))"
          }
        ]
      },
      {
        "title": "Work Orders Created (24h)",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(increase(maintainx_work_orders_created_total[24h]))"
          }
        ]
      }
    ]
  }
}
```

## Output

- Prometheus metrics collection
- Structured JSON logging
- Distributed tracing setup
- Health check endpoints
- Alerting rules configured
- Dashboard definition

## Key Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error rate | >5% | Investigate API issues |
| P95 latency | >2s | Check network/caching |
| Rate limit remaining | <10 | Reduce request rate |
| Cache hit rate | <50% | Review caching strategy |

## Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [MaintainX API Documentation](https://maintainx.dev/)

## Next Steps

For incident response, see `maintainx-incident-runbook`.
