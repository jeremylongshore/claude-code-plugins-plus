# Diagnostic Scripts and Schemas

## Quick Diagnostic Script

Run all inspect commands at once:

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

## Metrics Table Schema

Backing table for the custom-metrics Edge Function, with a retention policy:

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
