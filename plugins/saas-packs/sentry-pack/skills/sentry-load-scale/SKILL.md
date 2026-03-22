---
name: sentry-load-scale
description: |
  Scale Sentry for high-traffic applications.
  Use when optimizing for high event volumes,
  managing costs at scale, or tuning for performance.
  Trigger with phrases like "sentry high traffic", "scale sentry",
  "sentry high volume", "sentry millions events".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, performance, scaling, high-traffic]

---
# Sentry Load & Scale

## Prerequisites
- High-traffic application metrics available (requests/sec, error rate)
- Sentry quota and billing understood
- Performance baseline established
- Event volume estimates calculated per category

## Instructions

### 1. Adaptive Error Sampling

For applications with millions of requests/day, static sampling wastes quota on duplicates:

```typescript
// Adaptive sampling: reduce rate for high-frequency errors
const errorCounts = new Map<string, number>();
const WINDOW_MS = 60_000; // 1 minute window

setInterval(() => errorCounts.clear(), WINDOW_MS);

Sentry.init({
  dsn: process.env.SENTRY_DSN,

  beforeSend(event, hint) {
    const error = hint?.originalException;
    const key = error instanceof Error
      ? `${error.name}:${error.message?.substring(0, 100)}`
      : 'unknown';

    const count = (errorCounts.get(key) || 0) + 1;
    errorCounts.set(key, count);

    // First occurrence: always send
    if (count === 1) return event;

    // 2-10 occurrences: send every 5th
    if (count <= 10) return count % 5 === 0 ? event : null;

    // 11-100: send every 25th
    if (count <= 100) return count % 25 === 0 ? event : null;

    // 100+: send every 100th (0.01% of duplicates)
    return count % 100 === 0 ? event : null;
  },
});
```

### 2. Tiered Transaction Sampling

```typescript
Sentry.init({
  tracesSampler: (samplingContext) => {
    const { name, parentSampled } = samplingContext;

    // Respect parent decision for distributed tracing consistency
    if (parentSampled !== undefined) return parentSampled;

    // Tier 0: Never sample (high-frequency, zero diagnostic value)
    if (name?.match(/\/(health|ready|alive|ping|metrics|favicon)/)) return 0;
    if (name?.match(/\.(css|js|png|jpg|svg|woff2?|ico)$/)) return 0;

    // Tier 1: Always sample (business-critical, low volume)
    if (name?.includes('/payment') || name?.includes('/checkout')) return 1.0;
    if (name?.includes('/auth/login')) return 0.5;

    // Tier 2: Moderate sampling (API endpoints)
    if (name?.startsWith('POST /api/')) return 0.05; // 5%
    if (name?.startsWith('GET /api/')) return 0.02;  // 2%

    // Tier 3: Minimal sampling (everything else)
    return 0.005; // 0.5%
  },
});
```

### 3. Minimize SDK Overhead

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Reduce memory: fewer breadcrumbs
  maxBreadcrumbs: 15, // Down from 100 default

  // Reduce payload size
  maxValueLength: 200,

  // Disable integrations that add overhead
  integrations: (defaults) => defaults.filter(i =>
    !['Console', 'ContextLines'].includes(i.name)
  ),

  // No profiling at high scale
  profilesSampleRate: 0,

  // Limit context size
  beforeSend(event) {
    // Truncate large contexts
    if (event.contexts) {
      for (const [key, ctx] of Object.entries(event.contexts)) {
        const str = JSON.stringify(ctx);
        if (str.length > 2000) {
          event.contexts[key] = { _truncated: true, size: str.length };
        }
      }
    }
    return event;
  },
});
```

### 4. Graceful Shutdown and Flush

At high scale, ensure events are sent before process exit:

```typescript
import * as Sentry from '@sentry/node';

