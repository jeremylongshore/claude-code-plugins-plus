---
name: supabase-rate-limits
description: |
  Manage Supabase rate limits and quotas across all plan tiers.
  Use when hitting 429 errors, configuring connection pooling,
  optimizing API throughput, or understanding tier-specific quotas
  for Auth, Storage, Realtime, and Edge Functions.
  Trigger: "supabase rate limit", "supabase 429", "supabase throttle",
  "supabase quota", "supabase connection pool", "supabase too many requests".
allowed-tools: Read, Write, Edit, Bash, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, rate-limiting, reliability, quotas]

---
# Supabase Rate Limits

## Overview

Supabase enforces rate limits and quotas across every API surface — PostgREST, Auth, Storage, Realtime, and Edge Functions. Limits scale by plan tier. This skill covers the exact numbers per tier, connection pooling via Supavisor, retry/backoff patterns, pagination to reduce payload, and dashboard monitoring so you can stay within quotas and handle 429 errors gracefully.

## Prerequisites

- Active Supabase project (any tier)
- `@supabase/supabase-js` v2+ installed
- Project URL and anon/service-role key available
- Node.js 18+ or equivalent runtime

## Instructions

### Step 1 — Understand Rate Limits by Tier and Surface

Every Supabase project has per-surface limits that differ by plan. Know these numbers before you architect:

**API Request Limits**

| Metric | Free | Pro | Enterprise |
|--------|------|-----|------------|
| Requests per minute (RPM) | 500 | 5,000 | Unlimited (custom) |
| Requests per day (RPD) | 50,000 | 1,000,000 | Unlimited (custom) |

**Auth Rate Limits**

| Endpoint | Free | Pro |
|----------|------|-----|
| Signup | 30/hour per IP | Higher (configurable) |
| Sign-in (password) | 30/hour per IP | Higher (configurable) |
| Magic link / OTP | 4/hour per user | Configurable |
| Token refresh | 360/hour | 360/hour |

Auth limits are per-IP and per-user. Configure custom limits in Dashboard > Authentication > Rate Limits.

**Storage Bandwidth**

| Metric | Free | Pro |
|--------|------|-----|
| Storage size | 1 GB | 100 GB |
| Bandwidth | 2 GB/month | 250 GB/month |
| Max file size | 50 MB | 5 GB |
| Upload rate | Shared with API RPM | Shared with API RPM |

**Realtime Connections**

| Metric | Free | Pro |
|--------|------|-----|
| Concurrent connections | 200 | 500 |
| Messages per second | 100 | 500 |
| Channel joins | Shared with connection limit | Shared |

**Edge Functions**

| Metric | Free | Pro |
|--------|------|-----|
| Invocations/month | 500,000 | 2,000,000 |
| Execution time | 150s wall / 50ms CPU | 150s wall / 2s CPU |
| Memory | 256 MB | 256 MB |

**Database Connections**

| Mode | Free | Pro |
|------|------|-----|
| Direct connections | 60 | 100+ |
| Pooled connections (Supavisor) | 200 | 1,500+ |

### Step 2 — Configure Connection Pooling with Supavisor

Supavisor is Supabase's built-in connection pooler (replaced PgBouncer). It supports two modes:

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
      // Use the pooler connection string with port 6543
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
// Connection string: postgresql://...@pooler.supabase.com:5432/postgres
```

**When to use which mode:**

| Use case | Mode | Port |
|----------|------|------|
| Serverless / Edge Functions | Transaction | 6543 |
| Next.js API routes | Transaction | 6543 |
| Long-running workers | Session | 5432 |
| Realtime subscriptions | Direct (no pooler) | 5432 |
| Prisma / Drizzle ORM | Transaction + `?pgbouncer=true` | 6543 |

### Step 3 — Implement Retry, Pagination, and Monitoring

**Retry with exponential backoff for 429 errors:**

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

**Pagination to reduce payload and stay within limits:**

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

**Monitor usage via the Dashboard:**

1. Navigate to Dashboard > Reports > API Usage
2. Check the "API Requests" chart for RPM/RPD trends
3. Review "Database" section for connection count and pool utilization
4. Set up alerts in Dashboard > Settings > Notifications for:
   - API request threshold (e.g., 80% of RPM limit)
   - Database connection saturation
   - Storage bandwidth approaching limit

**Batch operations to reduce request count:**

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

## Output

After applying this skill you will have:

- Clear understanding of rate limits per tier (Free: 500 RPM / 50K RPD, Pro: 5K RPM / 1M RPD)
- Connection pooling configured via Supavisor (port 6543 transaction mode for serverless)
- Retry wrapper with exponential backoff handling 429 errors
- Paginated queries using `.range(0, 99)` to reduce payload size
- Batch upsert pattern reducing N requests to 1
- Dashboard monitoring configured for API usage alerts

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Exceeded RPM or RPD limit | Apply `withRetry` backoff; reduce concurrency; upgrade tier |
| `PGRST000: could not connect` | Connection pool exhausted | Switch to Supavisor transaction mode (port 6543); reduce concurrent queries |
| Auth `over_request_rate_limit` | Too many signups/logins from one IP | Add CAPTCHA; configure custom auth rate limits in Dashboard |
| Storage `413 Payload Too Large` | File exceeds tier limit | Use TUS resumable upload; check tier file size limit |
| Realtime `too_many_connections` | Concurrent connection limit reached | Unsubscribe unused channels; upgrade to Pro for 500 connections |
| Edge Function `BOOT_ERROR` | Cold start timeout or memory exceeded | Reduce bundle size; avoid large imports at top level |
| `pgbouncer=true` errors with Prisma | Missing connection string parameter | Append `?pgbouncer=true` to pooler connection string on port 6543 |

## Examples

**Example 1 — Serverless Edge Function with rate-limit-safe client:**

```typescript
// supabase/functions/process-webhook/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  const payload = await req.json()

  // Batch insert webhook events (single request vs N)
  const { error } = await supabase
    .from('webhook_events')
    .insert(payload.events.map((e: any) => ({
      type: e.type,
      data: e.data,
      received_at: new Date().toISOString(),
    })))

  if (error) {
    console.error('Insert failed:', error.message)
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }

  return new Response(JSON.stringify({ processed: payload.events.length }), { status: 200 })
})
```

**Example 2 — Connection string selection for different runtimes:**

```bash
# Serverless (Vercel, Netlify, Edge Functions) — transaction mode
DATABASE_URL="postgresql://postgres.abc123:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true"

# Long-running server (Express, Fastify) — session mode
DATABASE_URL="postgresql://postgres.abc123:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres"

# Direct connection (migrations, schema changes only)
DATABASE_URL="postgresql://postgres:password@db.abc123.supabase.co:5432/postgres"
```

## Resources

- [Supabase Platform Limits & Quotas](https://supabase.com/docs/guides/platform/going-into-prod#rate-limiting)
- [Supavisor Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Auth Rate Limits Configuration](https://supabase.com/docs/guides/auth/auth-rate-limits)
- [Edge Functions Limits](https://supabase.com/docs/guides/functions/limits)
- [Storage Limits](https://supabase.com/docs/guides/storage#limits)
- [@supabase/supabase-js Reference](https://supabase.com/docs/reference/javascript/introduction)

## Next Steps

For securing your Supabase project with RLS policies and API key management, see `supabase-security-basics`. For optimizing database queries and indexing, see `supabase-performance-tuning`.
