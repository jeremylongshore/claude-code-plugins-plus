---
name: sentry-observability
description: |
  Integrate Sentry with observability stack.
  Use when connecting Sentry to logging, metrics, APM tools,
  or building unified observability dashboards.
  Trigger with phrases like "sentry observability", "sentry logging integration",
  "sentry metrics", "sentry datadog integration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Observability Integration

## Overview
Integrate Sentry with your broader observability stack for unified monitoring.

## Logging Integration

### Structured Logging with Sentry
```typescript
import * as Sentry from '@sentry/node';
import pino from 'pino';

const logger = pino({
  hooks: {
    logMethod(inputArgs, method, level) {
      // Send errors to Sentry
      if (level >= 50) { // error level
        const [msg, ...args] = inputArgs;
        Sentry.addBreadcrumb({
          category: 'log',
          message: typeof msg === 'string' ? msg : JSON.stringify(msg),
          level: 'error',
        });
      }
      return method.apply(this, inputArgs);
    },
  },
});

// Attach request ID for correlation
export function createRequestLogger(requestId: string) {
  Sentry.setTag('request_id', requestId);
  return logger.child({ requestId });
}
```

### Winston Integration
```typescript
import * as Sentry from '@sentry/node';
import winston from 'winston';

const sentryTransport = new winston.transports.Console({
  log(info, callback) {
    if (info.level === 'error') {
      Sentry.captureMessage(info.message, {
        level: 'error',
        extra: info,
      });
    }
    callback();
  },
});

const logger = winston.createLogger({
  transports: [sentryTransport],
});
```

## Metrics Integration

### Custom Metrics to Sentry
```typescript
import * as Sentry from '@sentry/node';

// Add metrics as tags/context
function trackMetric(name: string, value: number) {
  Sentry.setMeasurement(name, value, 'none');
}

// In transaction
const transaction = Sentry.startTransaction({ name: 'api.request' });
trackMetric('db_queries', 5);
trackMetric('cache_hits', 12);
transaction.finish();
```

### Prometheus + Sentry
```typescript
import { Registry, Counter } from 'prom-client';
import * as Sentry from '@sentry/node';

const errorCounter = new Counter({
  name: 'app_errors_total',
  help: 'Total application errors',
  labelNames: ['type', 'sentry_event_id'],
});

// Capture error and track metric
function captureError(error: Error) {
  const eventId = Sentry.captureException(error);
  errorCounter.inc({
    type: error.name,
    sentry_event_id: eventId,
  });
}
```

## APM Tool Integration

### Datadog + Sentry Correlation
```typescript
import * as Sentry from '@sentry/node';
import tracer from 'dd-trace';

// Add Datadog trace ID to Sentry events
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  beforeSend(event) {
    const span = tracer.scope().active();
    if (span) {
      event.tags = {
        ...event.tags,
        'dd.trace_id': span.context().toTraceId(),
        'dd.span_id': span.context().toSpanId(),
      };
    }
    return event;
  },
});
```

### New Relic + Sentry
```typescript
import * as Sentry from '@sentry/node';
import newrelic from 'newrelic';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  beforeSend(event) {
    // Add New Relic transaction link
    const transactionName = newrelic.getTransaction()?.name;
    if (transactionName) {
      event.tags = {
        ...event.tags,
        newrelic_transaction: transactionName,
      };
    }
    return event;
  },
});
```

## Distributed Tracing Correlation

### OpenTelemetry Integration
```typescript
import * as Sentry from '@sentry/node';
import { trace, context } from '@opentelemetry/api';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  integrations: [
    new Sentry.Integrations.OpenTelemetry(),
  ],
});

// Traces are automatically correlated
```

### Manual Trace Correlation
```typescript
// Add trace ID to Sentry events
Sentry.configureScope((scope) => {
  scope.setTag('trace_id', getTraceId());
  scope.setTag('span_id', getSpanId());
});
```

## Dashboard Integration

### Grafana Dashboard with Sentry Data
```json
{
  "panels": [
    {
      "title": "Sentry Error Rate",
      "type": "graph",
      "datasource": "sentry",
      "targets": [
        {
          "query": "sum(sentry_events{level='error'})"
        }
      ]
    }
  ]
}
```

### Sentry API for Custom Dashboards
```bash
# Get error counts
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$ORG/issues/?query=is:unresolved"
```

## Alerting Correlation

### PagerDuty Integration
1. Sentry Settings → Integrations → PagerDuty
2. Connect PagerDuty service
3. Configure alert rules to trigger incidents

### Slack with Context Links
```yaml
# Alert action with observability links
actions:
  - type: slack
    channel: "#alerts"
    template: |
      🚨 Error: {{ event.title }}
      Sentry: {{ event.url }}
      Logs: https://logs.company.com?trace_id={{ event.tags.trace_id }}
      APM: https://apm.company.com/trace/{{ event.tags.trace_id }}
```

## Best Practices

1. **Use consistent trace IDs** across all observability tools
2. **Correlate Sentry events** with logs and APM traces
3. **Avoid duplicate alerting** - route through single source
4. **Add context links** in alert messages
5. **Use Sentry for errors**, APM for performance, logs for debugging

## Resources
- [Sentry Integrations](https://docs.sentry.io/product/integrations/)
- [OpenTelemetry Integration](https://docs.sentry.io/platforms/javascript/performance/instrumentation/opentelemetry/)
