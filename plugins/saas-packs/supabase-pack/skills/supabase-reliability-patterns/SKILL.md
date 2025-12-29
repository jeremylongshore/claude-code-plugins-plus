---
name: supabase-reliability-patterns
description: |
  Supabase idempotency, circuit breakers, and reliability patterns.
  Use when implementing production reliability for Supabase integration.
  Trigger with phrases like "supabase reliability", "supabase circuit breaker",
  "supabase idempotent", "supabase resilience".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Reliability Patterns

## Overview
Production-grade reliability patterns for Supabase integrations.

## Prerequisites
- supabase-install-auth completed
- opossum or similar circuit breaker library
- Redis for distributed state (optional)
- Queue system for DLQ

## Instructions

### Step 1: Circuit Breaker

Implement a circuit breaker to prevent cascading failures when Supabase experiences issues. The circuit breaker will automatically stop sending requests when the error rate exceeds a threshold, allowing the service time to recover.

```typescript
import CircuitBreaker from 'opossum';

const supabaseBreaker = new CircuitBreaker(
  async (operation: () => Promise<any>) => operation(),
  {
    timeout: 30000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000,
    volumeThreshold: 10,
  }
);

// Events
supabaseBreaker.on('open', () => {
  console.warn('Supabase circuit OPEN - requests failing fast');
  alertOps('Supabase circuit breaker opened');
});

supabaseBreaker.on('halfOpen', () => {
  console.info('Supabase circuit HALF-OPEN - testing recovery');
});

supabaseBreaker.on('close', () => {
  console.info('Supabase circuit CLOSED - normal operation');
});

// Usage
async function safeSupabaseCall<T>(fn: () => Promise<T>): Promise<T> {
  return supabaseBreaker.fire(fn);
}
```

## Idempotency Keys

```typescript
import { v4 as uuidv4 } from 'uuid';
import crypto from 'crypto';

// Generate deterministic idempotency key from input
function generateIdempotencyKey(
  operation: string,
  params: Record<string, any>
): string {
  const data = JSON.stringify({ operation, params });
  return crypto.createHash('sha256').update(data).digest('hex');
}

// Or use random key with storage
class IdempotencyManager {
  private store: Map<string, { key: string; expiresAt: Date }> = new Map();

  getOrCreate(operationId: string): string {
    const existing = this.store.get(operationId);
    if (existing && existing.expiresAt > new Date()) {
      return existing.key;
    }

    const key = uuidv4();
    this.store.set(operationId, {
      key,
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
    });
    return key;
  }
}
```

## Bulkhead Pattern

```typescript
import PQueue from 'p-queue';

// Separate queues for different operations
const supabaseQueues = {
  critical: new PQueue({ concurrency: 10 }),
  normal: new PQueue({ concurrency: 5 }),
  bulk: new PQueue({ concurrency: 2 }),
};

async function prioritizedSupabaseCall<T>(
  priority: 'critical' | 'normal' | 'bulk',
  fn: () => Promise<T>
): Promise<T> {
  return supabaseQueues[priority].add(fn);
}

// Usage
await prioritizedSupabaseCall('critical', () =>
  supabaseClient.processPayment(order)
);

await prioritizedSupabaseCall('bulk', () =>
  supabaseClient.syncCatalog(products)
);
```

## Timeout Hierarchy

```typescript
const TIMEOUT_CONFIG = {
  connect: 5000,      // Initial connection
  request: 30000,     // Standard requests
  upload: 120000,     // File uploads
  longPoll: 300000,   // Webhook long-polling
};

async function timedoutSupabaseCall<T>(
  operation: 'connect' | 'request' | 'upload' | 'longPoll',
  fn: () => Promise<T>
): Promise<T> {
  const timeout = TIMEOUT_CONFIG[operation];

  return Promise.race([
    fn(),
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`Supabase ${operation} timeout`)), timeout)
    ),
  ]);
}
```

## Graceful Degradation

```typescript
interface SupabaseFallback {
  enabled: boolean;
  data: any;
  staleness: 'fresh' | 'stale' | 'very_stale';
}

async function withSupabaseFallback<T>(
  fn: () => Promise<T>,
  fallbackFn: () => Promise<T>
): Promise<{ data: T; fallback: boolean }> {
  try {
    const data = await fn();
    // Update cache for future fallback
    await updateFallbackCache(data);
    return { data, fallback: false };
  } catch (error) {
    console.warn('Supabase failed, using fallback:', error.message);
    const data = await fallbackFn();
    return { data, fallback: true };
  }
}
```

## Dead Letter Queue

```typescript
interface DeadLetterEntry {
  id: string;
  operation: string;
  payload: any;
  error: string;
  attempts: number;
  lastAttempt: Date;
}

class SupabaseDeadLetterQueue {
  private queue: DeadLetterEntry[] = [];

  add(entry: Omit<DeadLetterEntry, 'id' | 'lastAttempt'>): void {
    this.queue.push({
      ...entry,
      id: uuidv4(),
      lastAttempt: new Date(),
    });
  }

  async processOne(): Promise<boolean> {
    const entry = this.queue.shift();
    if (!entry) return false;

    try {
      await supabaseClient[entry.operation](entry.payload);
      console.log(`DLQ: Successfully reprocessed ${entry.id}`);
      return true;
    } catch (error) {
      entry.attempts++;
      entry.lastAttempt = new Date();

      if (entry.attempts < 5) {
        this.queue.push(entry);
      } else {
        console.error(`DLQ: Giving up on ${entry.id} after 5 attempts`);
        await alertOnPermanentFailure(entry);
      }
      return false;
    }
  }
}
```

### Step 2: Health Check with Degraded State

```typescript
type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

async function supabaseHealthCheck(): Promise<{
  status: HealthStatus;
  details: Record<string, any>;
}> {
  const checks = {
    api: await checkApiConnectivity(),
    circuitBreaker: supabaseBreaker.stats(),
    dlqSize: deadLetterQueue.size(),
  };

  const status: HealthStatus =
    !checks.api.connected ? 'unhealthy' :
    checks.circuitBreaker.state === 'open' ? 'degraded' :
    checks.dlqSize > 100 ? 'degraded' :
    'healthy';

  return { status, details: checks };
}
```

## Output
- Circuit breaker protecting against cascading failures
- Idempotency keys preventing duplicate operations
- Bulkhead pattern isolating different workloads
- Graceful degradation when Supabase is unavailable

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Circuit open | Too many failures | Wait for reset, check Supabase status |
| Idempotency collision | Reused key | Generate unique keys per operation |
| Queue backlog | Slow processing | Scale consumers, check DLQ |
| Fallback failed | Both primary and fallback down | Alert, enable maintenance mode |

## Examples

### Retry with Jitter

```typescript
async function retryWithJitter<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      const baseDelay = Math.pow(2, i) * 1000;
      const jitter = Math.random() * 1000;
      await sleep(baseDelay + jitter);
    }
  }
  throw new Error('Unreachable');
}
```

## Resources
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Supabase Reliability Guide](https://supabase.com/docs/reliability)
- [Bulkhead Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/bulkhead)

## Next Steps
For policy enforcement, see `supabase-policy-guardrails`.