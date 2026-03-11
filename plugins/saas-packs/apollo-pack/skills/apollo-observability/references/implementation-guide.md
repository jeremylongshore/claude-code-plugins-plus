# Apollo Observability - Implementation Guide

> Full implementation details and code examples for the `apollo-observability` skill.

# Apollo Observability

## Overview
Comprehensive observability setup for Apollo.io integrations including metrics, logging, tracing, and alerting.

## Metrics with Prometheus

```typescript
// src/lib/apollo/metrics.ts
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const register = new Registry();

// Request metrics
export const apolloRequestsTotal = new Counter({
  name: 'apollo_requests_total',
  help: 'Total number of Apollo API requests',
  labelNames: ['endpoint', 'method', 'status'],
  registers: [register],
});

export const apolloRequestDuration = new Histogram({
  name: 'apollo_request_duration_seconds',
  help: 'Duration of Apollo API requests in seconds',
  labelNames: ['endpoint', 'method'],
  buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [register],
});

// Rate limit metrics
export const apolloRateLimitRemaining = new Gauge({
  name: 'apollo_rate_limit_remaining',
  help: 'Remaining Apollo API rate limit',
  labelNames: ['endpoint'],
  registers: [register],
});

export const apolloRateLimitHits = new Counter({
  name: 'apollo_rate_limit_hits_total',
  help: 'Number of times rate limit was hit',
  registers: [register],
});

// Cache metrics
export const apolloCacheHits = new Counter({
  name: 'apollo_cache_hits_total',
  help: 'Number of Apollo cache hits',
  labelNames: ['endpoint'],
  registers: [register],
});

export const apolloCacheMisses = new Counter({
  name: 'apollo_cache_misses_total',
  help: 'Number of Apollo cache misses',
  labelNames: ['endpoint'],
  registers: [register],
});

// Credit usage
export const apolloCreditsUsed = new Counter({
  name: 'apollo_credits_used_total',
  help: 'Total Apollo credits consumed',
  labelNames: ['operation'],
  registers: [register],
});

// Error tracking
export const apolloErrors = new Counter({
  name: 'apollo_errors_total',
  help: 'Total Apollo API errors',
  labelNames: ['endpoint', 'error_type'],
  registers: [register],
});

export { register };
```

### Instrumented Client

```typescript
// src/lib/apollo/instrumented-client.ts
import { apolloRequestsTotal, apolloRequestDuration, apolloErrors } from './metrics';

export class InstrumentedApolloClient {
  async request<T>(endpoint: string, options: RequestOptions): Promise<T> {
    const labels = { endpoint, method: options.method || 'POST' };
    const endTimer = apolloRequestDuration.startTimer(labels);

    try {
      const response = await this.baseClient.request(endpoint, options);

      apolloRequestsTotal.inc({ ...labels, status: 'success' });

      // Track rate limit from headers
      const remaining = response.headers['x-ratelimit-remaining'];
      if (remaining) {
        apolloRateLimitRemaining.set({ endpoint }, parseInt(remaining));
      }

      return response.data;
    } catch (error: any) {
      const errorType = this.classifyError(error);
      apolloRequestsTotal.inc({ ...labels, status: 'error' });
      apolloErrors.inc({ endpoint, error_type: errorType });

      if (error.response?.status === 429) {
        apolloRateLimitHits.inc();
      }

      throw error;
    } finally {
      endTimer();
    }
  }

  private classifyError(error: any): string {
    const status = error.response?.status;
    if (status === 401) return 'auth_error';
    if (status === 403) return 'permission_error';
    if (status === 422) return 'validation_error';
    if (status === 429) return 'rate_limit';
    if (status >= 500) return 'server_error';
    if (error.code === 'ECONNREFUSED') return 'connection_error';
    if (error.code === 'ETIMEDOUT') return 'timeout';
    return 'unknown';
  }
}
```

## Structured Logging

```typescript
// src/lib/apollo/logger.ts
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  redact: {
    paths: ['api_key', '*.email', '*.phone', 'headers.authorization'],
    censor: '[REDACTED]',
  },
  base: {
    service: 'apollo-integration',
    environment: process.env.NODE_ENV,
  },
});

export const apolloLogger = logger.child({ component: 'apollo' });

// Request/response logging
export function logApolloRequest(context: {
  endpoint: string;
  method: string;
  params?: object;
  requestId: string;
}): void {
  apolloLogger.info({
    type: 'apollo_request',
    ...context,
    timestamp: new Date().toISOString(),
  });
}

export function logApolloResponse(context: {
  endpoint: string;
  status: number;
  durationMs: number;
  requestId: string;
  resultCount?: number;
}): void {
  apolloLogger.info({
    type: 'apollo_response',
    ...context,
    timestamp: new Date().toISOString(),
  });
}

export function logApolloError(context: {
  endpoint: string;
  error: Error;
  requestId: string;
  retryCount?: number;
}): void {
  apolloLogger.error({
    type: 'apollo_error',
    endpoint: context.endpoint,
    error: {
      name: context.error.name,
      message: context.error.message,
      stack: context.error.stack,
    },
    requestId: context.requestId,
    retryCount: context.retryCount,
    timestamp: new Date().toISOString(),
  });
}
```

## Distributed Tracing (OpenTelemetry)

