---
name: salesforce-reliability-patterns
description: |
  Implement Salesforce reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant Salesforce integrations, implementing retry strategies,
  or adding resilience to production Salesforce services.
  Trigger with phrases like "salesforce reliability", "salesforce circuit breaker",
  "salesforce idempotent", "salesforce resilience", "salesforce fallback", "salesforce bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesforce]
---

# Salesforce Reliability Patterns

## Overview
Production-grade reliability patterns for Salesforce integrations.

## Prerequisites
- Understanding of circuit breaker pattern
- opossum or similar library installed
- Queue infrastructure for DLQ
- Caching layer for fallbacks

## Circuit Breaker

```typescript
import CircuitBreaker from 'opossum';

const salesforceBreaker = new CircuitBreaker(
  async (operation: () => Promise<any>) => operation(),
  {
    timeout: 30000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000,
    volumeThreshold: 10,
  }
);

// Events
salesforceBreaker.on('open', () => {
  console.warn('Salesforce circuit OPEN - requests failing fast');
  alertOps('Salesforce circuit breaker opened');
});

salesforceBreaker.on('halfOpen', () => {
  console.info('Salesforce circuit HALF-OPEN - testing recovery');
});

salesforceBreaker.on('close', () => {
  console.info('Salesforce circuit CLOSED - normal operation');
});

// Usage
async function safeSalesforceCall<T>(fn: () => Promise<T>): Promise<T> {
  return salesforceBreaker.fire(fn);
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
const salesforceQueues = {
  critical: new PQueue({ concurrency: 10 }),
  normal: new PQueue({ concurrency: 5 }),
  bulk: new PQueue({ concurrency: 2 }),
};

async function prioritizedSalesforceCall<T>(
  priority: 'critical' | 'normal' | 'bulk',
  fn: () => Promise<T>
): Promise<T> {
  return salesforceQueues[priority].add(fn);
}

// Usage
await prioritizedSalesforceCall('critical', () =>
  salesforceClient.processPayment(order)
);

await prioritizedSalesforceCall('bulk', () =>
  salesforceClient.syncCatalog(products)
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

async function timedoutSalesforceCall<T>(
  operation: 'connect' | 'request' | 'upload' | 'longPoll',
  fn: () => Promise<T>
): Promise<T> {
  const timeout = TIMEOUT_CONFIG[operation];

  return Promise.race([
    fn(),
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`Salesforce ${operation} timeout`)), timeout)
    ),
  ]);
}
```

## Graceful Degradation

```typescript
interface SalesforceFallback {
  enabled: boolean;
  data: any;
  staleness: 'fresh' | 'stale' | 'very_stale';
}

async function withSalesforceFallback<T>(
  fn: () => Promise<T>,
  fallbackFn: () => Promise<T>
): Promise<{ data: T; fallback: boolean }> {
  try {
    const data = await fn();
    // Update cache for future fallback
    await updateFallbackCache(data);
    return { data, fallback: false };
  } catch (error) {
    console.warn('Salesforce failed, using fallback:', error.message);
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

class SalesforceDeadLetterQueue {
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
      await salesforceClient[entry.operation](entry.payload);
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

async function salesforceHealthCheck(): Promise<{
  status: HealthStatus;
  details: Record<string, any>;
}> {
  const checks = {
    api: await checkApiConnectivity(),
    circuitBreaker: salesforceBreaker.stats(),
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
Wrap Salesforce calls with circuit breaker.

### Step 2: Add Idempotency Keys
Generate deterministic keys for operations.

### Step 3: Configure Bulkheads
Separate queues for different priorities.

### Step 4: Set Up Dead Letter Queue
Handle permanent failures gracefully.

## Output
- Circuit breaker protecting Salesforce calls
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
const state = salesforceBreaker.stats().state;
console.log('Salesforce circuit:', state);
```

## Resources
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Opossum Documentation](https://nodeshift.dev/opossum/)
- [Salesforce Reliability Guide](https://docs.salesforce.com/reliability)

## Next Steps
For policy enforcement, see `salesforce-policy-guardrails`.