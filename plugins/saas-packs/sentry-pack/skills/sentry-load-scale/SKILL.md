---
name: sentry-load-scale
description: |
  Scale Sentry for high-traffic applications.
  Use when optimizing for high event volumes,
  managing costs at scale, or tuning for performance.
  Trigger with phrases like "sentry high traffic", "scale sentry",
  "sentry high volume", "sentry millions events".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Load & Scale

## Overview
Optimize Sentry for high-traffic applications handling millions of events.

## High-Volume Sampling Strategies

### Adaptive Sampling
```typescript
import * as Sentry from '@sentry/node';

// Track recent error counts
const errorCounts = new Map<string, number>();
const WINDOW_MS = 60000; // 1 minute window

function getAdaptiveSampleRate(errorType: string): number {
  const count = errorCounts.get(errorType) || 0;

  // High volume = low sample rate
  if (count > 1000) return 0.001; // 0.1%
  if (count > 100) return 0.01;   // 1%
  if (count > 10) return 0.1;     // 10%
  return 1.0;                      // 100%
}

Sentry.init({
  dsn: process.env.SENTRY_DSN,

  beforeSend(event) {
    const errorType = event.exception?.values?.[0]?.type || 'unknown';

    // Update counter
    errorCounts.set(errorType, (errorCounts.get(errorType) || 0) + 1);

    // Sample based on frequency
    const sampleRate = getAdaptiveSampleRate(errorType);
    if (Math.random() > sampleRate) {
      return null; // Drop event
    }

    return event;
  },
});

// Reset counters periodically
setInterval(() => errorCounts.clear(), WINDOW_MS);
```

### Tiered Transaction Sampling
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  tracesSampler: (ctx) => {
    const name = ctx.transactionContext.name;

    // Critical paths: higher sampling
    if (name.includes('/checkout')) return 0.1;
    if (name.includes('/payment')) return 0.1;

    // High-volume endpoints: very low sampling
    if (name.includes('/api/events')) return 0.0001; // 0.01%
    if (name.includes('/health')) return 0;

    // Default: low sampling
    return 0.001; // 0.1%
  },
});
```

## Buffering and Batching

### Client-Side Buffering
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Buffer events before sending
  transport: Sentry.makeNodeTransport,
  transportOptions: {
    // Increase buffer size for high volume
    bufferSize: 1000,
  },
});
```

### Custom Batching Transport
```typescript
class BatchingTransport {
  private buffer: Sentry.Event[] = [];
  private flushInterval: NodeJS.Timer;

  constructor(private batchSize = 100, private flushMs = 5000) {
    this.flushInterval = setInterval(() => this.flush(), flushMs);
  }

  send(event: Sentry.Event) {
    this.buffer.push(event);
    if (this.buffer.length >= this.batchSize) {
      this.flush();
    }
  }

  private async flush() {
    if (this.buffer.length === 0) return;

    const batch = this.buffer.splice(0, this.batchSize);
    // Send batch to Sentry
    await this.sendBatch(batch);
  }

  private async sendBatch(events: Sentry.Event[]) {
    // Use envelope format for batch sending
    for (const event of events) {
      await Sentry.captureEvent(event);
    }
  }
}
```

## Resource Optimization

### Minimal SDK Configuration
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Reduce memory usage
  maxBreadcrumbs: 10, // Default is 100
  maxValueLength: 250, // Truncate long strings

  // Disable unused features
  autoSessionTracking: false,
  sendDefaultPii: false,

  // Minimal integrations
  integrations: (defaults) =>
    defaults.filter((i) =>
      ['Http', 'OnUncaughtException', 'OnUnhandledRejection'].includes(i.name)
    ),
});
```

### Async Event Processing
```typescript
// Don't block request handling
async function handleRequest(req: Request, res: Response) {
  try {
    const result = await processRequest(req);
    res.json(result);
  } catch (error) {
    // Capture async - don't await
    setImmediate(() => Sentry.captureException(error));

    res.status(500).json({ error: 'Internal error' });
  }
}
```

### Background Flushing
```typescript
// Flush on graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Flushing Sentry events...');
  await Sentry.close(10000); // 10 second timeout
  process.exit(0);
});

