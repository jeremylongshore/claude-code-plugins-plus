---
name: supabase-observability
description: |
  Set up comprehensive observability for Supabase: query monitoring with pg_stat_statements,
  structured logging, Supabase Log Explorer, metrics collection, and alerting.
  Use when implementing monitoring, setting up dashboards,
  or configuring alerts for Supabase project health.
  Trigger with phrases like "supabase monitoring", "supabase metrics",
  "supabase observability", "monitor supabase", "supabase alerts", "supabase logs".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, monitoring, observability]

---
# Supabase Observability

## Overview
Implement monitoring and observability for Supabase projects using built-in tools (Log Explorer, pg_stat_statements, Dashboard metrics) and external integrations (Prometheus, Grafana, Sentry) for a complete picture of application health.

## Prerequisites
- Supabase project on Pro plan or higher (for Log Explorer retention)
- `pg_stat_statements` extension enabled

## Instructions

### Step 1: Supabase Built-In Monitoring

Supabase Dashboard provides several monitoring tools out of the box:

- **Database Health**: Dashboard > Database > Performance (CPU, memory, disk I/O, connections)
- **API Logs**: Dashboard > Logs > API (PostgREST request logs)
- **Auth Logs**: Dashboard > Logs > Auth (login attempts, signups, errors)
- **Storage Logs**: Dashboard > Logs > Storage (uploads, downloads)
- **Realtime Logs**: Dashboard > Logs > Realtime (connections, messages)
- **Edge Function Logs**: Dashboard > Logs > Edge Functions (invocations, errors)

### Step 2: Query Performance Monitoring

```sql
-- Enable pg_stat_statements
create extension if not exists pg_stat_statements;

-- Dashboard view: slow queries
select
  substring(query, 1, 100) as query_preview,
  calls,
  mean_exec_time::numeric(10,2) as avg_ms,
  max_exec_time::numeric(10,2) as max_ms,
  stddev_exec_time::numeric(10,2) as stddev_ms,
  rows
from pg_stat_statements
where mean_exec_time > 100  -- queries averaging over 100ms
order by mean_exec_time desc
limit 20;

-- Connection monitoring
select
  state,
  count(*) as connections,
  max(age(now(), state_change))::text as longest_duration
from pg_stat_activity
where datname = current_database()
group by state
order by connections desc;

-- Cache hit ratio (should be > 99%)
select
  sum(heap_blks_hit) as hits,
  sum(heap_blks_read) as misses,
  round(sum(heap_blks_hit)::numeric /
    nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100, 2) as hit_ratio
from pg_statio_user_tables;
```

### Step 3: Application-Level Observability

```typescript
// lib/supabase-instrumented.ts
import { createClient, SupabaseClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

// Wrap Supabase calls with timing and error tracking
export function createInstrumentedClient(): SupabaseClient<Database> {
  const client = createClient<Database>(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_ANON_KEY!
  )

  // Middleware: log all queries with timing
  const originalFrom = client.from.bind(client)
  client.from = ((table: string) => {
    const start = performance.now()
    const builder = originalFrom(table)

    // Wrap the final execution
    const originalThen = builder.then?.bind(builder)
    if (originalThen) {
      builder.then = ((resolve: any, reject: any) => {
        return originalThen((result: any) => {
          const duration = performance.now() - start
          const logEntry = {
            table,
            duration_ms: Math.round(duration * 100) / 100,
            error: result.error?.code ?? null,
            count: result.data?.length ?? 0,
            timestamp: new Date().toISOString(),
          }

          if (duration > 500) {
            console.warn('[SLOW_QUERY]', JSON.stringify(logEntry))
          }

          if (result.error) {
            console.error('[SUPABASE_ERROR]', JSON.stringify(logEntry))
          }

          return resolve(result)
        }, reject)
      }) as any
    }

    return builder
  }) as any

  return client
}
```

### Step 4: Structured Logging

