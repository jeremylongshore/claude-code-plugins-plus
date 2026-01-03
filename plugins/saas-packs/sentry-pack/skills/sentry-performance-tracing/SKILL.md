---
name: sentry-performance-tracing
description: |
  Set up performance monitoring and distributed tracing with Sentry.
  Use when implementing performance tracking, tracing requests,
  or monitoring application performance.
  Trigger with phrases like "sentry performance", "sentry tracing",
  "sentry APM", "monitor performance sentry".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Performance Tracing

## Overview
Set up performance monitoring and distributed tracing to track application performance.

## Prerequisites
- Sentry SDK installed
- Performance plan enabled in Sentry
- Understanding of tracing concepts

## Instructions

### Step 1: Enable Performance Monitoring
```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Enable performance monitoring
  tracesSampleRate: 1.0, // 100% in dev, lower in prod

  // Or use sampling function
  tracesSampler: (samplingContext) => {
    if (samplingContext.transactionContext.name.includes('health')) {
      return 0; // Don't trace health checks
    }
    return 0.1; // 10% sample rate
  },

  // Enable profiling (optional)
  profilesSampleRate: 0.1,
});
```

### Step 2: Create Transactions
```typescript
// Automatic transactions for HTTP (enabled by default)
// Manual transactions for custom operations

const transaction = Sentry.startTransaction({
  name: 'processOrder',
  op: 'task',
  data: { orderId: order.id },
});

try {
  await processOrder(order);
} finally {
  transaction.finish();
}
```

### Step 3: Add Spans
```typescript
const transaction = Sentry.getCurrentHub().getScope()?.getTransaction();

if (transaction) {
  const span = transaction.startChild({
    op: 'db.query',
    description: 'SELECT * FROM users',
  });

  try {
    const result = await db.query('SELECT * FROM users');
    span.setData('row_count', result.length);
  } finally {
    span.finish();
  }
}
```

### Step 4: Distributed Tracing
```typescript
// Client side - include trace headers
const transaction = Sentry.getCurrentHub().getScope()?.getTransaction();
const traceHeaders = transaction?.toTraceparent();

fetch('/api/endpoint', {
  headers: {
    'sentry-trace': traceHeaders,
    'baggage': Sentry.getBaggage(),
  },
});

// Server side - continue trace
const transaction = Sentry.continueTrace(
  { sentryTrace: req.headers['sentry-trace'], baggage: req.headers['baggage'] },
  (ctx) => Sentry.startTransaction({ ...ctx, name: 'api.endpoint', op: 'http.server' })
);
```

## Output
- Performance data visible in Sentry Performance dashboard
- Distributed traces across services
- Span breakdowns for bottleneck identification

## Best Practices

### Sample Rate Guidelines
```typescript
const environment = process.env.NODE_ENV;

const sampleRates = {
  development: 1.0,   // 100% - capture everything
  staging: 0.5,       // 50% - good balance
  production: 0.1,    // 10% - cost efficient
};

Sentry.init({
  tracesSampleRate: sampleRates[environment] || 0.1,
});
```

### Custom Instrumentation
```typescript
// Wrap database operations
function instrumentedQuery<T>(sql: string, fn: () => Promise<T>): Promise<T> {
  const span = Sentry.getCurrentHub().getScope()?.getSpan();
  const child = span?.startChild({
    op: 'db.query',
    description: sql.substring(0, 100),
  });

  return fn()
    .then((result) => {
      child?.setStatus('ok');
      return result;
    })
    .catch((error) => {
      child?.setStatus('internal_error');
      throw error;
    })
    .finally(() => child?.finish());
}
```

## Examples

### Express Middleware
```typescript
import * as Sentry from '@sentry/node';
import express from 'express';

const app = express();

// Sentry request handler (creates transaction)
app.use(Sentry.Handlers.requestHandler());
app.use(Sentry.Handlers.tracingHandler());

app.get('/api/users', async (req, res) => {
  const span = Sentry.getCurrentHub().getScope()?.getTransaction()?.startChild({
    op: 'db.query',
    description: 'fetch_users',
  });

  const users = await db.users.findMany();
  span?.finish();

  res.json(users);
});
```

### Python with FastAPI
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
)

@app.get('/api/users')
async def get_users():
    with sentry_sdk.start_span(op='db.query', description='fetch_users'):
        users = await db.fetch_all('SELECT * FROM users')
    return users
```

## Resources
- [Sentry Performance](https://docs.sentry.io/product/performance/)
- [Distributed Tracing](https://docs.sentry.io/product/performance/distributed-tracing/)

## Next Steps
Proceed to `sentry-common-errors` for troubleshooting common issues.
