# Operational Patterns — Edge Functions, Caching, Queues, Audit

## Edge Functions for Business Logic

Move business logic close to the database. Edge Functions run on Deno in the same region as your Supabase project.

```typescript
// supabase/functions/process-order/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  const { order_id } = await req.json()

  // All business logic in one function, close to the database
  const { data: order, error } = await supabase
    .from('orders')
    .select('*, items:order_items(*)')
    .eq('id', order_id)
    .single()

  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 400 })

  // Calculate totals
  const total = order.items.reduce(
    (sum: number, item: { quantity: number; unit_price: number }) =>
      sum + item.quantity * item.unit_price,
    0
  )

  // Update order with calculated total and mark as processed
  const { error: updateError } = await supabase
    .from('orders')
    .update({ total, status: 'processed', processed_at: new Date().toISOString() })
    .eq('id', order_id)

  if (updateError) return new Response(JSON.stringify({ error: updateError.message }), { status: 500 })

  return new Response(JSON.stringify({ order_id, total, status: 'processed' }), {
    headers: { 'Content-Type': 'application/json' }
  })
})
```

Deploy with: `supabase functions deploy process-order`

## Server-Side Caching for Frequent Reads

Reduce database load for frequently-read, rarely-changed data.

```typescript
// lib/cached-queries.ts
import { getSupabaseAdmin } from './admin'

interface CacheEntry<T> {
  data: T
  expiresAt: number
}

const cache = new Map<string, CacheEntry<unknown>>()

export async function cachedQuery<T>(
  key: string,
  queryFn: () => Promise<T>,
  ttlMs: number = 60_000  // Default 60s TTL
): Promise<T> {
  const cached = cache.get(key) as CacheEntry<T> | undefined
  if (cached && cached.expiresAt > Date.now()) {
    return cached.data
  }

  const data = await queryFn()
  cache.set(key, { data, expiresAt: Date.now() + ttlMs })
  return data
}

// Usage: cache tenant config for 5 minutes
export async function getTenantConfig(tenantId: string) {
  return cachedQuery(
    `tenant-config:${tenantId}`,
    async () => {
      const { data, error } = await getSupabaseAdmin()
        .from('tenants')
        .select('id, name, plan, feature_flags')
        .eq('id', tenantId)
        .single()
      if (error) throw error
      return data
    },
    5 * 60_000  // 5 minute TTL
  )
}
```

## Queue Pattern with `pg_cron` and Custom Tables

Supabase does not have a built-in queue, but you can build a reliable one with a jobs table and `pg_cron`.

```sql
-- Migration: 20260104000000_create_job_queue.sql

create table public.job_queue (
  id bigint generated always as identity primary key,
  job_type text not null,
  payload jsonb not null default '{}',
  status text not null default 'pending'
    check (status in ('pending', 'processing', 'completed', 'failed', 'dead')),
  attempts int default 0,
  max_attempts int default 3,
  scheduled_at timestamptz default now(),
  started_at timestamptz,
  completed_at timestamptz,
  error_message text,
  created_at timestamptz default now()
);

create index idx_job_queue_pending
  on public.job_queue (scheduled_at)
  where status = 'pending';

-- Claim the next job atomically (prevents double-processing)
create or replace function public.claim_next_job(p_job_type text)
returns public.job_queue as $$
  update public.job_queue
  set status = 'processing',
      started_at = now(),
      attempts = attempts + 1
  where id = (
    select id from public.job_queue
    where status = 'pending'
      and job_type = p_job_type
      and scheduled_at <= now()
      and attempts < max_attempts
    order by scheduled_at
    for update skip locked
    limit 1
  )
  returning *;
$$ language sql;

-- pg_cron: retry failed jobs every 5 minutes
select cron.schedule(
  'retry-failed-jobs',
  '*/5 * * * *',
  $$
    update public.job_queue
    set status = 'pending'
    where status = 'failed'
      and attempts < max_attempts;

    update public.job_queue
    set status = 'dead'
    where status = 'failed'
      and attempts >= max_attempts;
  $$
);
```

## Audit Trail with Trigger-Based Logging

Automatically log every data change to an append-only audit table.

```sql
-- Migration: 20260105000000_create_audit_log.sql

create table public.audit_log (
  id bigint generated always as identity primary key,
  table_name text not null,
  record_id text not null,
  action text not null check (action in ('INSERT', 'UPDATE', 'DELETE')),
  old_data jsonb,
  new_data jsonb,
  changed_fields text[],
  user_id uuid references auth.users(id),
  org_id uuid,
  ip_address inet,
  created_at timestamptz default now()
);

create index idx_audit_log_table_record on public.audit_log (table_name, record_id);
create index idx_audit_log_created on public.audit_log (created_at);
create index idx_audit_log_user on public.audit_log (user_id);

-- Generic audit trigger function
create or replace function public.audit_trigger_fn()
returns trigger as $$
declare
  changed text[];
  col text;
begin
  if TG_OP = 'UPDATE' then
    for col in select column_name from information_schema.columns
      where table_schema = TG_TABLE_SCHEMA and table_name = TG_TABLE_NAME
    loop
      if to_jsonb(OLD) ->> col is distinct from to_jsonb(NEW) ->> col then
        changed := array_append(changed, col);
      end if;
    end loop;
  end if;

  insert into public.audit_log (
    table_name, record_id, action,
    old_data, new_data, changed_fields,
    user_id, org_id
  ) values (
    TG_TABLE_NAME,
    coalesce(to_jsonb(NEW) ->> 'id', to_jsonb(OLD) ->> 'id'),
    TG_OP,
    case when TG_OP in ('UPDATE', 'DELETE') then to_jsonb(OLD) end,
    case when TG_OP in ('INSERT', 'UPDATE') then to_jsonb(NEW) end,
    changed,
    auth.uid(),
    coalesce(
      to_jsonb(NEW) ->> 'org_id',
      to_jsonb(OLD) ->> 'org_id'
    )::uuid
  );

  return coalesce(NEW, OLD);
end;
$$ language plpgsql security definer;

-- Attach to any table
create trigger audit_projects
  after insert or update or delete on public.projects
  for each row execute function public.audit_trigger_fn();
```

Query the audit trail:

```typescript
const { data: history } = await supabase
  .from('audit_log')
  .select('action, changed_fields, old_data, new_data, created_at')
  .eq('table_name', 'projects')
  .eq('record_id', projectId)
  .order('created_at', { ascending: false })
  .limit(50)
```
