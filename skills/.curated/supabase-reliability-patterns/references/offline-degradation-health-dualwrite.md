## Offline Queue, Graceful Degradation, Health Checks, and Dual-Write

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
