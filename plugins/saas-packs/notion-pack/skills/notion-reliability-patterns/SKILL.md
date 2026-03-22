---
name: notion-reliability-patterns
description: |
  Implement reliability patterns for Notion integrations: circuit breaker,
  graceful degradation, idempotency, and dead letter queues.
  Use when building fault-tolerant Notion integrations or adding resilience
  to production Notion services.
  Trigger with phrases like "notion reliability", "notion circuit breaker",
  "notion resilience", "notion fallback", "notion fault tolerant".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Reliability Patterns

## Overview
Production-grade reliability patterns for Notion integrations: circuit breaker to prevent cascade failures, graceful degradation with cached fallbacks, idempotent operations, and dead letter queues for failed writes.

## Prerequisites
- `@notionhq/client` installed
- Understanding of circuit breaker pattern
- Cache infrastructure (LRU or Redis)

## Instructions

### Step 1: Circuit Breaker for Notion API
```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

type CircuitState = 'closed' | 'open' | 'half-open';

class NotionCircuitBreaker {
  private state: CircuitState = 'closed';
  private failureCount = 0;
  private lastFailureTime = 0;
  private readonly failureThreshold = 5;    // Open after 5 consecutive failures
  private readonly resetTimeoutMs = 30_000;  // Try again after 30s

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.resetTimeoutMs) {
        this.state = 'half-open';
        console.log('Circuit half-open: testing Notion connectivity');
      } else {
        throw new Error('Circuit open: Notion API calls are disabled');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure(error);
      throw error;
    }
  }

  private onSuccess() {
    this.failureCount = 0;
    if (this.state === 'half-open') {
      this.state = 'closed';
      console.log('Circuit closed: Notion connectivity restored');
    }
  }

  private onFailure(error: unknown) {
    // Only count server errors and rate limits, not client errors
    if (isNotionClientError(error)) {
      const isTransient = error.code === APIErrorCode.RateLimited ||
        error.code === APIErrorCode.InternalServerError ||
        error.code === APIErrorCode.ServiceUnavailable;

      if (!isTransient) return; // Don't trip circuit on 400/401/404
    }

    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.failureCount >= this.failureThreshold) {
      this.state = 'open';
      console.warn(`Circuit OPEN after ${this.failureCount} failures`);
    }
  }

  getState(): { state: CircuitState; failures: number } {
    return { state: this.state, failures: this.failureCount };
  }
}

const circuitBreaker = new NotionCircuitBreaker();

// Usage
const pages = await circuitBreaker.execute(() =>
  notion.databases.query({ database_id: dbId })
);
```

### Step 2: Graceful Degradation with Cached Fallback
```typescript
import { LRUCache } from 'lru-cache';

const fallbackCache = new LRUCache<string, any>({
  max: 500,
  ttl: 3600_000, // 1 hour — stale data is better than no data
});

async function queryWithFallback(dbId: string, filter?: any) {
  const cacheKey = `query:${dbId}:${JSON.stringify(filter ?? {})}`;

  try {
    const result = await circuitBreaker.execute(() =>
      notion.databases.query({ database_id: dbId, filter, page_size: 100 })
    );

    // Update cache on success
    fallbackCache.set(cacheKey, result);
    return { data: result, source: 'live' as const };
  } catch (error) {
    // Try cached data
    const cached = fallbackCache.get(cacheKey);
    if (cached) {
      console.warn('Using cached Notion data (API unavailable)');
      return { data: cached, source: 'cache' as const };
    }

    // No cache available — propagate error
    throw error;
  }
}

// Caller can check source and show staleness indicator
const { data, source } = await queryWithFallback(dbId);
if (source === 'cache') {
  console.log('Warning: showing cached data. Notion API is currently unavailable.');
}
```

### Step 3: Idempotent Page Creation
```typescript
import crypto from 'crypto';

// Generate deterministic key from content
function idempotencyKey(dbId: string, titleContent: string, extraData?: string): string {
  const input = `${dbId}:${titleContent}:${extraData ?? ''}`;
  return crypto.createHash('sha256').update(input).digest('hex').substring(0, 16);
}

// Track created pages to prevent duplicates
const createdPages = new Map<string, string>(); // key -> pageId

async function idempotentCreatePage(
  dbId: string,
  properties: any,
  uniqueKey?: string
) {
  // Generate key from title content
  const titleProp = Object.values(properties).find((p: any) => p.title);
  const titleText = (titleProp as any)?.title?.[0]?.text?.content ?? '';
  const key = uniqueKey ?? idempotencyKey(dbId, titleText);

  // Check if already created
  if (createdPages.has(key)) {
    console.log(`Page already created (idempotency key: ${key})`);
    return { id: createdPages.get(key)!, duplicate: true };
  }

  const page = await notion.pages.create({
    parent: { database_id: dbId },
    properties,
  });

  createdPages.set(key, page.id);
  return { id: page.id, duplicate: false };
}
```

