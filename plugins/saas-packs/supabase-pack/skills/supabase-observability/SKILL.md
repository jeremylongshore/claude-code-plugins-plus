---
name: supabase-observability
description: |
  Set up monitoring and observability for Supabase projects using Dashboard
  reports, CLI inspect commands, pg_stat_statements, log drains, and alerting.
  Use when implementing monitoring, diagnosing slow queries, forwarding logs,
  or configuring alerts for Supabase project health.
  Trigger with phrases like "supabase monitoring", "supabase metrics",
  "supabase observability", "supabase logs", "supabase alerts",
  "supabase inspect", "supabase log drain".
allowed-tools: Read, Write, Edit, Bash(npx supabase:*), Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, supabase, monitoring, observability]
---

# Supabase Observability

## Overview
Monitor Supabase projects end-to-end: Dashboard reports for API/database/auth metrics, `supabase inspect db` CLI for deep Postgres diagnostics, `pg_stat_statements` for query analytics, log drains for external aggregation, Edge Functions for custom metrics, and alerting on quota thresholds.

## Prerequisites
- Supabase CLI installed (`npx supabase --version`)
- Supabase project linked (`supabase link --project-ref <ref>`)
- Pro plan or higher for log drain support and extended log retention
- `@supabase/supabase-js` v2+ installed for application-level monitoring

## Instructions

### Step 1: Dashboard Reports and CLI Inspect Commands

Supabase Dashboard provides built-in reports under **Dashboard > Reports**:

| Report | What It Shows |
|--------|---------------|
| API Requests | Total requests, response times, error rates by endpoint |
| Database | Active connections, query counts, replication lag |
| Auth Usage | Signups, logins, provider breakdown, failed attempts |
| Storage | Bandwidth, object counts, bucket usage |
| Realtime | Active connections, messages per second, channel counts |

For deeper Postgres diagnostics, use the CLI inspect commands:

```bash
# Table sizes — find the largest tables
npx supabase inspect db table-sizes --linked

# Index usage — find unused indexes wasting space
npx supabase inspect db index-usage --linked

# Cache hit ratio — should be > 99% (below 95% means upgrade compute)
npx supabase inspect db cache-hit --linked

# Sequential scans — tables needing indexes
npx supabase inspect db seq-scans --linked

# Long-running queries — find stuck queries
npx supabase inspect db long-running-queries --linked

# Table index sizes — compare index vs table size
npx supabase inspect db table-index-sizes --linked

# Bloat — estimate wasted space from dead tuples
npx supabase inspect db bloat --linked

# Blocking queries — find lock contention
npx supabase inspect db blocking --linked

# Replication slots — check replication health
npx supabase inspect db replication-slots --linked
```

### Step 2: Query Analytics with pg_stat_statements and Log Drains

Enable `pg_stat_statements` for detailed query-level metrics:

```sql
-- Enable the extension (Dashboard > Database > Extensions, or SQL)
create extension if not exists pg_stat_statements;

-- Top 20 slowest queries by average execution time
select
  substring(query, 1, 80) as query_preview,
  calls,
  round(mean_exec_time::numeric, 2) as avg_ms,
  round(max_exec_time::numeric, 2) as max_ms,
  round(total_exec_time::numeric, 2) as total_ms,
  rows
from pg_stat_statements
where mean_exec_time > 50
order by mean_exec_time desc
limit 20;

-- Most-called queries (high call count may indicate N+1 problems)
select
  substring(query, 1, 80) as query_preview,
  calls,
  round(mean_exec_time::numeric, 2) as avg_ms,
  rows
from pg_stat_statements
order by calls desc
limit 20;

-- Real-time connection monitoring
select
  state,
  count(*) as connections,
  max(age(now(), state_change))::text as longest_duration
from pg_stat_activity
where datname = current_database()
group by state
order by connections desc;

-- Reset stats after optimization (to measure improvement)
select pg_stat_statements_reset();
```

**Log drains** forward Supabase logs to external aggregation tools:

```bash
# Add a Datadog log drain
npx supabase log-drains add \
  --name datadog-drain \
  --type datadog \
  --datadog-api-key "$DATADOG_API_KEY" \
  --datadog-region us1 \
  --linked

# Add a custom HTTP log drain (Logflare, Axiom, etc.)
npx supabase log-drains add \
  --name custom-drain \
  --type webhook \
  --url "https://api.logflare.app/logs/supabase" \
  --linked

# List active drains
npx supabase log-drains list --linked

# Remove a drain
npx supabase log-drains remove <drain-id> --linked
```

Log drain events include API requests, Auth events, Postgres logs, Storage operations, and Edge Function invocations.

### Step 3: Custom Metrics, Alerting, and Health Checks

**Custom metrics via Edge Functions** — emit structured events for business-level monitoring:

```typescript
// supabase/functions/collect-metrics/index.ts
import { createClient } from '@supabase/supabase-js';
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';

serve(async () => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );

  // Collect quota-relevant metrics
  const { count: userCount } = await supabase
    .from('profiles')
    .select('*', { count: 'exact', head: true });

  const { count: storageObjects } = await supabase
    .storage.from('uploads')
    .list('', { limit: 1, offset: 0 })
    .then(({ data }) => ({ count: data?.length ?? 0 }));

  const { data: dbSize } = await supabase
    .rpc('get_database_size');

  const metrics = {
    timestamp: new Date().toISOString(),
    user_count: userCount,
    db_size_mb: dbSize,
    storage_objects: storageObjects,
  };

  // Store metrics for trend analysis
  await supabase.from('app_metrics').insert(metrics);

  // Alert on quota thresholds
  const DB_LIMIT_MB = 8000; // 8GB Pro plan limit
  if (dbSize > DB_LIMIT_MB * 0.85) {
    console.warn(`[QUOTA_ALERT] Database at ${Math.round(dbSize / DB_LIMIT_MB * 100)}% capacity`);
    // Send alert via webhook, email, or Slack
  }

  return new Response(JSON.stringify(metrics), {
    headers: { 'Content-Type': 'application/json' },
  });
});
```

