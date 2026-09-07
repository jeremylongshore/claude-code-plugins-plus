# Instrumentation Implementation

Full source for the metrics, tracing, and logging layers. Wire these three
modules once, then route every Klaviyo call through `instrumentedCall()` (and
optionally `tracedKlaviyoCall()`).

## Step 1: Instrumented API Wrapper

```typescript
// src/klaviyo/instrumented-client.ts
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

const registry = new Registry();

const apiRequests = new Counter({
  name: 'klaviyo_api_requests_total',
  help: 'Total Klaviyo API requests',
  labelNames: ['method', 'endpoint', 'status'],
  registers: [registry],
});

const apiDuration = new Histogram({
  name: 'klaviyo_api_duration_seconds',
  help: 'Klaviyo API request duration in seconds',
  labelNames: ['method', 'endpoint'],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

const apiErrors = new Counter({
  name: 'klaviyo_api_errors_total',
  help: 'Klaviyo API errors by status code',
  labelNames: ['endpoint', 'status_code', 'error_code'],
  registers: [registry],
});

const rateLimitRemaining = new Gauge({
  name: 'klaviyo_rate_limit_remaining',
  help: 'Remaining requests in current rate limit window',
  registers: [registry],
});

export async function instrumentedCall<T>(
  endpoint: string,
  method: string,
  operation: () => Promise<T>
): Promise<T> {
  const timer = apiDuration.startTimer({ method, endpoint });

  try {
    const result = await operation();
    apiRequests.inc({ method, endpoint, status: 'success' });

    // Extract rate limit headers if available
    const headers = (result as any)?.headers;
    if (headers?.['ratelimit-remaining']) {
      rateLimitRemaining.set(parseInt(headers['ratelimit-remaining']));
    }

    return result;
  } catch (error: any) {
    const statusCode = error.status || 'unknown';
    const errorCode = error.body?.errors?.[0]?.code || 'unknown';
    apiRequests.inc({ method, endpoint, status: 'error' });
    apiErrors.inc({ endpoint, status_code: statusCode, error_code: errorCode });
    throw error;
  } finally {
    timer();
  }
}

export { registry };
```

## Step 2: Usage in Service Layer

```typescript
// Wrap all Klaviyo calls with instrumentation
import { instrumentedCall } from '../klaviyo/instrumented-client';

// Profile creation with metrics
const profile = await instrumentedCall('profiles', 'POST', () =>
  profilesApi.createOrUpdateProfile({
    data: {
      type: 'profile' as any,
      attributes: { email: user.email, firstName: user.name },
    },
  })
);

// Event tracking with metrics
await instrumentedCall('events', 'POST', () =>
  eventsApi.createEvent({
    data: {
      type: 'event',
      attributes: {
        metric: { data: { type: 'metric', attributes: { name: 'Placed Order' } } },
        profile: { data: { type: 'profile', attributes: { email: order.email } } },
        properties: { orderId: order.id },
        value: order.total,
        time: new Date().toISOString(),
      },
    },
  })
);
```

## Step 3: OpenTelemetry Tracing

```typescript
// src/klaviyo/tracing.ts
import { trace, SpanStatusCode, Span } from '@opentelemetry/api';

const tracer = trace.getTracer('klaviyo-integration', '1.0.0');

export async function tracedKlaviyoCall<T>(
  operationName: string,
  attributes: Record<string, string>,
  operation: () => Promise<T>
): Promise<T> {
  return tracer.startActiveSpan(`klaviyo.${operationName}`, async (span: Span) => {
    span.setAttributes({
      'klaviyo.operation': operationName,
      'klaviyo.revision': '2024-10-15',
      ...attributes,
    });

    try {
      const result = await operation();
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    } catch (error: any) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
      span.setAttributes({
        'klaviyo.error.status': error.status?.toString() || 'unknown',
        'klaviyo.error.code': error.body?.errors?.[0]?.code || 'unknown',
      });
      span.recordException(error);
      throw error;
    } finally {
      span.end();
    }
  });
}
```

## Step 4: Structured Logging

```typescript
// src/klaviyo/logger.ts
import pino from 'pino';

const logger = pino({
  name: 'klaviyo',
  level: process.env.KLAVIYO_LOG_LEVEL || 'info',
  serializers: {
    // Redact sensitive data from logs
    profile: (profile: any) => ({
      id: profile.id,
      email: profile.email ? `${profile.email.substring(0, 3)}***` : undefined,
    }),
    err: pino.stdSerializers.err,
  },
});

export function logApiCall(operation: string, durationMs: number, status: 'ok' | 'error', meta?: Record<string, any>) {
  logger.info({
    msg: `klaviyo.${operation}`,
    service: 'klaviyo',
    operation,
    durationMs: Math.round(durationMs),
    status,
    ...meta,
  });
}

export function logWebhook(topic: string, eventId: string, durationMs: number) {
  logger.info({
    msg: `klaviyo.webhook.${topic}`,
    service: 'klaviyo',
    topic,
    eventId,
    durationMs: Math.round(durationMs),
  });
}

export { logger };
```

## Step 6: Metrics Endpoint

```typescript
// src/routes/metrics.ts
import { registry } from '../klaviyo/instrumented-client';

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```
