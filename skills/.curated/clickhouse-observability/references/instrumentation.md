# Application-Level Instrumentation & Structured Logging

Server-side metrics tell you what ClickHouse is doing; application-level metrics
tell you what YOUR service is asking of it. Instrument the client so query
latency, error codes, and insert volume are attributed to your own code paths.

## Application-Level Metrics (prom-client)

```typescript
import { Registry, Counter, Histogram, Gauge } from 'prom-client';

const registry = new Registry();

const queryDuration = new Histogram({
  name: 'clickhouse_query_duration_seconds',
  help: 'ClickHouse query duration',
  labelNames: ['query_type', 'status'],
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

const queryErrors = new Counter({
  name: 'clickhouse_query_errors_total',
  help: 'ClickHouse query errors',
  labelNames: ['error_code'],
  registers: [registry],
});

const insertRows = new Counter({
  name: 'clickhouse_insert_rows_total',
  help: 'Total rows inserted into ClickHouse',
  labelNames: ['table'],
  registers: [registry],
});

// Instrumented query wrapper
async function instrumentedQuery<T>(
  queryType: string,
  fn: () => Promise<T>,
): Promise<T> {
  const timer = queryDuration.startTimer({ query_type: queryType });
  try {
    const result = await fn();
    timer({ status: 'success' });
    return result;
  } catch (err: any) {
    timer({ status: 'error' });
    queryErrors.inc({ error_code: err.code ?? 'unknown' });
    throw err;
  }
}

// Expose /metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

## Structured Logging

```typescript
import pino from 'pino';

const logger = pino({ name: 'clickhouse' });

// Log query performance for analysis
function logQuery(queryType: string, durationMs: number, rowsRead: number) {
  logger.info({
    service: 'clickhouse',
    query_type: queryType,
    duration_ms: durationMs,
    rows_read: rowsRead,
    status: durationMs > 5000 ? 'slow' : 'ok',
  });
}
```
