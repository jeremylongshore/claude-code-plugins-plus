---
name: supabase-rate-limits
description: |
  Implement Supabase rate limiting, backoff, retry, and idempotency patterns.
  Use when handling 429 errors, implementing retry logic,
  or optimizing API request throughput against Supabase rate limits.
  Trigger with phrases like "supabase rate limit", "supabase throttle",
  "supabase 429", "supabase retry", "supabase backoff", "supabase too many requests".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, rate-limiting, reliability]

---
# Supabase Rate Limits

## Overview
Handle Supabase API rate limits with retry logic, exponential backoff, request batching, and idempotency keys. Supabase rate limits vary by plan tier and API surface (PostgREST, Auth, Storage, Edge Functions, Realtime).

## Prerequisites
- Supabase SDK installed
- Understanding of async/await patterns

## Instructions

### Supabase Rate Limits by Surface

| Surface | Free Tier | Pro Tier | Notes |
|---------|-----------|----------|-------|
| PostgREST API | ~100 req/s per client | ~1000 req/s | Shared across all tables |
| Auth endpoints | 30 req/hour (signup) | Higher limits | Protects against abuse |
| Storage uploads | 5 MB/file standard | 50 MB/file | Use TUS for larger files |
| Edge Functions | 500K invocations/month | 2M+/month | Per-function limits |
| Realtime | 200 concurrent connections | 500+ | Per-project limit |
| Database connections | 60 direct / 200 pooled | Higher | Use connection pooling |

### Pattern 1: Retry with Exponential Backoff

```typescript
interface RetryOptions {
  maxRetries: number
  baseDelay: number
  maxDelay: number
}

async function withRetry<T>(
  fn: () => Promise<{ data: T | null; error: any }>,
  options: RetryOptions = { maxRetries: 3, baseDelay: 500, maxDelay: 10000 }
): Promise<T> {
  for (let attempt = 0; attempt <= options.maxRetries; attempt++) {
    const { data, error } = await fn()

    if (!error) return data as T

    // Only retry on transient errors
    const isRetryable =
      error.message?.includes('rate limit') ||
      error.message?.includes('too many requests') ||
      error.message?.includes('fetch failed') ||
      error.code === 'PGRST000' ||
      error.code === '429'

    if (!isRetryable || attempt === options.maxRetries) {
      throw error
    }

    const delay = Math.min(
      options.baseDelay * Math.pow(2, attempt) + Math.random() * 200,
      options.maxDelay
    )
    console.warn(`Retry ${attempt + 1}/${options.maxRetries} after ${delay}ms`)
    await new Promise((r) => setTimeout(r, delay))
  }
  throw new Error('Unreachable')
}

// Usage
const data = await withRetry(() =>
  supabase.from('todos').select('*').eq('user_id', userId)
)
```

### Pattern 2: Request Queue with Concurrency Control

```typescript
class SupabaseQueue {
  private queue: Array<() => Promise<void>> = []
  private running = 0
  private maxConcurrent: number

  constructor(maxConcurrent = 5) {
    this.maxConcurrent = maxConcurrent
  }

  async add<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try { resolve(await fn()) }
        catch (e) { reject(e) }
      })
      this.process()
    })
  }

  private async process() {
    while (this.running < this.maxConcurrent && this.queue.length > 0) {
      this.running++
      const task = this.queue.shift()!
      task().finally(() => { this.running--; this.process() })
    }
  }
}

const queue = new SupabaseQueue(5)  // 5 concurrent requests max

// Queue up requests
const results = await Promise.all(
  userIds.map(id =>
    queue.add(() => supabase.from('profiles').select('*').eq('id', id))
  )
)
```

### Pattern 3: Batch Operations

```typescript
// Instead of N individual inserts:
// BAD: for (const item of items) { await supabase.from('items').insert(item) }

// GOOD: batch insert (max 1000 rows per request)
function chunkArray<T>(arr: T[], size: number): T[][] {
  return Array.from({ length: Math.ceil(arr.length / size) }, (_, i) =>
    arr.slice(i * size, i * size + size)
  )
}

async function batchInsert(table: string, rows: any[], batchSize = 500) {
  const chunks = chunkArray(rows, batchSize)
  const results = []

  for (const chunk of chunks) {
    const { data, error } = await supabase
      .from(table)
      .insert(chunk)
      .select()

    if (error) throw error
    results.push(...(data ?? []))
  }

  return results
}

// Batch upsert with conflict handling
const { data } = await supabase
  .from('products')
  .upsert(batchOfProducts, { onConflict: 'sku' })
  .select()
```

### Pattern 4: Idempotency Keys

```typescript
import { createHash } from 'crypto'

function generateIdempotencyKey(operation: string, params: Record<string, any>): string {
  const payload = JSON.stringify({ operation, ...params })
  return createHash('sha256').update(payload).digest('hex').slice(0, 32)
}

async function idempotentInsert(table: string, row: Record<string, any>) {
  const key = generateIdempotencyKey('insert', { table, ...row })

  // Check if already processed
  const { data: existing } = await supabase
    .from('idempotency_keys')
    .select('result')
    .eq('key', key)
    .maybeSingle()

  if (existing) {
    console.log('Returning cached result for key:', key)
    return JSON.parse(existing.result)
  }

  // Execute and store result
  const { data, error } = await supabase.from(table).insert(row).select().single()
  if (error) throw error

  await supabase.from('idempotency_keys').insert({
    key,
    result: JSON.stringify(data),
    expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  })

  return data
}
```

## Output
- Retry wrapper with exponential backoff for transient failures
- Request queue limiting concurrent Supabase calls
- Batch insert/upsert pattern avoiding per-row round trips
- Idempotency key pattern preventing duplicate operations

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Rate limit exceeded | Apply retry with backoff; reduce concurrency |
| `PGRST000: connection pool exhausted` | Too many concurrent queries | Use queue with lower concurrency; enable pgBouncer |
| Auth rate limit (30/hr for signup) | Rapid signups | Implement CAPTCHA or queue signups |
| Storage upload 413 | File too large | Use TUS resumable upload for large files |

## Resources
- [Supabase Quotas & Limits](https://supabase.com/docs/guides/platform/going-into-prod#rate-limiting)
- [Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [p-queue (alternative)](https://github.com/sindresorhus/p-queue)

## Next Steps
For security hardening, see `supabase-security-basics`.