```typescript
// lib/logger.ts
type LogLevel = 'info' | 'warn' | 'error'

interface LogEntry {
  level: LogLevel
  service: string
  operation: string
  duration_ms?: number
  error_code?: string
  user_id?: string
  metadata?: Record<string, any>
  timestamp: string
}

export function log(entry: Omit<LogEntry, 'timestamp'>) {
  const fullEntry: LogEntry = {
    ...entry,
    timestamp: new Date().toISOString(),
  }
  // Structured JSON for log aggregation (Datadog, CloudWatch, etc.)
  console[entry.level === 'error' ? 'error' : 'log'](JSON.stringify(fullEntry))
}

// Usage in services
async function createOrder(order: OrderInsert) {
  const start = Date.now()
  try {
    const { data, error } = await supabase.from('orders').insert(order).select().single()
    if (error) throw error

    log({
      level: 'info',
      service: 'OrderService',
      operation: 'createOrder',
      duration_ms: Date.now() - start,
      metadata: { order_id: data.id },
    })
    return data
  } catch (err: any) {
    log({
      level: 'error',
      service: 'OrderService',
      operation: 'createOrder',
      duration_ms: Date.now() - start,
      error_code: err.code,
      metadata: { message: err.message },
    })
    throw err
  }
}
```

### Step 5: Health Check with Detailed Metrics

```typescript
// api/health.ts
export async function healthCheck() {
  const checks: Record<string, { status: string; latency_ms: number; detail?: string }> = {}

  // Database
  const dbStart = Date.now()
  const { error: dbErr } = await supabaseAdmin.rpc('version')
  checks.database = {
    status: dbErr ? 'unhealthy' : 'healthy',
    latency_ms: Date.now() - dbStart,
    detail: dbErr?.message,
  }

  // Auth
  const authStart = Date.now()
  const { error: authErr } = await supabaseAdmin.auth.admin.listUsers({ perPage: 1 })
  checks.auth = {
    status: authErr ? 'unhealthy' : 'healthy',
    latency_ms: Date.now() - authStart,
  }

  // Storage
  const storageStart = Date.now()
  const { error: storageErr } = await supabaseAdmin.storage.listBuckets()
  checks.storage = {
    status: storageErr ? 'unhealthy' : 'healthy',
    latency_ms: Date.now() - storageStart,
  }

  const overall = Object.values(checks).every(c => c.status === 'healthy')
  return {
    status: overall ? 'healthy' : 'degraded',
    checks,
    timestamp: new Date().toISOString(),
  }
}
```

### Step 6: Alerting Rules

```yaml
# Example: alert on high error rate (Prometheus/AlertManager)
groups:
  - name: supabase
    rules:
      - alert: HighSupabaseErrorRate
        expr: rate(supabase_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Supabase error rate above 5%"

      - alert: SlowSupabaseQueries
        expr: supabase_query_duration_p95 > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Supabase P95 latency above 1s"

      - alert: SupabaseConnectionPoolExhausted
        expr: supabase_active_connections > 50
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Supabase connection pool near limit"
```

## Output
- `pg_stat_statements` monitoring slow and frequent queries
- Application-level instrumentation tracking query timing
- Structured JSON logging for log aggregation
- Health check endpoint covering database, auth, and storage
- Alert rules for error rates, latency, and connection pool

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `pg_stat_statements` empty | Extension not enabled | Enable via Dashboard > Extensions |
| Log Explorer shows no logs | Free plan retention | Upgrade to Pro for extended log retention |
| Health check timeout | Network or DNS issue | Check SUPABASE_URL; verify connectivity |
| Cache hit ratio < 95% | Working set exceeds RAM | Consider upgrading compute or optimizing queries |

## Resources
- [Supabase Logs & Analytics](https://supabase.com/docs/guides/platform/logs)
- [Database Performance](https://supabase.com/docs/guides/database/inspect)
- [Supabase Reports](https://supabase.com/docs/guides/realtime/reports)

## Next Steps
For incident response, see `supabase-incident-runbook`.
