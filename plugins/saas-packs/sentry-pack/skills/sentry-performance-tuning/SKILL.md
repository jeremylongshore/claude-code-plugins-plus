---
name: sentry-performance-tuning
description: |
  Optimize Sentry performance monitoring configuration.
  Use when tuning sample rates, reducing overhead,
  or improving performance data quality.
  Trigger with phrases like "sentry performance optimize", "tune sentry tracing",
  "sentry overhead", "improve sentry performance".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Performance Tuning

## Overview
Optimize Sentry performance monitoring for production workloads.

## Sample Rate Optimization

### Dynamic Sampling
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  tracesSampler: (samplingContext) => {
    const { transactionContext, parentSampled } = samplingContext;
    const name = transactionContext.name;

    // Always trace if parent was sampled (distributed tracing)
    if (parentSampled !== undefined) return parentSampled;

    // Skip health checks entirely
    if (name.includes('/health') || name.includes('/ready')) {
      return 0;
    }

    // Lower rate for high-volume endpoints
    if (name.includes('/api/events')) return 0.01;

    // Higher rate for critical paths
    if (name.includes('/checkout') || name.includes('/payment')) {
      return 0.5;
    }

    // Default rate
    return 0.1;
  },
});
```

### Environment-Based Rates
```typescript
const sampleRates: Record<string, number> = {
  development: 1.0,
  staging: 0.5,
  production: 0.1,
};

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: sampleRates[process.env.NODE_ENV] || 0.1,
});
```

## Reduce SDK Overhead

### Minimal Integrations
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Only include needed integrations
  integrations: [
    new Sentry.Integrations.Http({ tracing: true }),
    // Remove unused integrations to reduce overhead
  ],

  // Disable automatic breadcrumbs if not needed
  integrations: (integrations) =>
    integrations.filter((i) => i.name !== 'Console'),
});
```

### Limit Breadcrumbs
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  maxBreadcrumbs: 20, // Default is 100
});
```

### Batch Events
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Buffer events before sending
  transport: Sentry.makeNodeTransport,
  transportOptions: {
    // Batch events (reduces network calls)
  },
});
```

## Transaction Optimization

### Meaningful Transaction Names
```typescript
// Bad: Creates too many unique transactions
app.get('/users/:id', (req, res) => {
  // Transaction name: /users/123, /users/456, etc.
});

// Good: Parameterized names
app.get('/users/:id', (req, res) => {
  const transaction = Sentry.getCurrentHub().getScope()?.getTransaction();
  if (transaction) {
    transaction.setName('/users/:id'); // Single transaction type
  }
});
```

### Skip Unnecessary Spans
```typescript
// Only create spans for meaningful operations
function processData(data: Data[]) {
  // Skip span for fast operations
  if (data.length < 10) {
    return quickProcess(data);
  }

  // Create span for slow operations
  const span = Sentry.getCurrentHub().getScope()?.getSpan()?.startChild({
    op: 'process',
    description: 'Process large dataset',
  });

  try {
    return slowProcess(data);
  } finally {
    span?.finish();
  }
}
```

## Profile Sampling

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Profiling is expensive - use sparingly
  profilesSampleRate: 0.01, // 1% of transactions

  // Or conditional profiling
  profilesSampler: (ctx) => {
    if (ctx.transactionContext.name.includes('slow-endpoint')) {
      return 0.1; // Profile 10% of slow endpoints
    }
    return 0; // Don't profile others
  },
});
```

## Metrics and Monitoring

### Track SDK Performance
```typescript
// Log SDK timing
const start = Date.now();
Sentry.init({ dsn: process.env.SENTRY_DSN });
console.log(`Sentry init: ${Date.now() - start}ms`);

// Monitor event queue
const client = Sentry.getCurrentHub().getClient();
console.log('Pending events:', client?.getTransport?.()?.flush?.(0));
```

### Production Baseline
```typescript
// Establish baseline without Sentry
const withoutSentry = await benchmark(handler);

// Compare with Sentry
Sentry.init({ dsn, tracesSampleRate: 0.1 });
const withSentry = await benchmark(handler);

console.log(`Overhead: ${withSentry - withoutSentry}ms`);
```

## High-Volume Optimization

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Aggressive sampling for high volume
  tracesSampleRate: 0.01, // 1%

  // Drop noisy errors
  beforeSend(event) {
    if (event.exception?.values?.[0]?.type === 'TimeoutError') {
      return null;
    }
    return event;
  },

  // Limit event size
  maxValueLength: 250,
  maxBreadcrumbs: 20,
});
```

## Resources
- [Sentry Performance](https://docs.sentry.io/product/performance/)
- [Sampling Strategies](https://docs.sentry.io/platforms/javascript/configuration/sampling/)
