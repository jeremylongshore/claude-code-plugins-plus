---
name: hubspot-reliability-patterns
description: |
  Implement HubSpot reliability patterns: circuit breakers, retries, and graceful degradation.
  Use when building fault-tolerant HubSpot integrations, implementing retry strategies,
  or adding resilience to production CRM services.
  Trigger with phrases like "hubspot reliability", "hubspot circuit breaker",
  "hubspot resilience", "hubspot fallback", "hubspot fault tolerant".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Reliability Patterns

## Overview

Production-grade reliability patterns for HubSpot CRM integrations: circuit breaker, retry with Retry-After, graceful degradation, and dead letter queues.

## Prerequisites

- `@hubspot/api-client` installed (has built-in retry)
- Optional: `opossum` for circuit breaker
- Optional: Redis or database for dead letter queue

## Instructions

### Step 1: SDK Built-in Retry (First Line of Defense)

```typescript
import * as hubspot from '@hubspot/api-client';

// The SDK automatically retries 429 and 5xx errors
const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3,  // retries with exponential backoff
});
// This handles most transient failures automatically
```

### Step 2: Circuit Breaker for HubSpot API

```typescript
import CircuitBreaker from 'opossum';

// Circuit breaker wrapping all HubSpot API calls
const hubspotBreaker = new CircuitBreaker(
  async <T>(operation: () => Promise<T>): Promise<T> => operation(),
  {
    timeout: 15000,                // 15s timeout per call
    errorThresholdPercentage: 50,  // open after 50% failure rate
    resetTimeout: 30000,           // try again after 30s
    volumeThreshold: 5,            // need 5+ calls before evaluating
    rollingCountTimeout: 60000,    // 60s rolling window
  }
);

// Monitor circuit state
hubspotBreaker.on('open', () => {
  console.warn('[HubSpot] Circuit OPEN -- requests failing fast');
  // Alert team: HubSpot integration degraded
});

hubspotBreaker.on('halfOpen', () => {
  console.info('[HubSpot] Circuit HALF-OPEN -- testing recovery');
});

hubspotBreaker.on('close', () => {
  console.info('[HubSpot] Circuit CLOSED -- normal operation');
});

// Usage
async function resilientHubSpotCall<T>(operation: () => Promise<T>): Promise<T> {
  return hubspotBreaker.fire(operation) as Promise<T>;
}

// Example
const contacts = await resilientHubSpotCall(() =>
  client.crm.contacts.basicApi.getPage(10, undefined, ['email'])
);
```

### Step 3: Graceful Degradation

```typescript
// Serve cached/fallback data when HubSpot is unavailable
import { LRUCache } from 'lru-cache';

const fallbackCache = new LRUCache<string, any>({
  max: 10000,
  ttl: 30 * 60 * 1000, // 30 minutes
});

async function withFallback<T>(
  cacheKey: string,
  operation: () => Promise<T>,
  fallback?: T
): Promise<{ data: T; source: 'live' | 'cache' | 'fallback' }> {
  try {
    const data = await resilientHubSpotCall(operation);
    fallbackCache.set(cacheKey, data);
    return { data, source: 'live' };
  } catch (error) {
    // Try cache first
    const cached = fallbackCache.get(cacheKey);
    if (cached) {
      console.warn(`[HubSpot] Serving cached data for ${cacheKey}`);
      return { data: cached as T, source: 'cache' };
    }

    // Use static fallback if provided
    if (fallback !== undefined) {
      console.warn(`[HubSpot] Serving fallback for ${cacheKey}`);
      return { data: fallback, source: 'fallback' };
    }

    throw error;
  }
}

// Usage
const { data: contacts, source } = await withFallback(
  'recent-contacts',
  () => client.crm.contacts.basicApi.getPage(10, undefined, ['email', 'firstname']),
  { results: [], paging: undefined } // empty fallback
);

if (source !== 'live') {
  console.warn(`Serving ${source} data -- HubSpot may be degraded`);
}
```

### Step 4: Dead Letter Queue

