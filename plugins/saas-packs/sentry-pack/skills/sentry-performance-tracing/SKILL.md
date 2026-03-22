---
name: sentry-performance-tracing
description: |
  Set up performance monitoring and distributed tracing with Sentry.
  Use when implementing performance tracking, tracing requests,
  or monitoring application performance.
  Trigger with phrases like "sentry performance", "sentry tracing",
  "sentry APM", "monitor performance sentry".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, monitoring, performance, tracing, spans]

---
# Sentry Performance Tracing

## Prerequisites
- Sentry SDK v8 installed with `tracesSampleRate > 0`
- Performance monitoring enabled in Sentry project settings
- Understanding of spans, traces, and distributed tracing concepts

## Instructions

### 1. Enable Tracing in SDK Init

```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1, // 10% of transactions in production

  // Or use dynamic sampling for fine-grained control
  tracesSampler: (samplingContext) => {
    const { name, attributes } = samplingContext;

    // Always trace health checks for baseline
    if (name === 'GET /health') return 0;

    // Sample payment endpoints at 100%
    if (name?.includes('/api/payment')) return 1.0;

    // Sample API routes at 20%
    if (name?.startsWith('GET /api/') || name?.startsWith('POST /api/')) return 0.2;

    // Default: 5%
    return 0.05;
  },
});
```

### 2. Automatic Instrumentation (v8 Built-in)

SDK v8 auto-instruments these without configuration:
- **HTTP/HTTPS** — all outbound requests via `httpIntegration()`
- **Express** — route handlers via `expressIntegration()`
- **Fastify** — routes via `fastifyIntegration()`
- **GraphQL** — resolvers via `graphqlIntegration()`
- **MongoDB** — queries via `mongoIntegration()`
- **PostgreSQL** — queries via `postgresIntegration()` (pg driver)
- **MySQL** — queries via `mysqlIntegration()`
- **Redis** — commands via `redisIntegration()`
- **Prisma** — queries via `prismaIntegration()`
- **Knex** — queries via `knexIntegration()`

### 3. Custom Spans with startSpan

Use `Sentry.startSpan()` to measure specific operations:

```typescript
// startSpan — auto-ends when callback completes
const result = await Sentry.startSpan(
  {
    name: 'order.process',
    op: 'function',
    attributes: {
      'order.id': orderId,
      'order.items': items.length,
    },
  },
  async (span) => {
    // Nested span — automatically becomes child
    const validated = await Sentry.startSpan(
      { name: 'order.validate', op: 'function' },
      async () => {
        return validateOrder(order);
      }
    );

    // Another child span
    const charged = await Sentry.startSpan(
      { name: 'payment.charge', op: 'http.client' },
      async () => {
        return chargePayment(order.total);
      }
    );

    // Set span status based on outcome
    if (!charged.success) {
      span.setStatus({ code: 2, message: 'payment_failed' });
    }

    return { validated, charged };
  }
);
```

### 4. Manual Span Control with startSpanManual

For spans that cross callback boundaries:

```typescript
Sentry.startSpanManual(
  { name: 'queue.process', op: 'queue.task' },
  (span) => {
    queue.on('message', async (msg) => {
      try {
        await processMessage(msg);
        span.setStatus({ code: 1 }); // OK
      } catch (error) {
        span.setStatus({ code: 2, message: 'processing_failed' });
        Sentry.captureException(error);
      } finally {
        span.end(); // Must call end() manually
      }
    });
  }
);
```

### 5. Inactive Spans

For measuring operations where you do not want the span to be the active context:

```typescript
const span = Sentry.startInactiveSpan({
  name: 'background.cleanup',
  op: 'function',
});

// ... do work without this span being the "current" span ...

span.end();
```

### 6. Distributed Tracing Across Services

Sentry propagates trace context via `sentry-trace` and `baggage` headers automatically for HTTP. For custom propagation:

```typescript
// Service A: Extract headers to pass to downstream service
const traceHeaders = {
  'sentry-trace': Sentry.spanToTraceHeader(Sentry.getActiveSpan()),
  'baggage': Sentry.spanToBaggageHeader(Sentry.getActiveSpan()),
};

// Pass these headers in your HTTP request to Service B
await fetch('https://service-b.internal/api/process', {
  headers: { ...traceHeaders, 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
});

// Service B: Sentry SDK automatically reads sentry-trace/baggage
// from incoming request headers and continues the trace
```

### 7. Span Attributes and Measurements

```typescript
await Sentry.startSpan(
  { name: 'search.query', op: 'db.query' },
  async (span) => {
    const start = Date.now();
    const results = await searchIndex(query);

    // Add attributes for filtering in Sentry UI
    span.setAttribute('search.query', query);
    span.setAttribute('search.results_count', results.length);
    span.setAttribute('search.index', indexName);

    // Custom measurements appear in Performance dashboard
    Sentry.setMeasurement('search.duration_ms', Date.now() - start, 'millisecond');
    Sentry.setMeasurement('search.result_count', results.length, 'none');

    return results;
  }
);
```

### 8. Express Middleware Performance Tracking

```typescript
import express from 'express';
import * as Sentry from '@sentry/node';

const app = express();

// Sentry auto-instruments Express routes
// Add custom spans for specific middleware:
app.use('/api', async (req, res, next) => {
  await Sentry.startSpan(
    { name: 'middleware.auth', op: 'middleware' },
    async () => {
      req.user = await authenticateRequest(req);
    }
  );
  next();
});

// Parameterized route names prevent cardinality explosion
// Sentry automatically uses '/api/users/:id' not '/api/users/12345'
app.get('/api/users/:id', async (req, res) => {
  const user = await Sentry.startSpan(
    { name: 'db.getUser', op: 'db.query' },
    () => db.users.findById(req.params.id)
  );
  res.json(user);
});

Sentry.setupExpressErrorHandler(app);
```

## Reading Performance Data in Sentry

1. **Performance tab** > Overview shows p50/p75/p95 latency
2. **Trace View** shows waterfall of spans across services
3. **Span Details** shows attributes, duration, and child spans
4. **Web Vitals** (browser SDK) shows LCP, FID, CLS, TTFB, INP

## Output
- Performance data visible in Sentry Performance dashboard
- Distributed traces linked across services via trace headers
- Custom spans measuring specific operations with attributes
- Span waterfall showing bottlenecks in trace view
- Custom measurements for domain-specific metrics

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No transactions in Performance tab | `tracesSampleRate` is 0 | Set `tracesSampleRate > 0` or configure `tracesSampler` |
| Spans not nested correctly | Span created outside parent callback | Use `startSpan` inside parent `startSpan` callback |
| High cardinality warning | Dynamic values in transaction names | Use parameterized names: `/api/users/:id` not `/api/users/123` |
| Distributed trace broken | Headers not propagated | Verify `sentry-trace` and `baggage` headers forwarded between services |
| `startSpanManual` span never ends | Missing `span.end()` call | Always call `span.end()` in `finally` block |

## Resources
- [Set Up Tracing](https://docs.sentry.io/platforms/javascript/guides/node/tracing/)
- [Custom Instrumentation](https://docs.sentry.io/platforms/javascript/guides/node/tracing/instrumentation/custom-instrumentation/)
- [Distributed Tracing](https://docs.sentry.io/platforms/javascript/guides/node/tracing/distributed-tracing/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
