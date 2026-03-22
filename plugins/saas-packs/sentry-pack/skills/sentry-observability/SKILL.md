---
name: sentry-observability
description: |
  Integrate Sentry with your observability stack.
  Use when connecting Sentry to logging, metrics, APM tools,
  or building unified observability dashboards.
  Trigger with phrases like "sentry observability", "sentry logging integration",
  "sentry metrics", "sentry opentelemetry".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, observability, logging, opentelemetry, metrics]

---
# Sentry Observability

## Prerequisites
- Existing observability stack (logging, metrics, APM)
- Trace ID correlation strategy defined
- Dashboard platform available (Grafana, Datadog, etc.)
- Alert routing established

## Instructions

### 1. OpenTelemetry Integration (SDK v8)

Sentry SDK v8 is built on OpenTelemetry under the hood. You can connect Sentry to your existing OTel pipeline:

```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,

  // Sentry auto-uses OpenTelemetry for tracing in v8
  // Additional OTel exporters can be added:
  // The SDK creates an OTel TracerProvider automatically
});

// Access the OTel tracer for custom instrumentation
import { trace } from '@opentelemetry/api';

const tracer = trace.getTracer('my-app');
const span = tracer.startSpan('custom-operation');
// Sentry sees this span automatically via OTel bridge
span.end();
```

### 2. Structured Logging Integration

Connect your logger to Sentry for correlated error + log context:

```typescript
// Winston integration
import winston from 'winston';
import * as Sentry from '@sentry/node';

const logger = winston.createLogger({
  transports: [new winston.transports.Console()],
});

// Log errors to both Winston and Sentry
function logError(message: string, error: Error, context?: object) {
  // Log to file/stdout
  logger.error(message, { error: error.message, stack: error.stack, ...context });

  // Capture in Sentry with same context
  Sentry.withScope((scope) => {
    if (context) scope.setContext('log', context);
    scope.setTag('logger', 'winston');
    Sentry.captureException(error);
  });
}

// Add Sentry event ID to log entries for cross-referencing
function logWithSentryId(level: string, message: string, meta?: object) {
  const eventId = level === 'error'
    ? Sentry.captureMessage(message, 'error')
    : undefined;

  logger.log(level, message, {
    ...meta,
    ...(eventId && { sentry_event_id: eventId }),
  });
}
```

### 3. Request ID Correlation

Link logs, Sentry events, and traces with a shared request ID:

```typescript
import { randomUUID } from 'crypto';
import * as Sentry from '@sentry/node';

// Express middleware: attach request ID everywhere
app.use((req, res, next) => {
  const requestId = req.headers['x-request-id'] as string || randomUUID();
  req.requestId = requestId;
  res.setHeader('x-request-id', requestId);

  // Set in Sentry scope
  Sentry.setTag('request_id', requestId);

  // Set in logger context
  logger.defaultMeta = { ...logger.defaultMeta, request_id: requestId };

  next();
});

// Now all systems share the same request_id:
// - Sentry events: tags.request_id
// - Log entries: request_id field
// - HTTP responses: X-Request-Id header
// - Downstream services: X-Request-Id header propagated
```

### 4. Custom Metrics with Sentry

```typescript
// Sentry v8 supports custom metrics
import * as Sentry from '@sentry/node';

// Counter — track occurrences
Sentry.metrics.increment('api.requests', 1, {
  tags: { endpoint: '/api/users', method: 'GET', status: '200' },
});

// Gauge — track current values
Sentry.metrics.gauge('queue.depth', currentDepth, {
  tags: { queue: 'email-notifications' },
});

// Distribution — track value distributions
Sentry.metrics.distribution('api.response_time', responseTimeMs, {
  tags: { endpoint: '/api/search' },
  unit: 'millisecond',
});

// Set — track unique values
Sentry.metrics.set('users.active', userId, {
  tags: { plan: 'enterprise' },
});
```

### 5. Grafana Dashboard Integration

```typescript
// Export Sentry data to Grafana via API
// Create a Grafana data source pointing to Sentry API

// Sentry API queries for Grafana panels:
const queries = {
  // Error rate over time
  errorRate: `https://sentry.io/api/0/organizations/${org}/events-stats/?field=count()&query=is:unresolved&interval=1h`,

  // Transaction duration percentiles
  latency: `https://sentry.io/api/0/organizations/${org}/events-stats/?field=p95(transaction.duration)&interval=1h`,

  // Error count by service
  errorsByService: `https://sentry.io/api/0/organizations/${org}/events/?field=count()&groupBy=tags.service`,
};
```

### 6. PagerDuty Integration

Configure in **Settings > Integrations > PagerDuty**:

1. Connect PagerDuty account
2. Map Sentry projects to PagerDuty services
3. Create alert rules that trigger PagerDuty incidents:

```
Issue Alert: "Critical Production Error"
  Conditions: level:fatal AND environment:production
  Actions: Send PagerDuty notification to "Production On-Call"
  Frequency: Once per issue (deduplicated)

Metric Alert: "Error Spike"
  Trigger: Error count > 100 in 5 minutes
  Actions: Create PagerDuty incident (Critical severity)
  Resolution: Error count < 10 for 10 minutes
```

### 7. Slack Integration

Configure in **Settings > Integrations > Slack**:

```
# Alert routing by channel
#alerts-critical    → P0 production errors (PagerDuty + Slack)
#alerts-production  → New production issues, regressions
#alerts-staging     → Staging errors
#alerts-performance → P95 latency breaches, Web Vital regressions
```

### 8. Cross-Tool Trace Correlation

```typescript
// Embed Sentry trace ID in all outbound contexts
const traceId = Sentry.getActiveSpan()?.spanContext().traceId;

// Add to HTTP response headers
res.setHeader('X-Sentry-Trace-Id', traceId || '');

// Add to log entries
logger.info('Request processed', {
  trace_id: traceId,
  request_id: req.requestId,
  sentry_url: `https://sentry.io/organizations/${org}/performance/trace/${traceId}/`,
});

// Add to downstream API calls
fetch('https://service-b.internal/api', {
  headers: {
    'X-Trace-Id': traceId,
    // sentry-trace and baggage are auto-propagated
  },
});
```

## Output
- OpenTelemetry bridge connecting Sentry to OTel pipeline
- Structured logging correlated with Sentry events via request ID
- Custom metrics tracking business KPIs in Sentry
- PagerDuty and Slack integrations with tiered alert routing
- Cross-tool trace correlation linking logs, traces, and errors

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| OTel spans not in Sentry | SDK not using OTel bridge | SDK v8 uses OTel by default; verify version |
| Missing request IDs in logs | Middleware order wrong | Request ID middleware must run before logger and Sentry |
| PagerDuty not triggering | Alert rule conditions too narrow | Test with lower thresholds first, then tune |
| Metrics not appearing | Feature not enabled | Verify Sentry plan includes custom metrics |
| Trace IDs not matching | Different trace ID formats | Use Sentry's trace ID format (W3C standard) |

## Resources
- [Integrations](https://docs.sentry.io/organization/integrations/)
- [OpenTelemetry](https://docs.sentry.io/platforms/javascript/guides/node/tracing/instrumentation/opentelemetry/)
- [Custom Metrics](https://docs.sentry.io/product/explore/metrics/)
- [PagerDuty](https://docs.sentry.io/organization/integrations/notification-incidents/pagerduty/)
- [Slack](https://docs.sentry.io/organization/integrations/notification-incidents/slack/)