```typescript
// src/lib/apollo/tracing.ts
import { trace, Span, SpanStatusCode, context as otelContext } from '@opentelemetry/api';
import { W3CTraceContextPropagator } from '@opentelemetry/core';

const tracer = trace.getTracer('apollo-integration');
const propagator = new W3CTraceContextPropagator();

export function createApolloSpan(
  name: string,
  attributes: Record<string, any>
): Span {
  return tracer.startSpan(`apollo.${name}`, {
    attributes: {
      'apollo.endpoint': attributes.endpoint,
      'apollo.method': attributes.method,
      'service.name': 'apollo-integration',
    },
  });
}

export async function traceApolloRequest<T>(
  endpoint: string,
  requestFn: () => Promise<T>
): Promise<T> {
  const span = createApolloSpan('request', { endpoint });

  try {
    const result = await otelContext.with(
      trace.setSpan(otelContext.active(), span),
      requestFn
    );

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

// Middleware for Express
export function apolloTracingMiddleware(req: any, res: any, next: any) {
  const span = createApolloSpan('http_request', {
    endpoint: req.path,
    method: req.method,
  });

  req.apolloSpan = span;

  res.on('finish', () => {
    span.setAttribute('http.status_code', res.statusCode);
    span.end();
  });

  next();
}
```

## Alerting Rules

```yaml
# prometheus/apollo-alerts.yml
groups:
  - name: apollo-alerts
    rules:
      # High error rate
      - alert: ApolloHighErrorRate
        expr: |
          sum(rate(apollo_errors_total[5m])) /
          sum(rate(apollo_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Apollo API error rate"
          description: "Apollo error rate is {{ $value | humanizePercentage }}"

      # Rate limit warnings
      - alert: ApolloRateLimitApproaching
        expr: apollo_rate_limit_remaining < 20
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Apollo rate limit approaching"
          description: "Only {{ $value }} requests remaining"

      - alert: ApolloRateLimitHit
        expr: increase(apollo_rate_limit_hits_total[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Apollo rate limit hit"
          description: "Rate limit was hit {{ $value }} times in last 5 minutes"

      # Latency alerts
      - alert: ApolloHighLatency
        expr: |
          histogram_quantile(0.95, rate(apollo_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Apollo API latency"
          description: "P95 latency is {{ $value | humanizeDuration }}"

      # Credit usage
      - alert: ApolloHighCreditUsage
        expr: |
          increase(apollo_credits_used_total[24h]) > 8000
        labels:
          severity: warning
        annotations:
          summary: "High Apollo credit consumption"
          description: "{{ $value }} credits used in last 24 hours"
```

## Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Apollo.io Integration",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(apollo_requests_total[5m])) by (endpoint)",
            "legendFormat": "{{ endpoint }}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(apollo_errors_total[5m])) by (error_type)",
            "legendFormat": "{{ error_type }}"
          }
        ]
      },
      {
        "title": "Request Duration (P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(apollo_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P95"
          }
        ]
      },
      {
        "title": "Rate Limit Status",
        "type": "gauge",
        "targets": [
          {
            "expr": "apollo_rate_limit_remaining",
            "legendFormat": "Remaining"
          }
        ],
        "thresholds": [
          { "value": 0, "color": "red" },
          { "value": 20, "color": "yellow" },
          { "value": 50, "color": "green" }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(apollo_cache_hits_total[5m])) / (sum(rate(apollo_cache_hits_total[5m])) + sum(rate(apollo_cache_misses_total[5m])))",
            "legendFormat": "Hit Rate"
          }
        ]
      },
      {
        "title": "Credits Used Today",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(apollo_credits_used_total[24h])"
          }
        ]
      }
    ]
  }
}
```

## Health Check Endpoint

```typescript
// src/routes/health/apollo.ts
import { Router } from 'express';
import { register } from '../../lib/apollo/metrics';

const router = Router();

router.get('/health/apollo', async (req, res) => {
  const checks = {
    api: false,
    rateLimit: false,
    cache: false,
  };

  try {
    // Check API connectivity
    await apollo.healthCheck();
    checks.api = true;

    // Check rate limit status
    const remaining = apolloRateLimitRemaining.get();
    checks.rateLimit = remaining > 10;

    // Check cache health
    const cacheStats = apolloCache.getStats();
    checks.cache = cacheStats.size > 0;

    const healthy = Object.values(checks).every(Boolean);

    res.status(healthy ? 200 : 503).json({
      status: healthy ? 'healthy' : 'degraded',
      checks,
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message,
      checks,
    });
  }
});

router.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

export default router;
```

## Output
- Prometheus metrics for all Apollo operations
- Structured JSON logging with PII redaction
- OpenTelemetry distributed tracing
- Alerting rules for errors, rate limits, latency
- Grafana dashboard configuration
- Health check endpoints

## Error Handling
| Issue | Resolution |
|-------|------------|
| Missing metrics | Verify instrumentation |
| Alert noise | Tune thresholds |
| Log volume | Adjust log levels |
| Trace gaps | Check propagation |

## Resources
- [Prometheus Documentation](https://prometheus.io/docs/)
- [OpenTelemetry](https://opentelemetry.io/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Pino Logger](https://getpino.io/)

## Next Steps
Proceed to `apollo-incident-runbook` for incident response.
