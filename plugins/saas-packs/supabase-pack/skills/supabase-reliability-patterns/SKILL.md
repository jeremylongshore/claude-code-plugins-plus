---
name: supabase-reliability-patterns
description: |
  Build resilient Supabase integrations: circuit breakers wrapping createClient
  calls, offline queue with IndexedDB, graceful degradation with cached fallbacks,
  health check endpoints, retry with exponential backoff and jitter,
  and dual-write patterns for critical data.
  Use when building fault-tolerant apps, handling Supabase outages gracefully,
  implementing offline-first patterns, or adding retry logic to SDK calls.
  Trigger with phrases like "supabase circuit breaker", "supabase offline",
  "supabase retry", "supabase health check", "supabase fallback",
  "supabase resilience", "supabase dual write", "supabase outage".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, reliability, resilience, circuit-breaker, offline, retry]
---

# Supabase Reliability Patterns

## Overview

Production Supabase apps need six reliability layers: **circuit breakers** (stop calling Supabase when it's down to prevent cascading failures), **offline queue** (buffer writes when the network is unavailable and replay when reconnected), **graceful degradation** (serve cached or fallback data during outages), **health checks** (detect Supabase availability before routing traffic), **retry with exponential backoff** (handle transient errors without overwhelming the service), and **dual-write** (write critical data to both Supabase and a backup store). All patterns use real `createClient` from `@supabase/supabase-js`.

## Prerequisites

- `@supabase/supabase-js` v2+ installed
- TypeScript project with Supabase client configured
- For offline queue: browser environment with IndexedDB or server with Redis
- For dual-write: secondary data store (Redis, DynamoDB, or local SQLite)

## Step 1 — Circuit Breaker and Retry with Exponential Backoff

A circuit breaker tracks failures per Supabase service (database, auth, storage) and stops making calls when a threshold is exceeded. Combined with retry logic, it prevents both cascading failures and unnecessary retries during extended outages.

### Circuit Breaker Implementation

```typescript
// lib/circuit-breaker.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN'

interface CircuitBreakerOptions {
  failureThreshold: number    // failures before opening
  resetTimeoutMs: number      // ms before trying again (half-open)
  halfOpenSuccesses: number   // successes in half-open to close
  name: string                // for logging
}

class CircuitBreaker {
  private state: CircuitState = 'CLOSED'
  private failures = 0
  private lastFailureTime = 0
  private halfOpenSuccesses = 0

  constructor(private opts: CircuitBreakerOptions) {}

  async call<T>(fn: () => Promise<T>, fallback?: () => T): Promise<T> {
    // Check if circuit should transition from OPEN to HALF_OPEN
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.opts.resetTimeoutMs) {
        this.state = 'HALF_OPEN'
        this.halfOpenSuccesses = 0
        console.log(`[CircuitBreaker:${this.opts.name}] OPEN → HALF_OPEN`)
      } else {
        if (fallback) return fallback()
        throw new Error(`Circuit breaker ${this.opts.name} is OPEN`)
      }
    }

    try {
      const result = await fn()

      // Success in HALF_OPEN: count toward recovery
      if (this.state === 'HALF_OPEN') {
        this.halfOpenSuccesses++
        if (this.halfOpenSuccesses >= this.opts.halfOpenSuccesses) {
          this.state = 'CLOSED'
          this.failures = 0
          console.log(`[CircuitBreaker:${this.opts.name}] HALF_OPEN → CLOSED`)
        }
      } else {
        this.failures = 0  // reset on success in CLOSED state
      }

      return result
    } catch (error) {
      this.failures++
      this.lastFailureTime = Date.now()

      if (this.failures >= this.opts.failureThreshold) {
        this.state = 'OPEN'
        console.error(
          `[CircuitBreaker:${this.opts.name}] CLOSED → OPEN after ${this.failures} failures`
        )
      }

      if (fallback) return fallback()
      throw error
    }
  }

  get currentState() {
    return { state: this.state, failures: this.failures }
  }
}

// One circuit breaker per Supabase service domain
export const dbCircuit = new CircuitBreaker({
  name: 'database',
  failureThreshold: 5,
  resetTimeoutMs: 30_000,
  halfOpenSuccesses: 3,
})

export const authCircuit = new CircuitBreaker({
  name: 'auth',
  failureThreshold: 3,
  resetTimeoutMs: 15_000,
  halfOpenSuccesses: 2,
})

export const storageCircuit = new CircuitBreaker({
  name: 'storage',
  failureThreshold: 3,
  resetTimeoutMs: 60_000,
  halfOpenSuccesses: 2,
})
```

### Retry with Exponential Backoff and Jitter

```typescript
// lib/retry.ts
interface RetryOptions {
  maxRetries: number
  baseDelayMs: number
  maxDelayMs: number
  retryableErrors?: string[]  // Supabase error codes to retry
}

const DEFAULT_RETRYABLE = [
  'PGRST301',   // connection error
  '08006',      // connection failure
  '57014',      // query cancelled (timeout)
  '40001',      // serialization failure
  '53300',      // too many connections
]

export async function withRetry<T>(
  fn: () => Promise<{ data: T | null; error: any }>,
  opts: RetryOptions = { maxRetries: 3, baseDelayMs: 200, maxDelayMs: 5000 }
): Promise<{ data: T | null; error: any }> {
  const retryable = opts.retryableErrors ?? DEFAULT_RETRYABLE

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    const result = await fn()

    if (!result.error) return result

    // Don't retry non-retryable errors (auth, RLS, validation)
    const errorCode = result.error.code ?? ''
    if (!retryable.includes(errorCode) && attempt > 0) {
      return result
    }

    if (attempt < opts.maxRetries) {
      // Exponential backoff with full jitter
      const delay = Math.min(
        opts.baseDelayMs * Math.pow(2, attempt) * (0.5 + Math.random() * 0.5),
        opts.maxDelayMs
      )
      console.warn(
        `[Retry] Attempt ${attempt + 1}/${opts.maxRetries} failed (${errorCode}), ` +
        `retrying in ${Math.round(delay)}ms`
      )
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  // Should not reach here, but return last result
  return fn()
}
```

### Combining Circuit Breaker + Retry

```typescript
// services/todo-service.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from '../lib/database.types'
import { dbCircuit } from '../lib/circuit-breaker'
import { withRetry } from '../lib/retry'

const supabase = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

export const TodoService = {
  async list(userId: string) {
    return dbCircuit.call(
      // Retry transient errors inside the circuit breaker
      () => withRetry(() =>
        supabase
          .from('todos')
          .select('id, title, is_complete, created_at')
          .eq('user_id', userId)
          .order('created_at', { ascending: false })
      ),
      // Fallback when circuit is OPEN: return empty list
      () => ({ data: [], error: null })
    )
  },

  async create(todo: { title: string; user_id: string }) {
    return dbCircuit.call(
      () => withRetry(() =>
        supabase
          .from('todos')
          .insert(todo)
          .select('id, title, is_complete, created_at')
          .single()
      )
      // No fallback for writes — let the error propagate to the offline queue
    )
  },
}
```

## Step 2 — Offline Queue and Graceful Degradation

### Offline Queue with IndexedDB (Browser)

```typescript
// lib/offline-queue.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

interface QueuedOperation {
  id: string
  table: string
  method: 'insert' | 'update' | 'delete'
  payload: any
  createdAt: number
  retries: number
}

class OfflineQueue {
  private db: IDBDatabase | null = null
  private readonly STORE = 'pending_operations'
  private processing = false

  async init() {
    return new Promise<void>((resolve, reject) => {
      const request = indexedDB.open('supabase_offline_queue', 1)
      request.onupgradeneeded = () => {
        const db = request.result
        if (!db.objectStoreNames.contains(this.STORE)) {
          db.createObjectStore(this.STORE, { keyPath: 'id' })
        }
      }
      request.onsuccess = () => { this.db = request.result; resolve() }
      request.onerror = () => reject(request.error)
    })
  }

  async enqueue(op: Omit<QueuedOperation, 'id' | 'createdAt' | 'retries'>) {
    if (!this.db) await this.init()

    const entry: QueuedOperation = {
      ...op,
      id: crypto.randomUUID(),
      createdAt: Date.now(),
      retries: 0,
    }

    const tx = this.db!.transaction(this.STORE, 'readwrite')
    tx.objectStore(this.STORE).add(entry)
    await new Promise(resolve => { tx.oncomplete = resolve })

    console.log(`[OfflineQueue] Enqueued ${op.method} on ${op.table}`)
    return entry.id
  }

  async flush(supabase: ReturnType<typeof createClient<Database>>) {
    if (this.processing || !this.db) return
    this.processing = true

    try {
      const tx = this.db.transaction(this.STORE, 'readonly')
      const store = tx.objectStore(this.STORE)
      const request = store.getAll()
      const items: QueuedOperation[] = await new Promise(resolve => {
        request.onsuccess = () => resolve(request.result)
      })

      for (const item of items.sort((a, b) => a.createdAt - b.createdAt)) {
        try {
          let result: any

          if (item.method === 'insert') {
            result = await supabase.from(item.table).insert(item.payload).select()
          } else if (item.method === 'update') {
            const { id, ...updates } = item.payload
            result = await supabase.from(item.table).update(updates).eq('id', id)
          } else if (item.method === 'delete') {
            result = await supabase.from(item.table).delete().eq('id', item.payload.id)
          }

          if (result?.error) throw result.error

          // Remove from queue on success
          const deleteTx = this.db!.transaction(this.STORE, 'readwrite')
          deleteTx.objectStore(this.STORE).delete(item.id)
          console.log(`[OfflineQueue] Flushed ${item.method} on ${item.table}`)
        } catch (error) {
          console.warn(`[OfflineQueue] Failed to flush ${item.id}:`, error)
          // Increment retry count; give up after 10 attempts
          if (item.retries >= 10) {
            const deleteTx = this.db!.transaction(this.STORE, 'readwrite')
            deleteTx.objectStore(this.STORE).delete(item.id)
            console.error(`[OfflineQueue] Gave up on ${item.id} after 10 retries`)
          } else {
            const updateTx = this.db!.transaction(this.STORE, 'readwrite')
            updateTx.objectStore(this.STORE).put({ ...item, retries: item.retries + 1 })
          }
        }
      }
    } finally {
      this.processing = false
    }
  }

  get pendingCount(): Promise<number> {
    if (!this.db) return Promise.resolve(0)
    const tx = this.db.transaction(this.STORE, 'readonly')
    const request = tx.objectStore(this.STORE).count()
    return new Promise(resolve => { request.onsuccess = () => resolve(request.result) })
  }
}

export const offlineQueue = new OfflineQueue()

// Auto-flush when back online
if (typeof window !== 'undefined') {
  window.addEventListener('online', async () => {
    const supabase = createClient<Database>(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
    await offlineQueue.flush(supabase)
  })
}
```

### Graceful Degradation with Cached Fallbacks

```typescript
// lib/degradation.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

interface DegradedResponse<T> {
  data: T
  degraded: boolean
  source: 'live' | 'cache' | 'fallback'
  cachedAt?: number
}

const cache = new Map<string, { data: any; timestamp: number }>()

export async function withDegradation<T>(
  cacheKey: string,
  liveFn: () => Promise<{ data: T | null; error: any }>,
  fallbackValue: T,
  cacheTtlMs = 5 * 60 * 1000  // 5 min default
): Promise<DegradedResponse<T>> {
  // Try live data first
  try {
    const { data, error } = await liveFn()
    if (!error && data !== null) {
      // Update cache on success
      cache.set(cacheKey, { data, timestamp: Date.now() })
      return { data, degraded: false, source: 'live' }
    }
    // Fall through to cache on error
    if (error) console.warn(`[Degradation] Live fetch failed: ${error.message}`)
  } catch (err) {
    console.warn('[Degradation] Live fetch threw:', err)
  }

  // Try cached data
  const cached = cache.get(cacheKey)
  if (cached && Date.now() - cached.timestamp < cacheTtlMs) {
    return {
      data: cached.data as T,
      degraded: true,
      source: 'cache',
      cachedAt: cached.timestamp,
    }
  }

  // Last resort: static fallback
  return { data: fallbackValue, degraded: true, source: 'fallback' }
}

// Usage
const supabase = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

async function getProducts(categoryId: string) {
  const result = await withDegradation(
    `products:${categoryId}`,
    () => supabase
      .from('products')
      .select('id, name, price, image_url')
      .eq('category_id', categoryId)
      .order('name'),
    []  // fallback: empty product list
  )

  if (result.degraded) {
    console.log(`Serving ${result.source} data for products`)
    // Show banner: "Some data may be stale"
  }

  return result
}
```

## Step 3 — Health Checks and Dual-Write for Critical Data

### Health Check Endpoint

```typescript
// api/health.ts (Next.js API route or Express handler)
import { createClient } from '@supabase/supabase-js'

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  services: {
    database: { ok: boolean; latencyMs: number }
    auth: { ok: boolean; latencyMs: number }
    storage: { ok: boolean; latencyMs: number }
  }
  timestamp: string
}

export async function checkHealth(): Promise<HealthStatus> {
  const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )

  const checks = await Promise.allSettled([
    // Database health: simple query
    (async () => {
      const start = Date.now()
      const { error } = await supabase.from('health_checks').select('id').limit(1)
      return { ok: !error, latencyMs: Date.now() - start }
    })(),

    // Auth health: verify service key works
    (async () => {
      const start = Date.now()
      const { error } = await supabase.auth.admin.listUsers({ perPage: 1 })
      return { ok: !error, latencyMs: Date.now() - start }
    })(),

    // Storage health: list buckets
    (async () => {
      const start = Date.now()
      const { error } = await supabase.storage.listBuckets()
      return { ok: !error, latencyMs: Date.now() - start }
    })(),
  ])

  const [db, auth, storage] = checks.map(r =>
    r.status === 'fulfilled' ? r.value : { ok: false, latencyMs: -1 }
  )

  const allOk = db.ok && auth.ok && storage.ok
  const anyOk = db.ok || auth.ok || storage.ok

  return {
    status: allOk ? 'healthy' : anyOk ? 'degraded' : 'unhealthy',
    services: { database: db, auth, storage },
    timestamp: new Date().toISOString(),
  }
}

// Periodic health check (call every 30s)
let lastHealth: HealthStatus | null = null

setInterval(async () => {
  lastHealth = await checkHealth()
  if (lastHealth.status !== 'healthy') {
    console.warn('[HealthCheck]', JSON.stringify(lastHealth))
    // Alert via webhook, PagerDuty, etc.
  }
}, 30_000)

export function getLastHealth() { return lastHealth }
```

### Dual-Write for Critical Data

For operations where data loss is unacceptable (payments, audit logs), write to both Supabase and a backup store. Reconcile later if they diverge.

```typescript
// lib/dual-write.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'
import Redis from 'ioredis'

const supabase = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)

const redis = new Redis(process.env.REDIS_URL!)

interface DualWriteResult<T> {
  primary: { data: T | null; error: any }
  backup: { ok: boolean; error?: string }
}

export async function dualWrite<T>(
  table: string,
  record: Record<string, any>,
  selectColumns: string
): Promise<DualWriteResult<T>> {
  // Write to both stores concurrently
  const [primary, backup] = await Promise.allSettled([
    // Primary: Supabase
    supabase
      .from(table)
      .insert(record)
      .select(selectColumns)
      .single(),

    // Backup: Redis with 30-day TTL
    redis.set(
      `backup:${table}:${record.id ?? crypto.randomUUID()}`,
      JSON.stringify({ ...record, _written_at: new Date().toISOString() }),
      'EX', 30 * 24 * 60 * 60
    ),
  ])

  const primaryResult = primary.status === 'fulfilled'
    ? primary.value
    : { data: null, error: primary.reason }

  const backupResult = backup.status === 'fulfilled'
    ? { ok: true }
    : { ok: false, error: String(backup.reason) }

  // Log if writes diverge
  if (primaryResult.error && backupResult.ok) {
    console.error(`[DualWrite] Primary failed but backup succeeded for ${table}`)
  } else if (!primaryResult.error && !backupResult.ok) {
    console.warn(`[DualWrite] Primary succeeded but backup failed for ${table}`)
  }

  return { primary: primaryResult, backup: backupResult }
}

// Usage: payment processing
async function recordPayment(payment: {
  order_id: string
  amount: number
  currency: string
  stripe_payment_id: string
}) {
  const result = await dualWrite<Database['public']['Tables']['payments']['Row']>(
    'payments',
    {
      ...payment,
      id: crypto.randomUUID(),
      status: 'completed',
      created_at: new Date().toISOString(),
    },
    'id, order_id, amount, status, created_at'
  )

  if (result.primary.error) {
    // Primary write failed — payment is in Redis backup
    // Trigger reconciliation job
    console.error('Payment write failed, queued for reconciliation:', result.primary.error)
    throw new Error(`Payment recording failed: ${result.primary.error.message}`)
  }

  return result.primary.data
}
```

### Reconciliation Job for Dual-Write

```typescript
// jobs/reconcile-payments.ts
import { createClient } from '@supabase/supabase-js'
import Redis from 'ioredis'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)

const redis = new Redis(process.env.REDIS_URL!)

export async function reconcilePayments() {
  // Find all backup records that might not be in Supabase
  const keys = await redis.keys('backup:payments:*')

  for (const key of keys) {
    const raw = await redis.get(key)
    if (!raw) continue

    const record = JSON.parse(raw)

    // Check if it exists in Supabase
    const { data } = await supabase
      .from('payments')
      .select('id')
      .eq('id', record.id)
      .maybeSingle()

    if (!data) {
      // Missing from Supabase — replay the write
      const { error } = await supabase
        .from('payments')
        .insert(record)
        .select()

      if (!error) {
        await redis.del(key)
        console.log(`[Reconcile] Replayed payment ${record.id}`)
      } else {
        console.error(`[Reconcile] Failed to replay ${record.id}:`, error.message)
      }
    } else {
      // Already in Supabase — clean up backup
      await redis.del(key)
    }
  }
}
```

## Output

- Circuit breaker protecting database, auth, and storage calls independently
- Retry with exponential backoff and jitter for transient Supabase errors
- Offline queue buffering writes during network outages with auto-flush on reconnect
- Graceful degradation serving cached or fallback data when Supabase is unavailable
- Health check endpoint monitoring all three Supabase services
- Dual-write pattern ensuring critical data survives Supabase outages
- Reconciliation job detecting and replaying missing records

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit stays OPEN indefinitely | Supabase extended outage | Monitor `status.supabase.com`; circuit auto-recovers via HALF_OPEN |
| Offline queue grows unbounded | User offline for hours | Cap queue at 1000 items; show UI warning at 100 |
| Stale cache served too long | Cache TTL too generous | Reduce `cacheTtlMs`; show "last updated" timestamp |
| Dual-write divergence | Network partition | Run reconciliation job every 5 min; alert on divergence count |
| Health check false positive | Transient network blip | Require 3 consecutive failures before marking unhealthy |
| Retry storm | All clients retry simultaneously | Jitter prevents thundering herd; circuit breaker stops retries when open |

## Examples

### Quick Health Check from CLI

```bash
curl -s https://your-app.com/api/health | jq '.services'
```

### Check Circuit Breaker Status

```typescript
import { dbCircuit, authCircuit, storageCircuit } from '../lib/circuit-breaker'

function getCircuitStatus() {
  return {
    database: dbCircuit.currentState,
    auth: authCircuit.currentState,
    storage: storageCircuit.currentState,
  }
}
```

### Test Offline Queue Pending Count

```typescript
import { offlineQueue } from '../lib/offline-queue'

const pending = await offlineQueue.pendingCount
if (pending > 0) {
  showBanner(`${pending} changes waiting to sync`)
}
```

## Resources

- [Circuit Breaker Pattern (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Exponential Backoff (AWS)](https://docs.aws.amazon.com/general/latest/gr/api-retries.html)
- [Supabase Status Page](https://status.supabase.com)
- [IndexedDB API](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)
- [Supabase Realtime (connection recovery)](https://supabase.com/docs/guides/realtime)

## Next Steps

For organizational governance and policy guardrails, see `supabase-policy-guardrails`.
