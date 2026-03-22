---
name: supabase-data-handling
description: |
  Implement Supabase PII handling, data retention policies, GDPR/CCPA compliance,
  and audit logging patterns.
  Use when handling sensitive data, implementing user data export/deletion,
  or configuring data retention and redaction in Supabase.
  Trigger with phrases like "supabase GDPR", "supabase PII",
  "supabase data retention", "supabase privacy", "supabase CCPA", "supabase delete user data".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, compliance, gdpr, data-privacy]

---
# Supabase Data Handling

## Overview
Handle sensitive data correctly in Supabase: PII classification, GDPR/CCPA right-to-deletion implementation, data retention policies, audit logging, and user data export.

## Prerequisites
- Understanding of GDPR/CCPA requirements
- Supabase project with user data
- Scheduled job infrastructure (pg_cron or external)

## Instructions

### Step 1: Data Classification Schema

```sql
-- Track which columns contain PII
comment on column public.profiles.email is 'PII: email';
comment on column public.profiles.full_name is 'PII: name';
comment on column public.profiles.phone is 'PII: phone';

-- Query to find all PII columns
select
  c.table_name,
  c.column_name,
  pgd.description as pii_tag
from information_schema.columns c
join pg_statio_user_tables st on st.relname = c.table_name
join pg_description pgd on pgd.objoid = st.relid
  and pgd.objsubid = c.ordinal_position
where pgd.description like 'PII:%'
order by c.table_name;
```

### Step 2: GDPR Right to Deletion

```sql
-- Function: delete all user data (cascade through related tables)
create or replace function public.delete_user_data(target_user_id uuid)
returns jsonb as $$
declare
  result jsonb := '{}';
  deleted_count int;
begin
  -- Delete user's files from storage
  delete from storage.objects
  where owner = target_user_id;
  get diagnostics deleted_count = row_count;
  result := result || jsonb_build_object('storage_objects', deleted_count);

  -- Delete user's todos (example - add all your tables)
  delete from public.todos where user_id = target_user_id;
  get diagnostics deleted_count = row_count;
  result := result || jsonb_build_object('todos', deleted_count);

  -- Delete user's profile
  delete from public.profiles where id = target_user_id;
  get diagnostics deleted_count = row_count;
  result := result || jsonb_build_object('profiles', deleted_count);

  -- Log the deletion for compliance audit
  insert into public.data_deletion_log (user_id, deleted_tables, deleted_at)
  values (target_user_id, result, now());

  -- Delete from Supabase Auth (must be last)
  -- This is done via the admin API, not SQL
  return result;
end;
$$ language plpgsql security definer;
```

```typescript
// api/delete-account.ts — Complete user deletion endpoint
import { getSupabaseAdmin } from '../lib/supabase-admin'

export async function deleteUserAccount(userId: string) {
  const supabase = getSupabaseAdmin()

  // Step 1: Delete application data
  const { data: deletionResult } = await supabase.rpc('delete_user_data', {
    target_user_id: userId,
  })

  // Step 2: Delete storage files
  const { data: files } = await supabase.storage
    .from('avatars')
    .list(userId)

  if (files?.length) {
    await supabase.storage
      .from('avatars')
      .remove(files.map(f => `${userId}/${f.name}`))
  }

  // Step 3: Delete auth user (removes from auth.users)
  const { error } = await supabase.auth.admin.deleteUser(userId)
  if (error) throw error

  return { deleted: true, details: deletionResult }
}
```

### Step 3: Data Export (GDPR Right to Access)