// Handle graceful shutdown
async function shutdown(signal: string) {
  console.log(`${signal} received — flushing Sentry events`);

  // Stop accepting new requests
  server.close();

  // Flush all pending Sentry events (2 second timeout)
  const flushed = await Sentry.close(2000);
  if (!flushed) {
    console.warn('Sentry flush timed out — some events may be lost');
  }

  process.exit(0);
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
```

### 5. Multi-Region and Load Balancer Considerations

```typescript
// Set server name for identifying which instance generated events
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  serverName: process.env.HOSTNAME || process.env.POD_NAME || os.hostname(),

  initialScope: {
    tags: {
      region: process.env.AWS_REGION || 'unknown',
      cluster: process.env.K8S_CLUSTER || 'default',
      pod: process.env.POD_NAME || 'unknown',
      instance_id: process.env.INSTANCE_ID || 'unknown',
    },
  },
});

// In Sentry dashboard, filter by:
// tags.region:us-east-1
// tags.cluster:production
// server_name:pod-abc-xyz
```

### 6. Background Worker Patterns

```typescript
// For queue workers processing millions of jobs/day:
import * as Sentry from '@sentry/node';

async function processJob(job: Job) {
  return Sentry.withScope(async (scope) => {
    scope.setTag('job.type', job.type);
    scope.setTag('job.queue', job.queue);
    scope.setContext('job', {
      id: job.id,
      attempts: job.attempts,
      created: job.createdAt,
    });

    try {
      // Only trace a sample of jobs
      if (Math.random() < 0.01) { // 1% of jobs
        return Sentry.startSpan(
          { name: `job.${job.type}`, op: 'queue.task' },
          () => executeJob(job)
        );
      }
      return executeJob(job);
    } catch (error) {
      Sentry.captureException(error);
      throw error; // Re-throw for retry logic
    }
  });
}

// Periodic flush for long-running workers
setInterval(async () => {
  await Sentry.flush(2000);
}, 30_000); // Every 30 seconds
```

### 7. Rate Limit Handling

```typescript
// Monitor SDK rate limit status
Sentry.init({
  beforeSend(event) {
    // The SDK automatically handles 429 responses
    // No manual retry logic needed
    return event;
  },

  // Set transport options for high-volume
  transportOptions: {
    // Buffer size for pending events
    bufferSize: 100, // Default: 64
  },
});
```

### 8. Cost Estimation at Scale

```
Application: 10M requests/day, 0.1% error rate

Error events:
  10M * 0.001 = 10,000 errors/day
  With sampleRate 0.5 = 5,000 errors/day = 150K/month

Transaction events:
  10M requests/day
  With tracesSampleRate 0.005 = 50,000 txns/day = 1.5M/month

Sentry Team plan: 50K errors + 100K transactions included
  Error overage: 100K * $0.00029 = $29/month
  Transaction overage: 1.4M * $0.000025 = $35/month

  Total: $26 (base) + $29 + $35 = ~$90/month for 10M requests/day
```

## Output
- Adaptive sampling reducing duplicate error volume by 90%+
- Tiered transaction sampling with endpoint-specific rates
- SDK overhead minimized for high-throughput environments
- Graceful shutdown ensuring event delivery
- Multi-region tagging for infrastructure visibility
- Cost estimation model for budget planning

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Events silently dropped | SDK buffer full at high volume | Increase `bufferSize`, reduce event rate |
| 429 rate limit responses | Quota exhausted | Reduce sample rates, enable spike protection |
| Memory growing over time | Breadcrumbs not cleared | Reduce `maxBreadcrumbs`, check for scope leaks |
| Lost events on shutdown | No `Sentry.close()` call | Add shutdown handler with `Sentry.close(timeout)` |
| Inconsistent distributed traces | Mixed sampling decisions | Use `parentSampled` in `tracesSampler` |

## Resources
- [Quota Management](https://docs.sentry.io/pricing/quotas/)
- [Sampling](https://docs.sentry.io/platforms/javascript/configuration/sampling/)
- [Transport Options](https://docs.sentry.io/platforms/javascript/configuration/transports/)
- [Pricing Calculator](https://sentry.io/pricing/)
