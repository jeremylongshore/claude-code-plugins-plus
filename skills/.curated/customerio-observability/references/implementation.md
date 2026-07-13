# Customer.io Observability - Implementation Details

## Configuration

### Structured Logging for All CIO Operations

```typescript
import pino from 'pino';

const logger = pino({ name: 'customerio', level: process.env.LOG_LEVEL ?? 'info' });

function logCioCall(op: string, userId: string, duration: number, ok: boolean, meta?: any) {
  const entry = { service: 'customerio', op, userId, duration_ms: duration, success: ok, ...meta };
  ok ? logger.info(entry, `CIO ${op} OK`) : logger.error(entry, `CIO ${op} FAILED`);
}
```

## Advanced Patterns

### Prometheus Metrics Instrumentation

```typescript
import { Counter, Histogram, Gauge } from 'prom-client';

const cioRequests = new Counter({
  name: 'customerio_requests_total',
  help: 'Total Customer.io API requests',
  labelNames: ['operation', 'status'],
});

const cioLatency = new Histogram({
  name: 'customerio_request_duration_seconds',
  help: 'Customer.io request latency',
  labelNames: ['operation'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
});

const cioQueueDepth = new Gauge({
  name: 'customerio_queue_depth',
  help: 'Number of pending CIO events in queue',
});

export async function instrumentedTrack(userId: string, event: string, data: any) {
  const end = cioLatency.startTimer({ operation: 'track' });
  try {
    await cio.track(userId, { name: event, data });
    cioRequests.inc({ operation: 'track', status: 'success' });
  } catch (err) {
    cioRequests.inc({ operation: 'track', status: 'error' });
    throw err;
  } finally {
    end();
  }
}
```

### Alerting Rules

```yaml
# prometheus-alerts.yml
groups:
  - name: customerio
    rules:
      - alert: CioHighErrorRate
        expr: >
          rate(customerio_requests_total{status="error"}[5m])
          / rate(customerio_requests_total[5m]) > 0.05
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Customer.io error rate above 5%"
      - alert: CioHighLatency
        expr: >
          histogram_quantile(0.95,
            rate(customerio_request_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Customer.io p95 latency above 2s"
      - alert: CioQueueBacklog
        expr: customerio_queue_depth > 1000
        for: 10m
        labels: { severity: critical }
        annotations:
          summary: "Customer.io event queue backlog exceeding 1000"
```

### Grafana Dashboard JSON (Key Panels)

```json
{
  "title": "Customer.io Operations",
  "panels": [
    {
      "title": "Request Rate",
      "type": "timeseries",
      "targets": [{ "expr": "rate(customerio_requests_total[5m])" }]
    },
    {
      "title": "Error Rate %",
      "type": "stat",
      "targets": [{ "expr": "rate(customerio_requests_total{status='error'}[5m]) / rate(customerio_requests_total[5m]) * 100" }]
    },
    {
      "title": "Latency P50 / P95 / P99",
      "type": "timeseries",
      "targets": [
        { "expr": "histogram_quantile(0.5, rate(customerio_request_duration_seconds_bucket[5m]))", "legendFormat": "p50" },
        { "expr": "histogram_quantile(0.95, rate(customerio_request_duration_seconds_bucket[5m]))", "legendFormat": "p95" },
        { "expr": "histogram_quantile(0.99, rate(customerio_request_duration_seconds_bucket[5m]))", "legendFormat": "p99" }
      ]
    }
  ]
}
```

## Troubleshooting

### Checking Metrics Locally

```bash
# Verify metrics endpoint
curl -s localhost:9090/metrics | grep customerio

# Quick error rate check
curl -s localhost:9090/api/v1/query?query='rate(customerio_requests_total{status="error"}[5m])' | jq '.data.result'
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
