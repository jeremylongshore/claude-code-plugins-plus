# Juicebox Observability - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Structured Logging
```typescript
// lib/logger.ts
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label })
  },
  base: {
    service: 'juicebox-integration',
    environment: process.env.NODE_ENV
  }
});

export function createJuiceboxLogger(context: Record<string, any>) {
  return logger.child({ juicebox: true, ...context });
}

// Usage
const log = createJuiceboxLogger({ operation: 'search' });

log.info({ query, options }, 'Starting search');
log.info({ resultCount: results.length, duration }, 'Search completed');
log.error({ error: err.message, code: err.code }, 'Search failed');
```

### Step 2: Metrics Collection
```typescript
// lib/metrics.ts
import { Counter, Histogram, Registry } from 'prom-client';

const registry = new Registry();

// Request metrics
export const juiceboxRequests = new Counter({
  name: 'juicebox_requests_total',
  help: 'Total Juicebox API requests',
  labelNames: ['operation', 'status'],
  registers: [registry]
});

export const juiceboxLatency = new Histogram({
  name: 'juicebox_request_duration_seconds',
  help: 'Juicebox API request latency',
  labelNames: ['operation'],
  buckets: [0.1, 0.5, 1, 2, 5, 10],
  registers: [registry]
});

export const juiceboxCacheHits = new Counter({
  name: 'juicebox_cache_hits_total',
  help: 'Juicebox cache hits',
  labelNames: ['operation'],
  registers: [registry]
});

export const juiceboxQuotaUsage = new Counter({
  name: 'juicebox_quota_usage_total',
  help: 'Juicebox quota usage',
  labelNames: ['type'],
  registers: [registry]
});

// Instrumented client wrapper
export function instrumentJuiceboxCall<T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> {
  const end = juiceboxLatency.startTimer({ operation });

  return fn()
    .then(result => {
      juiceboxRequests.inc({ operation, status: 'success' });
      return result;
    })
    .catch(error => {
      juiceboxRequests.inc({ operation, status: 'error' });
      throw error;
    })
    .finally(() => {
      end();
    });
}
```

### Step 3: Distributed Tracing
```typescript
// lib/tracing.ts
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('juicebox-integration');

export async function withJuiceboxSpan<T>(
  name: string,
  fn: () => Promise<T>,
  attributes?: Record<string, string>
): Promise<T> {
  return tracer.startActiveSpan(name, async (span) => {
    try {
      if (attributes) {
        Object.entries(attributes).forEach(([key, value]) => {
          span.setAttribute(key, value);
        });
      }

      const result = await fn();

      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: (error as Error).message
      });
      span.recordException(error as Error);
      throw error;
    } finally {
      span.end();
    }
  });
}

// Usage
async function searchPeople(query: string): Promise<SearchResult> {
  return withJuiceboxSpan(
    'juicebox.search.people',
    () => client.search.people({ query }),
    { 'juicebox.query': query }
  );
}
```

### Step 4: Health Checks
```typescript
// routes/health.ts
import { Router } from 'express';

const router = Router();

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, {
    status: 'pass' | 'fail';
    latency?: number;
    message?: string;
  }>;
}

router.get('/health/live', (req, res) => {
  res.json({ status: 'ok' });
});

router.get('/health/ready', async (req, res) => {
  const health: HealthStatus = {
    status: 'healthy',
    checks: {}
  };

  // Check Juicebox API
  try {
    const start = Date.now();
    await juiceboxClient.auth.me();
    health.checks.juicebox = {
      status: 'pass',
      latency: Date.now() - start
    };
  } catch (error) {
    health.checks.juicebox = {
      status: 'fail',
      message: (error as Error).message
    };
    health.status = 'degraded';
  }

  // Check database
  try {
    const start = Date.now();
    await db.$queryRaw`SELECT 1`;
    health.checks.database = {
      status: 'pass',
      latency: Date.now() - start
    };
  } catch (error) {
    health.checks.database = {
      status: 'fail',
      message: (error as Error).message
    };
    health.status = 'unhealthy';
  }

  const statusCode = health.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(health);
});

export default router;
```

### Step 5: Alerting Rules
```yaml
# prometheus/alerts.yaml
groups:
  - name: juicebox
    rules:
      - alert: JuiceboxHighErrorRate
        expr: |
          rate(juicebox_requests_total{status="error"}[5m])
          / rate(juicebox_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Juicebox error rate above 5%"

      - alert: JuiceboxHighLatency
        expr: |
          histogram_quantile(0.95, rate(juicebox_request_duration_seconds_bucket[5m])) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Juicebox P95 latency above 5s"

      - alert: JuiceboxQuotaWarning
        expr: |
          juicebox_quota_usage_total > 0.8 * juicebox_quota_limit
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Juicebox quota usage above 80%"
```

## Grafana Dashboard

```json
{
  "title": "Juicebox Integration",
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(juicebox_requests_total[5m])",
          "legendFormat": "{{operation}} - {{status}}"
        }
      ]
    },
    {
      "title": "Latency P95",
      "type": "graph",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(juicebox_request_duration_seconds_bucket[5m]))",
          "legendFormat": "{{operation}}"
        }
      ]
    },
    {
      "title": "Cache Hit Rate",
      "type": "stat",
      "targets": [
        {
          "expr": "rate(juicebox_cache_hits_total[5m]) / rate(juicebox_requests_total[5m])"
        }
      ]
    }
  ]
}
```
