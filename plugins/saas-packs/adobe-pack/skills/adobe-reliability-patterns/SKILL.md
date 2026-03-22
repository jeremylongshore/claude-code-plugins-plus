---
name: adobe-reliability-patterns
description: |
  Implement reliability patterns for Adobe APIs: circuit breakers for IMS/Firefly,
  idempotency for PDF Services operations, graceful degradation when Adobe is down,
  and dead letter queues for failed async jobs.
  Trigger with phrases like "adobe reliability", "adobe circuit breaker",
  "adobe fallback", "adobe resilience", "adobe graceful degradation".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Reliability Patterns

## Overview

Production-grade reliability patterns for Adobe API integrations. Adobe APIs present unique challenges: IMS tokens expire after 24h, Firefly/Photoshop jobs are async with variable completion times, and rate limits vary by API. These patterns address each failure mode.

## Prerequisites

- Understanding of circuit breaker pattern
- `opossum` installed for circuit breaker (`npm install opossum`)
- Queue infrastructure (BullMQ/Redis) for dead letter queue
- Caching layer for fallback data

## Instructions

### Pattern 1: Circuit Breaker per Adobe API

Different Adobe APIs fail independently — use separate circuit breakers:

```typescript
import CircuitBreaker from 'opossum';

// IMS circuit breaker (auth failures cascade to everything)
const imsBreaker = new CircuitBreaker(
  async () => {
    const res = await fetch('https://ims-na1.adobelogin.com/ims/token/v3', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: process.env.ADOBE_CLIENT_ID!,
        client_secret: process.env.ADOBE_CLIENT_SECRET!,
        grant_type: 'client_credentials',
        scope: process.env.ADOBE_SCOPES!,
      }),
    });
    if (!res.ok) throw new Error(`IMS ${res.status}`);
    return res.json();
  },
  {
    timeout: 10_000,              // IMS should respond in 10s
    errorThresholdPercentage: 30, // Open after 30% errors
    resetTimeout: 60_000,         // Try again after 1 min
    volumeThreshold: 3,           // Minimum calls before tripping
  }
);

// Firefly circuit breaker (higher tolerance for latency)
const fireflyBreaker = new CircuitBreaker(
  async (fn: () => Promise<any>) => fn(),
  {
    timeout: 60_000,              // Firefly jobs can take up to 60s
    errorThresholdPercentage: 50,
    resetTimeout: 30_000,
    volumeThreshold: 5,
  }
);

// PDF Services circuit breaker
const pdfBreaker = new CircuitBreaker(
  async (fn: () => Promise<any>) => fn(),
  {
    timeout: 30_000,
    errorThresholdPercentage: 40,
    resetTimeout: 30_000,
    volumeThreshold: 5,
  }
);

// Monitor circuit state
for (const [name, breaker] of [['ims', imsBreaker], ['firefly', fireflyBreaker], ['pdf', pdfBreaker]] as const) {
  breaker.on('open', () => console.warn(`Circuit ${name} OPEN — failing fast`));
  breaker.on('halfOpen', () => console.info(`Circuit ${name} HALF-OPEN — testing recovery`));
  breaker.on('close', () => console.info(`Circuit ${name} CLOSED — normal`));
}
```

### Pattern 2: Graceful Degradation with Fallback

```typescript
// When Adobe is down, return cached/default data instead of failing

interface FallbackResult<T> {
  data: T;
  source: 'live' | 'cached' | 'default';
  staleness?: string;
}

async function withAdobeFallback<T>(
  liveFn: () => Promise<T>,
  cacheKey: string,
  defaultValue: T
): Promise<FallbackResult<T>> {
  // Try live API first
  try {
    const data = await liveFn();
    // Update cache for future fallback
    await cache.set(cacheKey, JSON.stringify(data), 'EX', 3600);
    return { data, source: 'live' };
  } catch (error: any) {
    console.warn(`Adobe API failed (${error.message}), trying fallback`);
  }

  // Try cached data
  const cached = await cache.get(cacheKey);
  if (cached) {
    const ttl = await cache.ttl(cacheKey);
    return {
      data: JSON.parse(cached),
      source: 'cached',
      staleness: `${3600 - ttl}s old`,
    };
  }

  // Last resort: return default
  return { data: defaultValue, source: 'default' };
}

// Usage: image generation with fallback to placeholder
const result = await withAdobeFallback(
  () => generateImage({ prompt: 'product hero image' }),
  'hero-image-cache',
  { outputs: [{ image: { url: '/images/placeholder-hero.jpg' } }] }
);

if (result.source !== 'live') {
  console.warn(`Serving ${result.source} data for hero image`);
}
```

