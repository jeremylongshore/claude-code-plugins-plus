# Metrics Collection

## Metrics Collection

### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `supabase_requests_total` | Counter | Total API requests |
| `supabase_request_duration_seconds` | Histogram | Request latency |
| `supabase_errors_total` | Counter | Error count by type |
| `supabase_rate_limit_remaining` | Gauge | Rate limit headroom |

### Prometheus Metrics

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const requestCounter = new Counter({
  name: 'supabase_requests_total',
  help: 'Total Supabase API requests',
  labelNames: ['method', 'status'],
  registers: [registry],
});

const requestDuration = new Histogram({
  name: 'supabase_request_duration_seconds',
  help: 'Supabase request duration',
  labelNames: ['method'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
  registers: [registry],
});

const errorCounter = new Counter({
  name: 'supabase_errors_total',
  help: 'Supabase errors by type',
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
