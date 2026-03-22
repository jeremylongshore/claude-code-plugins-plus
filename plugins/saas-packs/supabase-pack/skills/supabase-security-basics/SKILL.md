---
name: supabase-security-basics
description: |
  Apply Supabase security best practices: RLS enforcement, key management,
  API surface hardening, and security audit checklist.
  Use when securing a Supabase project, auditing API key usage,
  or implementing least-privilege access patterns.
  Trigger with phrases like "supabase security", "supabase RLS",
  "secure supabase", "supabase API key security", "supabase hardening".
allowed-tools: Read, Write, Edit, Grep, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, security, rls]

---
# Supabase Security Basics

## Overview
Security hardening for Supabase projects: understanding the two API keys, enforcing Row Level Security on every table, securing the API surface, and a production security audit checklist.

## Prerequisites
- Supabase project with Dashboard access
- Understanding of JWT and RLS concepts

## Instructions

### The Two Keys

| Key | Name | Exposed to Client? | RLS Behavior |
|-----|------|-------------------|--------------|
| `SUPABASE_ANON_KEY` | Anonymous/Publishable | Yes, safe for browser | Respects RLS policies |
| `SUPABASE_SERVICE_ROLE_KEY` | Service Role | Never expose | Bypasses ALL RLS |

The anon key is embedded in your JWT and used by PostgREST to determine which RLS policies apply. It is safe to include in client-side bundles. The service role key bypasses all RLS and should only ever be used in server-side code (API routes, Edge Functions, cron jobs).

### Rule 1: Enable RLS on Every Table

```sql
-- Check which tables are missing RLS
select schemaname, tablename, rowsecurity
from pg_tables
where schemaname = 'public'
order by tablename;

-- Enable RLS (does NOT create policies; the table becomes inaccessible until you add them)
alter table public.todos enable row level security;
alter table public.profiles enable row level security;

-- CRITICAL: A table with RLS enabled and NO policies blocks all access via the API.
-- You must add at least one policy for each operation you want to allow.
```

### Rule 2: Write Correct RLS Policies

```sql
-- Pattern: users can only access their own rows
create policy "Users read own data"
  on public.todos for select
  using (auth.uid() = user_id);

-- Pattern: public read, authenticated write
create policy "Anyone can read"
  on public.posts for select
  using (true);

create policy "Authenticated users can insert"
  on public.posts for insert
  with check (auth.uid() is not null);

-- Pattern: role-based access via JWT claims
create policy "Admins can do anything"
  on public.settings for all
  using (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
  );

-- Pattern: organization-scoped access
create policy "Org members can read"
  on public.projects for select
  using (
    exists (
      select 1 from public.members
      where members.organization_id = projects.organization_id
      and members.user_id = auth.uid()
    )
  );
```

### Rule 3: Never Expose Service Role Key

```typescript
// BAD: service role key in client-side code
const supabase = createClient(url, process.env.NEXT_PUBLIC_SERVICE_ROLE_KEY!)  // NEVER

// GOOD: anon key on client side
const supabase = createClient(url, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)

// GOOD: service role key only in server-side code (API routes, Edge Functions)
// app/api/admin/route.ts (Next.js server route)
import { createClient } from '@supabase/supabase-js'
const supabaseAdmin = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)
```

### Rule 4: Secure the API Surface

```sql
-- Revoke default access from the public schema for the anon role
-- (Supabase does this by default, but verify)
revoke all on all tables in schema public from anon;
revoke all on all tables in schema public from authenticated;

-- Then grant back only what you need via RLS policies
-- RLS policies implicitly grant access when they match
```

```typescript
// Disable unused Supabase features in your client config
const supabase = createClient(url, anonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
  },
  // Only expose schemas you need
  db: { schema: 'public' },
})
```

### Rule 5: Protect Against Common Attacks

```sql
-- Enable SSL enforcement (Dashboard > Database > Settings > SSL)
-- Enforces encrypted connections to Postgres

-- Set sensible statement timeout to prevent long-running queries
alter role authenticated set statement_timeout = '10s';

-- Enable pg_audit for compliance logging (Enterprise)
-- create extension pgaudit;
```

```typescript
// Sanitize user input before using in .or() or .textSearch()
// PostgREST parameterizes queries, but filter strings need care
const sanitizedSearch = userInput.replace(/[%_]/g, '\\$&')
const { data } = await supabase
  .from('posts')
  .select('*')
  .ilike('title', `%${sanitizedSearch}%`)
```

### Security Audit Checklist

- [ ] RLS enabled on ALL public tables (check `pg_tables.rowsecurity`)
- [ ] Every table has at least one RLS policy per needed operation
- [ ] Service role key is NOT in any client-side environment variables
- [ ] `.env` files are in `.gitignore`
- [ ] Email confirmation is enabled for auth (Dashboard > Auth > Settings)
- [ ] OAuth redirect URLs are restricted to your domains
- [ ] Unused auth providers are disabled
- [ ] SSL enforcement is enabled (Dashboard > Database > Settings)
- [ ] Database password has been changed from default
- [ ] Point-in-time recovery (PITR) is enabled for production
- [ ] MFA is available for sensitive user operations
- [ ] `statement_timeout` is set for the `authenticated` role

## Output
- RLS enabled and policies created for all public tables
- API keys correctly separated (anon = client, service role = server only)
- Security audit checklist completed
- SSL enforcement and statement timeouts configured

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `42501: new row violates RLS` | Policy missing or incorrect | Add/fix RLS policy for the operation |
| Empty data with no error | RLS filtering out all rows | Verify `auth.uid()` in policy matches user |
| `PGRST302: anonymous access disabled` | Anon key not set | Include anon key in client initialization |

## Resources
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Securing Your API](https://supabase.com/docs/guides/api/securing-your-api)
- [Security Guide](https://supabase.com/docs/guides/security)
- [Production Checklist](https://supabase.com/docs/guides/deployment/going-into-prod)

## Next Steps
For production deployment, see `supabase-prod-checklist`.