### Pattern 3: Dead Letter Queue for Failed Jobs

```typescript
import { Queue, Worker } from 'bullmq';
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

// DLQ for failed Adobe operations
const adobeDlq = new Queue('adobe-dlq', { connection: redis });

// Main processing queue
const adobeQueue = new Queue('adobe-jobs', { connection: redis });

const worker = new Worker('adobe-jobs', async (job) => {
  try {
    switch (job.data.operation) {
      case 'firefly-generate':
        return await generateImage(job.data.params);
      case 'pdf-extract':
        return await extractPdfContent(job.data.params.pdfPath);
      case 'photoshop-cutout':
        return await removeBackground(job.data.params);
      default:
        throw new Error(`Unknown operation: ${job.data.operation}`);
    }
  } catch (error: any) {
    // Route to DLQ after max retries
    if (job.attemptsMade >= 3) {
      await adobeDlq.add('failed-job', {
        originalJob: job.data,
        error: error.message,
        attempts: job.attemptsMade,
        failedAt: new Date().toISOString(),
      });
      console.error(`Job ${job.id} moved to DLQ after ${job.attemptsMade} attempts`);
      return; // Don't rethrow — job is handled
    }
    throw error; // Retry
  }
}, {
  connection: redis,
  concurrency: 5,
  limiter: {
    max: 10,
    duration: 60_000, // Max 10 jobs per minute (respect Adobe rate limits)
  },
});
```

### Pattern 4: Timeout Hierarchy for Adobe APIs

```typescript
// Adobe APIs have very different latency profiles
const ADOBE_TIMEOUTS = {
  ims_token: 10_000,       // IMS should be fast
  firefly_sync: 30_000,    // Sync image generation
  firefly_async: 5_000,    // Async job submission (fast, just queues)
  firefly_poll: 120_000,   // Total polling timeout
  pdf_extract: 30_000,     // PDF extraction
  pdf_create: 20_000,      // PDF creation
  photoshop_submit: 5_000, // Job submission
  photoshop_poll: 120_000, // Total polling timeout
};

async function timedAdobeCall<T>(
  operation: keyof typeof ADOBE_TIMEOUTS,
  fn: () => Promise<T>
): Promise<T> {
  const timeout = ADOBE_TIMEOUTS[operation];
  return Promise.race([
    fn(),
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`Adobe ${operation} timeout (${timeout}ms)`)), timeout)
    ),
  ]);
}
```

### Pattern 5: Health Check with Degraded State

```typescript
type ServiceHealth = 'healthy' | 'degraded' | 'unhealthy';

async function adobeHealthCheck(): Promise<{
  status: ServiceHealth;
  services: Record<string, any>;
}> {
  const checks = {
    ims: {
      status: imsBreaker.stats().state === 'closed' ? 'healthy' : 'unhealthy',
      circuitState: imsBreaker.stats().state,
    },
    firefly: {
      status: fireflyBreaker.stats().state === 'closed' ? 'healthy' :
              fireflyBreaker.stats().state === 'halfOpen' ? 'degraded' : 'unhealthy',
      circuitState: fireflyBreaker.stats().state,
    },
    pdf: {
      status: pdfBreaker.stats().state === 'closed' ? 'healthy' : 'degraded',
      circuitState: pdfBreaker.stats().state,
    },
    dlq: {
      size: await adobeDlq.count(),
      status: (await adobeDlq.count()) > 100 ? 'degraded' : 'healthy',
    },
  };

  const overall: ServiceHealth =
    checks.ims.status === 'unhealthy' ? 'unhealthy' :
    Object.values(checks).some(c => c.status === 'degraded') ? 'degraded' :
    'healthy';

  return { status: overall, services: checks };
}
```

## Output

- Per-API circuit breakers (IMS, Firefly, PDF Services)
- Graceful degradation with cached/default fallback
- Dead letter queue for failed async jobs
- Timeout hierarchy matching Adobe API latency profiles
- Health check with degraded state detection

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| IMS circuit stays open | Credentials rotated | Update secret and restart |
| Firefly circuit flapping | Intermittent 500s | Increase `resetTimeout` |
| DLQ growing | Persistent failures | Investigate root cause; process DLQ |
| Fallback data too stale | Long outage | Increase cache TTL; notify users |

## Resources

- [Opossum Circuit Breaker](https://nodeshift.dev/opossum/)
- [BullMQ Documentation](https://docs.bullmq.io/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Adobe Status Page](https://status.adobe.com)

## Next Steps

For policy enforcement, see `adobe-policy-guardrails`.