// Periodic flush for long-running processes
setInterval(() => {
  Sentry.flush(5000);
}, 60000); // Every minute
```

## Multi-Region Deployment

### Region-Based DSN Routing
```typescript
const regionDSNs: Record<string, string> = {
  'us-east': 'https://xxx@o123.ingest.us.sentry.io/456',
  'eu-west': 'https://xxx@o123.ingest.eu.sentry.io/456',
  'ap-south': 'https://xxx@o123.ingest.us.sentry.io/456',
};

const region = process.env.DEPLOY_REGION || 'us-east';

Sentry.init({
  dsn: regionDSNs[region],
  environment: process.env.NODE_ENV,

  initialScope: {
    tags: { region },
  },
});
```

### Per-Region Projects
```
Organization: mycompany
├── Project: api-us-east
├── Project: api-eu-west
└── Project: api-ap-south
```

## Quota Management at Scale

### Budget Allocation
```typescript
// 1M events/month budget
// Allocation:
// - Production errors: 500K (0.5M)
// - Production transactions: 400K
// - Staging: 100K

const quotaConfig = {
  production: {
    errorRate: 0.5, // 50% of errors
    traceRate: 0.001, // 0.1% of transactions
  },
  staging: {
    errorRate: 1.0,
    traceRate: 0.01,
  },
};

const env = process.env.NODE_ENV as keyof typeof quotaConfig;
const config = quotaConfig[env] || quotaConfig.staging;

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  sampleRate: config.errorRate,
  tracesSampleRate: config.traceRate,
});
```

### Dynamic Rate Adjustment
```typescript
// Adjust sampling based on quota usage
async function getQuotaUsage(): Promise<number> {
  const response = await fetch(
    `https://sentry.io/api/0/organizations/${ORG}/stats/v2/`,
    {
      headers: { Authorization: `Bearer ${SENTRY_TOKEN}` },
    }
  );
  const data = await response.json();
  return data.usage / data.quota; // 0-1 ratio
}

// Adjust sampling dynamically
let currentSampleRate = 1.0;

setInterval(async () => {
  const usage = await getQuotaUsage();

  if (usage > 0.9) currentSampleRate = 0.1;
  else if (usage > 0.7) currentSampleRate = 0.5;
  else currentSampleRate = 1.0;

  console.log(`Quota usage: ${usage * 100}%, sample rate: ${currentSampleRate}`);
}, 300000); // Check every 5 minutes
```

## Performance Monitoring at Scale

### Selective Transaction Sampling
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  tracesSampler: (ctx) => {
    // Always trace errors
    if (ctx.parentSampled !== undefined) {
      return ctx.parentSampled;
    }

    const requestsPerSecond = getRequestRate();

    // Scale sampling inversely with load
    if (requestsPerSecond > 10000) return 0.0001;
    if (requestsPerSecond > 1000) return 0.001;
    if (requestsPerSecond > 100) return 0.01;
    return 0.1;
  },
});
```

## Monitoring Sentry Health

### Track Event Throughput
```typescript
let eventsSent = 0;
let eventsDropped = 0;

Sentry.init({
  dsn: process.env.SENTRY_DSN,

  beforeSend(event) {
    eventsSent++;
    return event;
  },
});

// Report metrics
setInterval(() => {
  console.log(`Sentry: ${eventsSent} sent, ${eventsDropped} dropped`);
  eventsSent = 0;
  eventsDropped = 0;
}, 60000);
```

## Resources
- [Sentry Quotas](https://docs.sentry.io/product/accounts/quotas/)
- [Performance Best Practices](https://docs.sentry.io/product/performance/)
