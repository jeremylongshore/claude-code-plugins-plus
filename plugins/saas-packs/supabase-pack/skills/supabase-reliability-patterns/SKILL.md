---
name: supabase-reliability-patterns
description: |
  Implement Supabase reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Supabase integrations, implementing retry strategies,
  or adding resilience to production Supabase services.
  Trigger with phrases like "supabase reliability", "supabase circuit breaker",
  "supabase idempotent", "supabase resilience", "supabase fallback", "supabase bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Reliability Patterns

## Overview
Production-grade reliability patterns for Supabase integrations.

## Prerequisites
- Understanding of circuit breaker pattern
- opossum or similar library installed
- Queue infrastructure for DLQ
- Caching layer for fallbacks

## Circuit Breaker

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

## Health Check with Degraded State

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

## Instructions

### Step 1: Implement Circuit Breaker
Wrap Supabase calls with circuit breaker.

### Step 2: Add Idempotency Keys
Generate deterministic keys for operations.

### Step 3: Configure Bulkheads
Separate queues for different priorities.

### Step 4: Set Up Dead Letter Queue
Handle permanent failures gracefully.

## Output
- Circuit breaker protecting Supabase calls
- Idempotency preventing duplicates
- Bulkhead isolation implemented
- DLQ for failed operations

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit stays open | Threshold too low | Adjust error percentage |
| Duplicate operations | Missing idempotency | Add idempotency key |
| Queue full | Rate too high | Increase concurrency |
| DLQ growing | Persistent failures | Investigate root cause |

## Examples

### Quick Circuit Check
```typescript
const state = supabaseBreaker.stats().state;
console.log('Supabase circuit:', state);
```

## Resources
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Opossum Documentation](https://nodeshift.dev/opossum/)
- [Supabase Reliability Guide](https://supabase.com/docs/reliability)

## Next Steps
For policy enforcement, see `supabase-policy-guardrails`.