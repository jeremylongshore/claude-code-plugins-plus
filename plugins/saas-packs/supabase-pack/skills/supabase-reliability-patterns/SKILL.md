---
name: supabase-reliability-patterns
description: |
  Implement Supabase reliability patterns: circuit breakers around Supabase calls,
  idempotent writes, bulkhead isolation, and dead letter queues.
  Use when building fault-tolerant integrations, implementing retry strategies,
  or adding resilience to production Supabase services.
  Trigger with phrases like "supabase reliability", "supabase circuit breaker",
  "supabase idempotent", "supabase resilience", "supabase fallback".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, reliability, resilience]

---
# Supabase Reliability Patterns

## Overview
Production reliability patterns for Supabase: circuit breakers preventing cascading failures, idempotent writes for safe retries, bulkhead isolation for priority queues, graceful degradation during outages, and dead letter queues for failed operations.

## Prerequisites
- Supabase SDK installed
- Understanding of circuit breaker pattern
- Optional: Redis for distributed state

## Instructions

### Pattern 1: Circuit Breaker

```typescript
// lib/circuit-breaker.ts
type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN'

class CircuitBreaker {
  private state: CircuitState = 'CLOSED'
  private failureCount = 0
  private lastFailure = 0
  private successCount = 0

  constructor(
    private readonly threshold: number = 5,      // failures to trip
    private readonly resetTimeout: number = 30000, // ms before half-open
    private readonly halfOpenMax: number = 3       // test requests in half-open
  ) {}

  async execute<T>(fn: () => Promise<T>, fallback?: () => T): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailure > this.resetTimeout) {
        this.state = 'HALF_OPEN'
        this.successCount = 0
      } else {
        if (fallback) return fallback()
        throw new Error('Circuit breaker is OPEN — Supabase calls blocked')
      }
    }

    try {
      const result = await fn()

      if (this.state === 'HALF_OPEN') {
        this.successCount++
        if (this.successCount >= this.halfOpenMax) {
          this.state = 'CLOSED'
          this.failureCount = 0
        }
      }

      return result
    } catch (error) {
      this.failureCount++
      this.lastFailure = Date.now()

      if (this.failureCount >= this.threshold) {
        this.state = 'OPEN'
        console.error(`[CIRCUIT_BREAKER] OPEN after ${this.failureCount} failures`)
      }

      if (fallback) return fallback()
      throw error
    }
  }

  get currentState(): CircuitState { return this.state }
}

// One circuit breaker per Supabase service
export const dbCircuit = new CircuitBreaker(5, 30000)
export const storageCircuit = new CircuitBreaker(3, 60000)
export const authCircuit = new CircuitBreaker(3, 15000)
```

```typescript
// Usage in services
import { dbCircuit } from '../lib/circuit-breaker'

const TodoService = {
  async list(userId: string) {
    return dbCircuit.execute(
      async () => {
        const { data, error } = await supabase
          .from('todos')
          .select('id, title, is_complete')
          .eq('user_id', userId)
        if (error) throw error
        return data
      },
      () => []  // fallback: return empty list when circuit is open
    )
  },
}
```

### Pattern 2: Idempotent Writes

```sql
-- Idempotency key table
create table public.idempotency_keys (
  key text primary key,
  response jsonb not null,
  created_at timestamptz default now(),
  expires_at timestamptz default now() + interval '24 hours'
);

-- Auto-cleanup expired keys
select cron.schedule('cleanup-idempotency', '0 * * * *',
  $$DELETE FROM public.idempotency_keys WHERE expires_at < now()$$
);
```

```typescript
// lib/idempotent.ts
import { createHash } from 'crypto'

export async function idempotentWrite<T>(
  key: string,
  writeFn: () => Promise<T>
): Promise<T> {
  // Check for existing result
  const { data: existing } = await supabase
    .from('idempotency_keys')
    .select('response')
    .eq('key', key)
    .maybeSingle()

  if (existing) {
    return existing.response as T
  }

  // Execute the write
  const result = await writeFn()

  // Store for deduplication
  await supabase.from('idempotency_keys').insert({
    key,
    response: result as any,
    expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  })

  return result
}

// Usage: payment processing
const payment = await idempotentWrite(
  `payment:${orderId}:${amount}`,
  async () => {
    const { data } = await supabase
      .from('payments')
      .insert({ order_id: orderId, amount, status: 'completed' })
      .select()
      .single()
    return data
  }
)
```

### Pattern 3: Bulkhead Isolation

