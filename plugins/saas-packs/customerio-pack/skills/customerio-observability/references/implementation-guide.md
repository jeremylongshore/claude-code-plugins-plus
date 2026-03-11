# Customer.io Observability - Implementation Guide

### Step 1: Metrics Collection
```typescript
// lib/metrics.ts
import { Counter, Histogram, Registry } from 'prom-client';

const register = new Registry();

// API metrics
export const apiLatency = new Histogram({
  name: 'customerio_api_latency_ms',
  help: 'Customer.io API call latency in milliseconds',
  labelNames: ['operation', 'status'],
  buckets: [10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
  registers: [register]
});

export const apiRequests = new Counter({
  name: 'customerio_api_requests_total',
  help: 'Total Customer.io API requests',
  labelNames: ['operation', 'status'],
  registers: [register]
});

export const apiErrors = new Counter({
  name: 'customerio_api_errors_total',
  help: 'Total Customer.io API errors',
  labelNames: ['operation', 'error_type'],
  registers: [register]
});

// Email metrics
export const emailsSent = new Counter({
  name: 'customerio_email_sent_total',
  help: 'Total emails sent via Customer.io',
  labelNames: ['campaign_type'],
  registers: [register]
});

export const emailsDelivered = new Counter({
  name: 'customerio_email_delivered_total',
  help: 'Total emails delivered',
  labelNames: ['campaign_type'],
  registers: [register]
});

export const emailsBounced = new Counter({
  name: 'customerio_email_bounced_total',
  help: 'Total email bounces',
  labelNames: ['bounce_type'],
  registers: [register]
});

// Webhook metrics
export const webhooksReceived = new Counter({
  name: 'customerio_webhook_received_total',
  help: 'Total webhooks received from Customer.io',
  labelNames: ['event_type'],
  registers: [register]
});

export { register };
```

### Step 2: Instrumented Client
```typescript
// lib/customerio-instrumented.ts
import { TrackClient, RegionUS } from '@customerio/track';
import * as metrics from './metrics';

export class InstrumentedCustomerIO {
  private client: TrackClient;

  constructor(siteId: string, apiKey: string) {
    this.client = new TrackClient(siteId, apiKey, { region: RegionUS });
  }

  async identify(userId: string, attributes: Record<string, any>): Promise<void> {
    const timer = metrics.apiLatency.startTimer({ operation: 'identify' });

    try {
      await this.client.identify(userId, attributes);
      timer({ status: 'success' });
      metrics.apiRequests.inc({ operation: 'identify', status: 'success' });
    } catch (error: any) {
      timer({ status: 'error' });
      metrics.apiRequests.inc({ operation: 'identify', status: 'error' });
      metrics.apiErrors.inc({
        operation: 'identify',
        error_type: error.statusCode || 'unknown'
      });
      throw error;
    }
  }

  async track(userId: string, event: string, data?: Record<string, any>): Promise<void> {
    const timer = metrics.apiLatency.startTimer({ operation: 'track' });

    try {
      await this.client.track(userId, { name: event, data });
      timer({ status: 'success' });
      metrics.apiRequests.inc({ operation: 'track', status: 'success' });
    } catch (error: any) {
      timer({ status: 'error' });
      metrics.apiRequests.inc({ operation: 'track', status: 'error' });
      metrics.apiErrors.inc({
        operation: 'track',
        error_type: error.statusCode || 'unknown'
      });
      throw error;
    }
  }
}
```

### Step 3: Structured Logging
```typescript
// lib/logger.ts
import pino from 'pino';

export const logger = pino({
  name: 'customerio',
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label })
  },
  base: {
    service: 'customerio-integration',
    environment: process.env.NODE_ENV
  }
});

// Logging wrapper for Customer.io operations
export function logOperation(
  operation: string,
  userId: string,
  data: any,
  result: 'success' | 'error',
  error?: Error
) {
  const logData = {
    operation,
    userId,
    result,
    data: sanitizeForLogging(data),
    ...(error && {
      error: {
        message: error.message,
        stack: error.stack
      }
    })
  };

  if (result === 'error') {
    logger.error(logData, `Customer.io ${operation} failed`);
  } else {
    logger.info(logData, `Customer.io ${operation} succeeded`);
  }
}

// Remove PII from logs
function sanitizeForLogging(data: any): any {
  if (!data) return data;

  const sanitized = { ...data };
  const piiFields = ['email', 'phone', 'address', 'ssn'];

  for (const field of piiFields) {
    if (sanitized[field]) {
      sanitized[field] = '[REDACTED]';
    }
  }

  return sanitized;
}
```

### Step 4: Distributed Tracing
```typescript
// lib/tracing.ts
import { trace, SpanKind, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('customerio-integration');

export async function withTracing<T>(
  operationName: string,
  attributes: Record<string, string>,
  operation: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(
    `customerio.${operationName}`,
    {
      kind: SpanKind.CLIENT,
      attributes: {
        'customerio.operation': operationName,
        ...attributes
      }
    },
    async (span) => {
      try {
        const result = await operation();
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error: any) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message
        });
        span.recordException(error);
        throw error;
      } finally {
        span.end();
      }
    }
  );
}

// Usage
await withTracing('identify', { userId }, () =>
  client.identify(userId, attributes)
);
```

### Step 5: Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Customer.io Integration",
    "panels": [
      {
        "title": "API Latency (p50, p95, p99)",
        "type": "timeseries",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(customerio_api_latency_ms_bucket[5m]))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(customerio_api_latency_ms_bucket[5m]))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(customerio_api_latency_ms_bucket[5m]))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "API Request Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(customerio_api_requests_total[5m])",
            "legendFormat": "{{operation}} - {{status}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(customerio_api_errors_total[5m])) / sum(rate(customerio_api_requests_total[5m])) * 100",
            "legendFormat": "Error Rate %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "value": 0, "color": "green" },
                { "value": 1, "color": "yellow" },
                { "value": 5, "color": "red" }
              ]
            }
          }
        }
      },
      {
        "title": "Email Delivery Funnel",
        "type": "bargauge",
        "targets": [
          {
            "expr": "sum(customerio_email_sent_total)",
            "legendFormat": "Sent"
          },
          {
            "expr": "sum(customerio_email_delivered_total)",
            "legendFormat": "Delivered"
          },
          {
            "expr": "sum(customerio_email_bounced_total)",
            "legendFormat": "Bounced"
          }
        ]
      }
    ]
  }
}
```

### Step 6: Alerting Rules
```yaml
# prometheus/alerts/customerio.yml
groups:
  - name: customerio
    rules:
      - alert: CustomerIOHighErrorRate
        expr: |
          sum(rate(customerio_api_errors_total[5m]))
          / sum(rate(customerio_api_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: Customer.io API error rate > 5%
          description: Error rate is {{ $value | printf "%.2f" }}%

      - alert: CustomerIOHighLatency
        expr: |
          histogram_quantile(0.99, rate(customerio_api_latency_ms_bucket[5m])) > 5000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: Customer.io p99 latency > 5s
          description: p99 latency is {{ $value | printf "%.0f" }}ms

      - alert: CustomerIOHighBounceRate
        expr: |
          sum(rate(customerio_email_bounced_total[1h]))
          / sum(rate(customerio_email_sent_total[1h])) > 0.05
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: Email bounce rate > 5%
          description: Bounce rate is {{ $value | printf "%.2f" }}%

      - alert: CustomerIOWebhookProcessingFailed
        expr: |
          sum(rate(customerio_webhook_errors_total[5m])) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: Customer.io webhook processing failures
          description: {{ $value }} webhooks failed in last 5 minutes
```
