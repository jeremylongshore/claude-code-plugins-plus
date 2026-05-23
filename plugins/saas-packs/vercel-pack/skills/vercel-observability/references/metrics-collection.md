# Metrics Collection

## Metrics Collection

### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `vercel_requests_total` | Counter | Total API requests |
| `vercel_request_duration_seconds` | Histogram | Request latency |
| `vercel_errors_total` | Counter | Error count by type |
| `vercel_rate_limit_remaining` | Gauge | Rate limit headroom |

### Prometheus Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const requestCounter = new Counter({
  name: 'vercel_requests_total',
  help: 'Total Vercel API requests',
  labelNames: ['method', 'status'],
  registers: [registry],
});

const requestDuration = new Histogram({
  name: 'vercel_request_duration_seconds',
  help: 'Vercel request duration',
  labelNames: ['method'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
  registers: [registry],
});

const errorCounter = new Counter({
  name: 'vercel_errors_total',
  help: 'Vercel errors by type',
  labelNames: ['error_type'],
  registers: [registry],
});
```

### Instrumented Client

```typescript
async function instrumentedRequest<T>(
  method: string,
  operation: () => Promise<T>
): Promise<T> {
  const timer = requestDuration.startTimer({ method });

  try {
    const result = await operation();
    requestCounter.inc({ method, status: 'success' });
    return result;
  } catch (error: any) {
    requestCounter.inc({ method, status: 'error' });
    errorCounter.inc({ error_type: error.code || 'unknown' });
    throw error;
  } finally {
    timer();
  }
}
```