```typescript
// lib/bulkhead.ts
class Bulkhead {
  private active = 0

  constructor(
    private readonly maxConcurrent: number,
    private readonly name: string
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.active >= this.maxConcurrent) {
      throw new Error(`[BULKHEAD:${this.name}] Rejected: ${this.active}/${this.maxConcurrent} slots in use`)
    }

    this.active++
    try {
      return await fn()
    } finally {
      this.active--
    }
  }

  get usage() { return { active: this.active, max: this.maxConcurrent } }
}

// Separate pools for different priority levels
export const criticalBulkhead = new Bulkhead(20, 'critical')  // auth, payments
export const normalBulkhead = new Bulkhead(30, 'normal')       // CRUD operations
export const batchBulkhead = new Bulkhead(5, 'batch')          // bulk imports, reports

// Usage
const authResult = await criticalBulkhead.execute(
  () => supabase.auth.signInWithPassword({ email, password })
)

const reportData = await batchBulkhead.execute(
  () => supabase.from('analytics').select('*').limit(10000)
)
```

### Pattern 4: Graceful Degradation

```typescript
// lib/degradation.ts
interface DegradedResponse<T> {
  data: T
  degraded: boolean
  source: 'live' | 'cache' | 'fallback'
}

async function withDegradation<T>(
  liveFn: () => Promise<T>,
  cacheFn: () => Promise<T | null>,
  fallbackValue: T
): Promise<DegradedResponse<T>> {
  try {
    const data = await liveFn()
    // Update cache on successful fetch
    return { data, degraded: false, source: 'live' }
  } catch (error) {
    console.warn('[DEGRADED] Live fetch failed, trying cache:', error)

    try {
      const cached = await cacheFn()
      if (cached !== null) {
        return { data: cached, degraded: true, source: 'cache' }
      }
    } catch {
      // Cache also failed
    }

    return { data: fallbackValue, degraded: true, source: 'fallback' }
  }
}

// Usage
const { data: products, degraded } = await withDegradation(
  () => supabase.from('products').select('*').then(r => r.data!),
  () => cache.get('products'),
  []  // fallback: empty product list
)

if (degraded) {
  // Show banner: "Some data may be stale. We're working on it."
}
```

### Pattern 5: Dead Letter Queue

```sql
-- Dead letter queue for failed operations
create table public.dead_letter_queue (
  id bigint generated always as identity primary key,
  operation text not null,
  payload jsonb not null,
  error_message text,
  error_code text,
  attempts int default 1,
  max_attempts int default 5,
  status text default 'pending' check (status in ('pending', 'retrying', 'exhausted', 'resolved')),
  created_at timestamptz default now(),
  last_attempted_at timestamptz default now()
);
```

```typescript
// lib/dlq.ts
async function withDLQ<T>(
  operation: string,
  payload: any,
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  try {
    return await fn()
  } catch (error: any) {
    // Enqueue to DLQ for later retry
    await supabase.from('dead_letter_queue').insert({
      operation,
      payload,
      error_message: error.message,
      error_code: error.code,
    })

    console.error(`[DLQ] Enqueued failed ${operation}:`, error.message)
    throw error
  }
}

// Process DLQ items (run via cron or Edge Function)
async function processDLQ() {
  const { data: items } = await supabase
    .from('dead_letter_queue')
    .select('*')
    .eq('status', 'pending')
    .lt('attempts', 5)
    .order('created_at')
    .limit(10)

  for (const item of items ?? []) {
    try {
      // Re-execute the operation based on type
      await retryOperation(item.operation, item.payload)

      await supabase.from('dead_letter_queue')
        .update({ status: 'resolved' })
        .eq('id', item.id)
    } catch {
      await supabase.from('dead_letter_queue')
        .update({
          attempts: item.attempts + 1,
          last_attempted_at: new Date().toISOString(),
          status: item.attempts + 1 >= item.max_attempts ? 'exhausted' : 'pending',
        })
        .eq('id', item.id)
    }
  }
}
```

## Output
- Circuit breaker protecting Supabase calls with configurable thresholds
- Idempotent write pattern preventing duplicate operations
- Bulkhead isolation separating critical and batch operations
- Graceful degradation returning cached/fallback data during outages
- Dead letter queue capturing and replaying failed operations

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit breaker stays OPEN | Supabase still down | Wait for `resetTimeout`; check status.supabase.com |
| Idempotency key collision | Hash collision | Use longer key; include timestamp |
| Bulkhead rejection | All slots in use | Increase pool or queue requests |
| DLQ growing unbounded | Persistent failures | Alert on DLQ depth; fix root cause |

## Resources
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Idempotency Patterns](https://stripe.com/docs/api/idempotent_requests)
- [Bulkhead Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/bulkhead)

## Next Steps
For policy guardrails, see `supabase-policy-guardrails`.