Schedule it with a cron trigger in `supabase/config.toml`:

```toml
[functions.collect-metrics]
schedule = "*/15 * * * *"  # Every 15 minutes
```

**Health check endpoint** for uptime monitoring (Uptime Robot, Pingdom, etc.):

```typescript
// supabase/functions/health/index.ts
import { createClient } from '@supabase/supabase-js';
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';

serve(async () => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );

  const checks: Record<string, { status: string; latency_ms: number; detail?: string }> = {};

  // Database check
  const dbStart = Date.now();
  const { error: dbErr } = await supabase.rpc('version');
  checks.database = {
    status: dbErr ? 'unhealthy' : 'healthy',
    latency_ms: Date.now() - dbStart,
    ...(dbErr && { detail: dbErr.message }),
  };

  // Auth check
  const authStart = Date.now();
  const { error: authErr } = await supabase.auth.admin.listUsers({ perPage: 1 });
  checks.auth = {
    status: authErr ? 'unhealthy' : 'healthy',
    latency_ms: Date.now() - authStart,
  };

  // Storage check
  const storageStart = Date.now();
  const { error: storageErr } = await supabase.storage.listBuckets();
  checks.storage = {
    status: storageErr ? 'unhealthy' : 'healthy',
    latency_ms: Date.now() - storageStart,
  };

  const overall = Object.values(checks).every(c => c.status === 'healthy');
  const statusCode = overall ? 200 : 503;

  return new Response(
    JSON.stringify({ status: overall ? 'healthy' : 'degraded', checks, timestamp: new Date().toISOString() }),
    { status: statusCode, headers: { 'Content-Type': 'application/json' } }
  );
});
```

**Real-time connection monitoring** — track active Realtime connections:

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Monitor channel state changes
const channel = supabase.channel('monitoring');

channel
  .on('system', { event: '*' }, (payload) => {
    console.log(`[REALTIME] System event:`, payload);
  })
  .subscribe((status) => {
    console.log(`[REALTIME] Connection status: ${status}`);
    if (status === 'CHANNEL_ERROR') {
      console.error('[REALTIME] Connection lost — will auto-reconnect');
    }
  });
```

## Output
- Dashboard reports configured for API, database, and auth monitoring
- CLI inspect commands available for Postgres diagnostics (table sizes, index usage, cache hits, sequential scans, long-running queries)
- `pg_stat_statements` enabled with slow-query and high-frequency-query views
- Log drains forwarding to external tools (Datadog, Logflare, or webhook)
- Custom metrics Edge Function collecting quota-relevant data on a schedule
- Health check endpoint returning per-service status with latency
- Alerting on quota thresholds (database size, user count)

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `pg_stat_statements` returns no rows | Extension not enabled | Enable via Dashboard > Database > Extensions |
| `supabase inspect db` fails | CLI not linked to project | Run `supabase link --project-ref <ref>` |
| Log drain not receiving events | API key invalid or region mismatch | Verify credentials; check `supabase log-drains list` |
| Cache hit ratio below 95% | Working set exceeds RAM | Upgrade compute add-on or optimize queries |
| Health check returns 503 | One or more services degraded | Check `detail` field in response; verify service role key |
| Edge Function cron not firing | Missing `schedule` in config.toml | Add `[functions.<name>]` with `schedule` field and redeploy |
| Long-running queries growing | Missing indexes or lock contention | Run `inspect db seq-scans` and `inspect db blocking` |

## Examples

### Quick Diagnostic Script
```bash
#!/bin/bash
# supabase-health-check.sh — run all inspect commands at once
echo "=== Table Sizes ==="
npx supabase inspect db table-sizes --linked
echo ""
echo "=== Cache Hit Ratio ==="
npx supabase inspect db cache-hit --linked
echo ""
echo "=== Sequential Scans ==="
npx supabase inspect db seq-scans --linked
echo ""
echo "=== Long Running Queries ==="
npx supabase inspect db long-running-queries --linked
echo ""
echo "=== Index Usage ==="
npx supabase inspect db index-usage --linked
```

### Metrics Table Schema
```sql
create table if not exists app_metrics (
  id bigint generated always as identity primary key,
  timestamp timestamptz not null default now(),
  user_count integer,
  db_size_mb numeric,
  storage_objects integer,
  api_requests_24h integer,
  avg_response_ms numeric
);

-- Index for time-series queries
create index idx_app_metrics_timestamp on app_metrics (timestamp desc);

-- Retention policy: keep 90 days
create or replace function cleanup_old_metrics()
returns void as $$
  delete from app_metrics where timestamp < now() - interval '90 days';
$$ language sql;
```

## Resources
- [Supabase Logs & Analytics](https://supabase.com/docs/guides/platform/logs)
- [Database Inspect Commands](https://supabase.com/docs/guides/database/inspect)
- [Log Drains](https://supabase.com/docs/guides/platform/log-drains)
- [Edge Functions Scheduling](https://supabase.com/docs/guides/functions/schedule-functions)
- [pg_stat_statements](https://supabase.com/docs/guides/database/extensions/pg_stat_statements)
- [Supabase JS Client](https://supabase.com/docs/reference/javascript/introduction)

## Next Steps
For incident response procedures, see `supabase-incident-runbook`.
For performance optimization, see `supabase-performance-tuning`.
