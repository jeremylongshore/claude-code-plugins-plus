---
name: sentry-performance-tuning
description: |
  Optimize Sentry performance monitoring configuration.
  Use when tuning sample rates, reducing overhead,
  or improving performance data quality.
  Trigger with phrases like "sentry performance optimize", "tune sentry tracing",
  "sentry overhead", "improve sentry performance".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, monitoring, performance, optimization]

---
# Sentry Performance Tuning

## Prerequisites
- Performance monitoring enabled (`tracesSampleRate > 0`)
- Transaction volume metrics available in Sentry Performance dashboard
- Critical user paths identified for high-fidelity sampling
- Performance baseline established

## Instructions

### 1. Dynamic Sampling with tracesSampler

Replace static `tracesSampleRate` with intelligent sampling:

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  tracesSampler: (samplingContext) => {
    const { name, attributes, parentSampled } = samplingContext;

    // Respect parent decision for distributed traces
    if (parentSampled !== undefined) return parentSampled;

    // Health checks: never sample
    if (name?.match(/\/(health|ready|alive|ping)$/)) return 0;

    // Static assets: never sample
    if (name?.match(/\.(js|css|png|jpg|svg|woff)$/)) return 0;

    // Payment/checkout: always sample (business-critical)
    if (name?.includes('/checkout') || name?.includes('/payment')) return 1.0;

    // API endpoints: moderate sampling
    if (name?.startsWith('POST /api/')) return 0.2;
    if (name?.startsWith('GET /api/')) return 0.1;

    // Background jobs: low sampling
    if (name?.startsWith('job:') || name?.startsWith('queue:')) return 0.05;

    // Default: 5%
    return 0.05;
  },
});
```

### 2. Reduce SDK Overhead

```typescript
Sentry.init({
  // Limit breadcrumbs — each one consumes memory
  maxBreadcrumbs: 30, // Default: 100

  // Reduce max event payload size
  maxValueLength: 500,

  // Disable integrations you don't need
  integrations: (defaults) => defaults.filter(i =>
    !['Console', 'GlobalHandlers'].includes(i.name)
  ),

  // Limit attachment size
  maxAttachmentSize: 5 * 1024 * 1024, // 5 MB

  // Disable profiling if not needed
  profilesSampleRate: 0,
});
```

### 3. Parameterize Transaction Names

High-cardinality transaction names (with dynamic IDs) cause performance issues in Sentry:

```typescript
// BAD — creates thousands of unique transaction names
// GET /api/users/12345
// GET /api/users/67890

// GOOD — Sentry auto-parameterizes Express routes
// GET /api/users/:id

// For custom spans, always use parameterized names:
Sentry.startSpan(
  {
    name: 'process-order',  // NOT 'process-order-12345'
    op: 'task',
    attributes: { 'order.id': orderId }, // Put ID in attributes
  },
  async () => { /* ... */ }
);
```

### 4. Optimize Span Creation

Only create spans for meaningful operations:

```typescript
// DON'T span trivial synchronous operations
function getConfig() {
  return config[env]; // Too fast to measure
}

// DO span operations with real latency
async function processPayment(order: Order) {
  return Sentry.startSpan(
    { name: 'payment.process', op: 'http.client' },
    async () => {
      // External API call — worth measuring
      return stripe.charges.create({ amount: order.total });
    }
  );
}

// DO span database queries
async function getUserOrders(userId: string) {
  return Sentry.startSpan(
    { name: 'db.getUserOrders', op: 'db.query' },
    async () => {
      return db.query('SELECT * FROM orders WHERE user_id = $1', [userId]);
    }
  );
}
```

### 5. Custom Measurements for Business Metrics

```typescript
// Track business-relevant performance data
await Sentry.startSpan({ name: 'search.execute', op: 'function' }, async () => {
  const start = performance.now();
  const results = await searchService.query(searchTerm);
  const duration = performance.now() - start;

  // Custom measurements appear in Performance dashboard
  Sentry.setMeasurement('search.latency', duration, 'millisecond');
  Sentry.setMeasurement('search.result_count', results.length, 'none');
  Sentry.setMeasurement('search.index_size', indexStats.docCount, 'none');

  return results;
});
```

### 6. Web Vitals Optimization (Browser SDK)

```typescript
// Browser SDK automatically captures Web Vitals:
// LCP (Largest Contentful Paint)
// FID (First Input Delay) / INP (Interaction to Next Paint)
// CLS (Cumulative Layout Shift)
// TTFB (Time to First Byte)

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  integrations: [
    Sentry.browserTracingIntegration({
      // Customize which page loads to trace
      shouldCreateSpanForRequest: (url) => {
        // Only trace your own API calls, not third-party
        return url.startsWith('/api/') || url.startsWith(window.location.origin);
      },
    }),
  ],
  tracesSampleRate: 0.1,
});
```

### 7. Profile Sampling (Continuous Profiling)

```typescript
import * as Sentry from '@sentry/node';
import { nodeProfilingIntegration } from '@sentry/profiling-node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  integrations: [nodeProfilingIntegration()],
  tracesSampleRate: 0.1,

  // Profile a subset of traced transactions
  profilesSampleRate: 0.1, // 10% of transactions get profiled

  // Or use continuous profiling (v8+)
  // profileSessionSampleRate: 0.1,
});
```

### 8. Measure and Reduce SDK Init Time

```typescript
// Measure SDK initialization overhead
const initStart = performance.now();

Sentry.init({ /* config */ });

const initDuration = performance.now() - initStart;
console.log(`Sentry init: ${initDuration.toFixed(1)}ms`);

// Typical: 5-15ms for Node.js, 10-30ms for browser with replay
// If >50ms: reduce integrations, defer non-critical setup
```

## Output
- Dynamic sampling rates configured per endpoint type
- SDK overhead minimized with reduced breadcrumbs and integrations
- Transaction names parameterized to prevent cardinality explosion
- Custom measurements tracking business-critical metrics
- Profile sampling configured for hotspot detection

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Too many unique transaction names" | Dynamic IDs in names | Use parameterized names, put IDs in attributes |
| Performance tab empty | `tracesSampler` returns 0 for all routes | Add logging to sampler to debug decisions |
| SDK adding 100ms+ to requests | Too many integrations or breadcrumbs | Reduce `maxBreadcrumbs`, remove unused integrations |
| Profiling not showing data | `profilesSampleRate` is 0 | Set to 0.01-0.1 and ensure `@sentry/profiling-node` installed |
| Incomplete distributed traces | Mixed sampling decisions | Use `parentSampled` in `tracesSampler` for consistency |

## Resources
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Sampling Strategies](https://docs.sentry.io/platforms/javascript/configuration/sampling/)
- [Profiling](https://docs.sentry.io/platforms/javascript/guides/node/profiling/)
- [Web Vitals](https://docs.sentry.io/product/insights/web-vitals/)
