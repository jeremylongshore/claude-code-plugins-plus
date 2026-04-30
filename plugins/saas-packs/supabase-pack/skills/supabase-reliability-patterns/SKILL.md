---
name: supabase-reliability-patterns
description: 'Build resilient Supabase integrations: circuit breakers wrapping createClient

  calls, offline queue with IndexedDB, graceful degradation with cached fallbacks,

  health check endpoints, retry with exponential backoff and jitter,

  and dual-write patterns for critical data.

  Use when building fault-tolerant apps, handling Supabase outages gracefully,

  implementing offline-first patterns, or adding retry logic to SDK calls.

  Trigger with phrases like "supabase circuit breaker", "supabase offline",

  "supabase retry", "supabase health check", "supabase fallback",

  "supabase resilience", "supabase dual write", "supabase outage".

  '
allowed-tools: Read, Write, Edit, Bash(supabase:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- supabase
- reliability
- resilience
- circuit-breaker
- offline
- retry
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
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

See [offline queue, graceful degradation, health checks, and dual-write](references/offline-degradation-health-dualwrite.md) for IndexedDB offline queue with auto-flush, cached fallback patterns, health check endpoints monitoring database/auth/storage, dual-write for critical data with Redis backup, and reconciliation jobs.

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

## Resources

- [Circuit Breaker Pattern (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Exponential Backoff (AWS)](https://docs.aws.amazon.com/general/latest/gr/api-retries.html)
- [Supabase Status Page](https://status.supabase.com)
- [IndexedDB API](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)
- [Supabase Realtime (connection recovery)](https://supabase.com/docs/guides/realtime)

## Next Steps

For organizational governance and policy guardrails, see `supabase-policy-guardrails`.
