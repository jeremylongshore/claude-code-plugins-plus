---
name: databricks-reliability-patterns
description: |
  Implement Databricks reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Databricks integrations, implementing retry strategies,
  or adding resilience to production Databricks services.
  Trigger with phrases like "databricks reliability", "databricks circuit breaker",
  "databricks idempotent", "databricks resilience", "databricks fallback", "databricks bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, databricks]
---

# Databricks Reliability Patterns

## Overview
Production-grade reliability patterns for Databricks integrations.

## Prerequisites
- Understanding of circuit breaker pattern
- opossum or similar library installed
- Queue infrastructure for DLQ
- Caching layer for fallbacks

## Circuit Breaker

```typescript
import CircuitBreaker from 'opossum';

const databricksBreaker = new CircuitBreaker(
  async (operation: () => Promise<any>) => operation(),
  {
    timeout: 30000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000,
    volumeThreshold: 10,
  }
);

// Events
databricksBreaker.on('open', () => {
  console.warn('Databricks circuit OPEN - requests failing fast');
  alertOps('Databricks circuit breaker opened');
});

databricksBreaker.on('halfOpen', () => {
  console.info('Databricks circuit HALF-OPEN - testing recovery');
});

databricksBreaker.on('close', () => {
  console.info('Databricks circuit CLOSED - normal operation');
});

// Usage
async function safeDatabricksCall<T>(fn: () => Promise<T>): Promise<T> {
  return databricksBreaker.fire(fn);
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
const databricksQueues = {
  critical: new PQueue({ concurrency: 10 }),
  normal: new PQueue({ concurrency: 5 }),
  bulk: new PQueue({ concurrency: 2 }),
};

async function prioritizedDatabricksCall<T>(
  priority: 'critical' | 'normal' | 'bulk',
  fn: () => Promise<T>
): Promise<T> {
  return databricksQueues[priority].add(fn);
}

// Usage
await prioritizedDatabricksCall('critical', () =>
  databricksClient.processPayment(order)
);

await prioritizedDatabricksCall('bulk', () =>
  databricksClient.syncCatalog(products)
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

async function timedoutDatabricksCall<T>(
  operation: 'connect' | 'request' | 'upload' | 'longPoll',
  fn: () => Promise<T>
): Promise<T> {
  const timeout = TIMEOUT_CONFIG[operation];

  return Promise.race([
    fn(),
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`Databricks ${operation} timeout`)), timeout)
    ),
  ]);
}
```

## Graceful Degradation

```typescript
interface DatabricksFallback {
  enabled: boolean;
  data: any;
  staleness: 'fresh' | 'stale' | 'very_stale';
}

async function withDatabricksFallback<T>(
  fn: () => Promise<T>,
  fallbackFn: () => Promise<T>
): Promise<{ data: T; fallback: boolean }> {
  try {
    const data = await fn();
    // Update cache for future fallback
    await updateFallbackCache(data);
    return { data, fallback: false };
  } catch (error) {
    console.warn('Databricks failed, using fallback:', error.message);
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

class DatabricksDeadLetterQueue {
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
      await databricksClient[entry.operation](entry.payload);
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

async function databricksHealthCheck(): Promise<{
  status: HealthStatus;
  details: Record<string, any>;
}> {
  const checks = {
    api: await checkApiConnectivity(),
    circuitBreaker: databricksBreaker.stats(),
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
Wrap Databricks calls with circuit breaker.

### Step 2: Add Idempotency Keys
Generate deterministic keys for operations.

### Step 3: Configure Bulkheads
Separate queues for different priorities.

### Step 4: Set Up Dead Letter Queue
Handle permanent failures gracefully.

## Output
- Circuit breaker protecting Databricks calls
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
const state = databricksBreaker.stats().state;
console.log('Databricks circuit:', state);
```

## Resources
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Opossum Documentation](https://nodeshift.dev/opossum/)
- [Databricks Reliability Guide](https://docs.databricks.com/reliability)

## Next Steps
For policy enforcement, see `databricks-policy-guardrails`.