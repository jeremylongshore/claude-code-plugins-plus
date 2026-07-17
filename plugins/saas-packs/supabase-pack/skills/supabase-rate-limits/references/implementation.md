# Implementation Guide

## Connection Pooling with Supavisor

Supavisor is Supabase's built-in connection pooler (replaced PgBouncer). It supports two modes.

**Transaction mode (port 6543)** — recommended for serverless:

```typescript
import { createClient } from '@supabase/supabase-js'

// Transaction mode: connections returned to pool after each transaction
// Best for: serverless functions, Edge Functions, high-concurrency apps
const supabase = createClient(
  'https://your-project.supabase.co',
  process.env.SUPABASE_ANON_KEY!,
  {
    db: {
      // Use the pooler connection string with port 6543 (transaction pooler)
      // Format: postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
    }
  }
)

// For direct Postgres connections (e.g., Prisma, Drizzle), add pgbouncer=true
// Connection string: postgresql://...@pooler.supabase.com:6543/postgres?pgbouncer=true
```

**Session mode (port 5432)** — for LISTEN/NOTIFY and prepared statements:

```typescript
// Session mode: dedicated connection per client session
// Best for: long-lived connections, LISTEN/NOTIFY, prepared statements
// Connection string: postgresql://...@pooler.supabase.com:5432/postgres (session pooler port)
```

**When to use which mode:**

| Use case | Mode | Port |
| ---------- | ------ | ------ |
| Serverless / Edge Functions | Transaction | 6543 |
| Next.js API routes | Transaction | 6543 |
| Long-running workers | Session | 5432 |
| Realtime subscriptions | Direct (no pooler) | 5432 |
| Prisma / Drizzle ORM | Transaction + `?pgbouncer=true` | 6543 |

## Retry with Exponential Backoff for 429 Errors

```typescript
import { createClient, SupabaseClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

interface RetryConfig {
  maxRetries: number
  baseDelayMs: number
  maxDelayMs: number
}

async function withRetry<T>(
  operation: () => Promise<{ data: T | null; error: any }>,
  config: RetryConfig = { maxRetries: 3, baseDelayMs: 500, maxDelayMs: 10_000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    const { data, error } = await operation()

    if (!error) return data as T

    const isRetryable =
      error.message?.includes('rate limit') ||
      error.message?.includes('too many requests') ||
      error.code === '429' ||
      error.code === 'PGRST000'  // connection pool exhausted

    if (!isRetryable || attempt === config.maxRetries) {
      throw new Error(`Supabase error after ${attempt + 1} attempts: ${error.message}`)
    }

    // Check Retry-After header if available
    const retryAfter = error.details?.retryAfter
    const delay = retryAfter
      ? retryAfter * 1000
      : Math.min(
          config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 200,
          config.maxDelayMs
        )

    console.warn(`[supabase-retry] Attempt ${attempt + 1}/${config.maxRetries}, waiting ${delay}ms`)
    await new Promise((resolve) => setTimeout(resolve, delay))
  }

  throw new Error('Unreachable')
}

// Usage — wraps any Supabase query
const users = await withRetry(() =>
  supabase.from('users').select('id, email, created_at').eq('active', true)
)
```

## Pagination to Reduce Payload and Stay Within Limits

```typescript
// Use .range() to paginate — reduces response size and avoids timeouts
async function fetchPaginated<T>(
  table: string,
  pageSize = 100,
  filters?: (query: any) => any
): Promise<T[]> {
  const allRows: T[] = []
  let from = 0

  while (true) {
    let query = supabase.from(table).select('*', { count: 'exact' })
    if (filters) query = filters(query)

    const { data, error, count } = await query.range(from, from + pageSize - 1)

    if (error) throw error
    if (!data || data.length === 0) break

    allRows.push(...(data as T[]))
    from += pageSize

    // Stop if we've fetched everything
    if (count !== null && from >= count) break
  }

  return allRows
}

// Usage
const allProducts = await fetchPaginated('products', 100, (q) =>
  q.eq('status', 'active').order('created_at', { ascending: false })
)

// Simple single-page fetch with .range()
const { data } = await supabase
  .from('orders')
  .select('id, total, status')
  .range(0, 99)  // First 100 rows (0-indexed)
  .order('created_at', { ascending: false })
```

## Batch Operations to Reduce Request Count

```typescript
// BAD: N individual inserts = N requests against your RPM
// for (const item of items) await supabase.from('items').insert(item)

// GOOD: single batch insert (max ~1000 rows per request)
const { data, error } = await supabase
  .from('items')
  .upsert(batchOfItems, { onConflict: 'external_id' })
  .select()

// For larger batches, chunk into groups
function chunk<T>(arr: T[], size: number): T[][] {
  return Array.from({ length: Math.ceil(arr.length / size) }, (_, i) =>
    arr.slice(i * size, i * size + size)
  )
}

for (const batch of chunk(largeDataset, 500)) {
  await withRetry(() =>
    supabase.from('items').upsert(batch, { onConflict: 'external_id' }).select()
  )
}
```

## Monitor Usage via the Dashboard

1. Navigate to Dashboard > Reports > API Usage
2. Check the "API Requests" chart for RPM/RPD trends
3. Review "Database" section for connection count and pool utilization
4. Set up alerts in Dashboard > Settings > Notifications for:
   - API request threshold (e.g., 80% of RPM limit)
   - Database connection saturation
   - Storage bandwidth approaching limit

## Additional Patterns

### Exponential Backoff with Jitter (generic)

```typescript
async function withExponentialBackoff<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 32000, jitterMs: 500 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;
      const status = error.status || error.response?.status;
      if (status !== 429 && (status < 500 || status >= 600)) throw error;

      // Exponential delay with jitter to prevent thundering herd
      const exponentialDelay = config.baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * config.jitterMs;
      const delay = Math.min(exponentialDelay + jitter, config.maxDelayMs);

      console.log(`Rate limited. Retrying in ${delay.toFixed(0)}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Idempotency Keys for Safe Retries

```typescript
import { v4 as uuidv4 } from 'uuid';
import crypto from 'crypto';

// Generate deterministic key from operation params (for safe retries)
function generateIdempotencyKey(operation: string, params: Record<string, any>): string {
  const data = JSON.stringify({ operation, params });
  return crypto.createHash('sha256').update(data).digest('hex');
}

async function idempotentRequest<T>(
  client: SupabaseClient,
  params: Record<string, any>,
  idempotencyKey?: string  // Pass existing key for retries
): Promise<T> {
  // Use provided key (for retries) or generate deterministic key from params
  const key = idempotencyKey || generateIdempotencyKey(params.method || 'POST', params);
  return client.request({
    ...params,
    headers: { 'Idempotency-Key': key, ...params.headers },
  });
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