```typescript
// api/export-user-data.ts
export async function exportUserData(userId: string) {
  const supabase = getSupabaseAdmin()

  // Gather all user data across tables
  const [profileRes, todosRes, ordersRes] = await Promise.all([
    supabase.from('profiles').select('*').eq('id', userId).single(),
    supabase.from('todos').select('*').eq('user_id', userId),
    supabase.from('orders').select('*').eq('user_id', userId),
  ])

  const exportData = {
    exported_at: new Date().toISOString(),
    user_id: userId,
    profile: profileRes.data,
    todos: todosRes.data,
    orders: ordersRes.data,
    // Add all tables containing user data
  }

  // Log the export for compliance
  await supabase.from('data_export_log').insert({
    user_id: userId,
    exported_at: new Date().toISOString(),
    tables_exported: Object.keys(exportData).filter(k => k !== 'exported_at' && k !== 'user_id'),
  })

  return exportData
}
```

### Step 4: Data Retention Policies

```sql
-- Create a retention policy table
create table public.retention_policies (
  id serial primary key,
  table_name text not null,
  retention_days int not null,
  delete_column text default 'created_at',
  is_active boolean default true
);

insert into public.retention_policies (table_name, retention_days, delete_column) values
  ('audit_logs', 365, 'created_at'),
  ('api_usage', 90, 'created_at'),
  ('session_logs', 30, 'created_at');

-- Function: enforce retention policies
create or replace function public.enforce_retention()
returns void as $$
declare
  policy record;
  deleted_count int;
begin
  for policy in
    select * from public.retention_policies where is_active = true
  loop
    execute format(
      'DELETE FROM public.%I WHERE %I < now() - interval ''%s days''',
      policy.table_name,
      policy.delete_column,
      policy.retention_days
    );
    get diagnostics deleted_count = row_count;
    raise notice 'Deleted % rows from %', deleted_count, policy.table_name;
  end loop;
end;
$$ language plpgsql security definer;

-- Schedule daily cleanup with pg_cron
select cron.schedule(
  'enforce-retention',
  '0 3 * * *',  -- 3 AM daily
  'select public.enforce_retention()'
);
```

### Step 5: Audit Logging

```sql
-- Audit log table
create table public.audit_log (
  id bigint generated always as identity primary key,
  user_id uuid,
  action text not null,
  table_name text not null,
  record_id text,
  old_data jsonb,
  new_data jsonb,
  ip_address inet,
  created_at timestamptz default now()
);

-- Generic audit trigger
create or replace function public.audit_trigger()
returns trigger as $$
begin
  insert into public.audit_log (user_id, action, table_name, record_id, old_data, new_data)
  values (
    auth.uid(),
    TG_OP,
    TG_TABLE_NAME,
    coalesce(new.id::text, old.id::text),
    case when TG_OP in ('UPDATE', 'DELETE') then to_jsonb(old) end,
    case when TG_OP in ('INSERT', 'UPDATE') then to_jsonb(new) end
  );
  return coalesce(new, old);
end;
$$ language plpgsql security definer;

-- Attach to sensitive tables
create trigger audit_orders
  after insert or update or delete on public.orders
  for each row execute function public.audit_trigger();

create trigger audit_profiles
  after insert or update or delete on public.profiles
  for each row execute function public.audit_trigger();
```

## Output
- PII classification with column-level tagging
- GDPR deletion function cascading through all user data
- User data export endpoint for right-to-access requests
- Automated retention policy enforcement via pg_cron
- Audit trail on sensitive tables capturing all mutations

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `foreign_key_violation` on delete | Dependent rows exist | Delete in correct order or use `ON DELETE CASCADE` |
| `pg_cron` not available | Extension not enabled | Enable pg_cron in Dashboard > Extensions (Pro plan) |
| Audit log growing too large | No retention on audit_log | Add audit_log to retention_policies table |
| Auth user not deleted | Admin API error | Verify service role key; user may already be deleted |

## Resources
- [Supabase Security Guide](https://supabase.com/docs/guides/security)
- [GDPR Compliance](https://supabase.com/docs/company/privacy)
- [pg_cron Extension](https://supabase.com/docs/guides/database/extensions/pg_cron)

## Next Steps
For enterprise access control, see `supabase-enterprise-rbac`.