```typescript
interface FailedOperation {
  id: string;
  operation: string;
  payload: any;
  error: string;
  correlationId?: string;
  attempts: number;
  firstAttempt: string;
  lastAttempt: string;
}

class HubSpotDeadLetterQueue {
  private queue: FailedOperation[] = [];

  add(operation: string, payload: any, error: any): void {
    const entry: FailedOperation = {
      id: `dlq-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      operation,
      payload,
      error: error?.body?.message || error.message,
      correlationId: error?.body?.correlationId,
      attempts: 1,
      firstAttempt: new Date().toISOString(),
      lastAttempt: new Date().toISOString(),
    };
    this.queue.push(entry);
    console.warn(`[DLQ] Enqueued ${operation}: ${entry.error}`);
  }

  async retryAll(): Promise<{ succeeded: number; failed: number }> {
    let succeeded = 0, failed = 0;

    for (const entry of [...this.queue]) {
      try {
        // Retry the operation
        await this.executeOperation(entry);
        this.queue = this.queue.filter(e => e.id !== entry.id);
        succeeded++;
      } catch (error) {
        entry.attempts++;
        entry.lastAttempt = new Date().toISOString();
        failed++;

        if (entry.attempts > 5) {
          console.error(`[DLQ] Giving up on ${entry.id} after ${entry.attempts} attempts`);
          // Move to permanent failure storage
        }
      }
    }

    return { succeeded, failed };
  }

  private async executeOperation(entry: FailedOperation): Promise<void> {
    switch (entry.operation) {
      case 'createContact':
        await client.crm.contacts.basicApi.create({
          properties: entry.payload,
          associations: [],
        });
        break;
      case 'updateContact':
        await client.crm.contacts.basicApi.update(
          entry.payload.id, { properties: entry.payload.properties }
        );
        break;
      // Add more operation types as needed
    }
  }

  getStats(): { pending: number; oldestAge: string } {
    return {
      pending: this.queue.length,
      oldestAge: this.queue.length > 0
        ? this.queue[0].firstAttempt
        : 'none',
    };
  }
}

const dlq = new HubSpotDeadLetterQueue();

// Usage
async function createContactWithDLQ(properties: Record<string, string>) {
  try {
    return await resilientHubSpotCall(() =>
      client.crm.contacts.basicApi.create({ properties, associations: [] })
    );
  } catch (error) {
    dlq.add('createContact', properties, error);
    throw error;
  }
}

// Retry DLQ periodically
setInterval(async () => {
  const stats = dlq.getStats();
  if (stats.pending > 0) {
    console.log(`[DLQ] Retrying ${stats.pending} failed operations...`);
    const result = await dlq.retryAll();
    console.log(`[DLQ] Results: ${result.succeeded} succeeded, ${result.failed} failed`);
  }
}, 5 * 60 * 1000); // every 5 minutes
```

### Step 5: Health Check with Degraded State

```typescript
type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

async function hubspotHealthCheck(): Promise<{
  status: HealthStatus;
  circuitState: string;
  dlqPending: number;
  apiLatencyMs: number;
}> {
  const dlqStats = dlq.getStats();
  const start = Date.now();

  try {
    await client.crm.contacts.basicApi.getPage(1);
    const latency = Date.now() - start;

    const status: HealthStatus =
      hubspotBreaker.stats().state === 'open' ? 'degraded' :
      dlqStats.pending > 50 ? 'degraded' :
      latency > 5000 ? 'degraded' :
      'healthy';

    return {
      status,
      circuitState: hubspotBreaker.stats().state,
      dlqPending: dlqStats.pending,
      apiLatencyMs: latency,
    };
  } catch {
    return {
      status: 'unhealthy',
      circuitState: hubspotBreaker.stats().state,
      dlqPending: dlqStats.pending,
      apiLatencyMs: Date.now() - start,
    };
  }
}
```

## Output

- SDK built-in retry handling transient 429/5xx errors
- Circuit breaker preventing cascade failures
- Graceful degradation with cached/fallback data
- Dead letter queue for failed operations with automatic retry
- Health check reporting degraded state

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit stays open | Threshold too low | Increase `errorThresholdPercentage` |
| Stale cache served | HubSpot down for long time | Alert when cache age > TTL |
| DLQ growing | Persistent failures | Investigate root cause, not symptoms |
| Fallback data confusing users | No degradation indicator | Show "data may be stale" in UI |

## Resources

- [Opossum Circuit Breaker](https://nodeshift.dev/opossum/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [lru-cache npm](https://github.com/isaacs/node-lru-cache)

## Next Steps

For policy enforcement, see `hubspot-policy-guardrails`.