### Step 4: Dead Letter Queue for Failed Writes
```typescript
interface DLQEntry {
  id: string;
  operation: 'create' | 'update' | 'append';
  payload: any;
  error: string;
  attempts: number;
  lastAttempt: Date;
  firstAttempt: Date;
}

class NotionDeadLetterQueue {
  private entries: DLQEntry[] = [];
  private readonly maxAttempts = 5;

  add(operation: DLQEntry['operation'], payload: any, error: string) {
    this.entries.push({
      id: crypto.randomUUID(),
      operation,
      payload,
      error,
      attempts: 1,
      lastAttempt: new Date(),
      firstAttempt: new Date(),
    });
    console.warn(`DLQ: Added failed ${operation} (${this.entries.length} total)`);
  }

  async retryAll(notion: Client): Promise<{ succeeded: number; failed: number }> {
    let succeeded = 0;
    let failed = 0;
    const remaining: DLQEntry[] = [];

    for (const entry of this.entries) {
      try {
        switch (entry.operation) {
          case 'create':
            await notion.pages.create(entry.payload);
            break;
          case 'update':
            await notion.pages.update(entry.payload);
            break;
          case 'append':
            await notion.blocks.children.append(entry.payload);
            break;
        }
        succeeded++;
        // Rate limit compliance
        await new Promise(r => setTimeout(r, 350));
      } catch (error: any) {
        entry.attempts++;
        entry.lastAttempt = new Date();
        entry.error = error.message;

        if (entry.attempts < this.maxAttempts) {
          remaining.push(entry);
        } else {
          console.error(`DLQ: Giving up on ${entry.id} after ${entry.attempts} attempts`);
        }
        failed++;
      }
    }

    this.entries = remaining;
    console.log(`DLQ retry: ${succeeded} succeeded, ${failed} failed, ${remaining.length} remaining`);
    return { succeeded, failed };
  }

  get size() { return this.entries.length; }

  getEntries() { return [...this.entries]; }
}

const dlq = new NotionDeadLetterQueue();

// Usage: wrap writes with DLQ fallback
async function resilientPageCreate(dbId: string, properties: any) {
  try {
    return await circuitBreaker.execute(() =>
      notion.pages.create({ parent: { database_id: dbId }, properties })
    );
  } catch (error: any) {
    dlq.add('create', { parent: { database_id: dbId }, properties }, error.message);
    return null;
  }
}
```

### Step 5: Priority Queue for Mixed Workloads
```typescript
import PQueue from 'p-queue';

// Separate queues prevent bulk operations from blocking critical reads
const queues = {
  critical: new PQueue({ concurrency: 2, interval: 1000, intervalCap: 2 }),
  normal: new PQueue({ concurrency: 1, interval: 1000, intervalCap: 1 }),
};

// Critical: user-facing reads
async function readPage(pageId: string) {
  return queues.critical.add(() => notion.pages.retrieve({ page_id: pageId }));
}

// Normal: background syncs and batch writes
async function backgroundSync(dbId: string, items: any[]) {
  for (const item of items) {
    await queues.normal.add(() =>
      notion.pages.create({ parent: { database_id: dbId }, properties: item })
    );
  }
}

// Total: 3 req/s (2 critical + 1 normal)
```

## Output
- Circuit breaker preventing cascade failures on Notion outages
- Graceful degradation serving cached data when API is down
- Idempotent page creation preventing duplicates
- Dead letter queue for failed writes with automatic retry
- Priority queues for mixed workloads

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit stays open | Threshold too low | Increase `failureThreshold` |
| Stale cached data | Long TTL | Add freshness indicator in UI |
| DLQ growing | Persistent API issue | Check circuit breaker state |
| Duplicate pages | Missing idempotency | Use `idempotentCreatePage` |

## Examples

### Health Dashboard
```typescript
function getSystemHealth() {
  return {
    circuit: circuitBreaker.getState(),
    dlq: { size: dlq.size, entries: dlq.getEntries().map(e => ({
      operation: e.operation, attempts: e.attempts, lastAttempt: e.lastAttempt,
    }))},
    queues: {
      critical: { pending: queues.critical.size, active: queues.critical.pending },
      normal: { pending: queues.normal.size, active: queues.normal.pending },
    },
  };
}
```

## Resources
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Notion Request Limits](https://developers.notion.com/reference/request-limits)
- [p-queue](https://github.com/sindresorhus/p-queue)
- [LRU Cache](https://github.com/isaacs/node-lru-cache)

## Next Steps
For policy enforcement, see `notion-policy-guardrails`.
