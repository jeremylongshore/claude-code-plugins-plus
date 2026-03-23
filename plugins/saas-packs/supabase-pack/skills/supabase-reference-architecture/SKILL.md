---
name: supabase-reference-architecture
description: |
  Implement enterprise Supabase reference architectures — monorepo layout, multi-tenant RLS,
  microservices with cross-project access, framework integration, edge functions, caching,
  queue patterns, and audit logging.
  Use when designing a new Supabase project from scratch, reviewing project structure for
  production readiness, planning multi-tenant isolation, or establishing team architecture standards.
  Trigger with phrases like "supabase architecture", "supabase project structure",
  "supabase monorepo", "supabase multi-tenant", "supabase reference design",
  "how to organize supabase at scale".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(supabase:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, architecture, patterns, multi-tenant, monorepo]
---

# Supabase Reference Architecture

## Overview

Production Supabase applications need more than a flat `lib/supabase.ts` file. This skill covers five enterprise architecture patterns: monorepo with shared types, multi-tenant RLS isolation, microservices with separate Supabase projects, framework integration (Next.js / SvelteKit), and operational patterns (edge functions, caching, queues, audit trails). Each pattern stands alone — pick the ones that match your scale.

For the full monorepo directory layout and microservices cross-project access, see [Project Structure](references/project-structure.md). For edge functions, caching, queue, and audit trail patterns, see [Operational Patterns](references/key-components.md).

## Prerequisites

- `@supabase/supabase-js` v2+ installed (`npm install @supabase/supabase-js`)
- Supabase CLI installed (`npm install -g supabase`)
- A Supabase project at [supabase.com/dashboard](https://supabase.com/dashboard)
- Familiarity with `supabase-install-auth` (project URL, anon key, service role key)
- PostgreSQL basics (RLS policies, triggers, functions)

## Instructions

### Step 1: Client Singleton — The Foundation

Every app in the monorepo imports from a shared package instead of creating its own client. This guarantees a single source of truth for the URL, keys, and type definitions.

```typescript
// packages/supabase/src/client.ts
import { createClient, SupabaseClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

let client: SupabaseClient<Database> | null = null

export function getSupabaseClient(): SupabaseClient<Database> {
  if (!client) {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? process.env.SUPABASE_URL
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? process.env.SUPABASE_ANON_KEY
    if (!url || !key) {
      throw new Error('Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables')
    }
    client = createClient<Database>(url, key)
  }
  return client
}

// Reset for testing
export function resetClient(): void {
  client = null
}
```

```typescript
// packages/supabase/src/admin.ts — Server-side only, never bundle in client code
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

export function getSupabaseAdmin() {
  const url = process.env.SUPABASE_URL
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !serviceKey) {
    throw new Error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY — server-only')
  }
  return createClient<Database>(url, serviceKey, {
    auth: { autoRefreshToken: false, persistSession: false }
  })
}
```

Key detail: The admin client sets `autoRefreshToken: false` and `persistSession: false` because server-side code should never store user sessions.

### Step 2: Multi-Tenant RLS via JWT Claims

The most scalable Supabase multi-tenant pattern uses a custom JWT claim (`org_id`) combined with RLS policies. Every table includes an `org_id` column, and RLS extracts the tenant from the user's JWT — no application-level filtering needed.

```sql
-- Migration: 20260101000000_create_tenants.sql

-- Tenants table
create table public.tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  plan text default 'free' check (plan in ('free', 'pro', 'enterprise')),
  created_at timestamptz default now()
);

-- Tenant membership
create table public.tenant_members (
  tenant_id uuid references public.tenants(id) on delete cascade,
  user_id uuid references auth.users(id) on delete cascade,
  role text default 'member' check (role in ('owner', 'admin', 'member', 'viewer')),
  primary key (tenant_id, user_id)
);

-- Example tenant-scoped table
create table public.projects (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.tenants(id) on delete cascade,
  name text not null,
  created_by uuid references auth.users(id),
  created_at timestamptz default now()
);

-- Enable RLS on all tenant-scoped tables
alter table public.projects enable row level security;

-- RLS policy: users can only see rows belonging to their tenant
-- The org_id is extracted from the JWT claims set during authentication
create policy "Tenant isolation" on public.projects
  for all
  using (
    org_id = (auth.jwt() ->> 'org_id')::uuid
  );
```

The tenant-switching function verifies membership before updating the JWT claim:

```sql
-- Helper function to set org_id in JWT claims after login
create or replace function public.set_tenant_claim(tenant_id uuid)
returns void as $$
begin
  -- Verify user is a member of this tenant
  if not exists (
    select 1 from public.tenant_members
    where tenant_members.tenant_id = set_tenant_claim.tenant_id
      and tenant_members.user_id = auth.uid()
  ) then
    raise exception 'Not a member of tenant %', tenant_id;
  end if;

  -- Set the custom claim
  perform auth.update_user_metadata(
    auth.uid(),
    jsonb_build_object('org_id', tenant_id)
  );
end;
$$ language plpgsql security definer;
```

Key details for multi-tenant RLS:
- `auth.jwt() ->> 'org_id'` reads a custom claim from the user's JWT — zero application code needed
- Every tenant-scoped table must have an `org_id` column and RLS enabled
- Tenant switching requires updating the JWT claim and re-authenticating
- For row-level tenant + role permissions, combine `org_id` with a role lookup

### Step 3: Framework Integration (Next.js)

Server components use the `service_role` key for direct database access. Client components use the `anon` key with RLS protection.

```typescript
// app/lib/supabase-server.ts — Next.js App Router (server components)
import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'
import type { Database } from '@my-platform/supabase'

export async function getSupabaseServer() {
  const cookieStore = await cookies()

  return createClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      auth: { autoRefreshToken: false, persistSession: false },
      global: {
        headers: {
          // Forward the user's auth cookie for RLS context
          cookie: cookieStore.toString()
        }
      }
    }
  )
}

// app/projects/page.tsx — Server component with direct DB access
export default async function ProjectsPage() {
  const supabase = await getSupabaseServer()
  const { data: projects } = await supabase
    .from('projects')
    .select('id, name, created_at')
    .order('created_at', { ascending: false })
    .limit(50)

  return <ProjectList projects={projects ?? []} />
}
```

```typescript
// app/lib/supabase-browser.ts — Client components use the anon key
'use client'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@my-platform/supabase'

let browserClient: ReturnType<typeof createClient<Database>> | null = null

export function getSupabaseBrowser() {
  if (!browserClient) {
    browserClient = createClient<Database>(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  }
  return browserClient
}
```

For SvelteKit integration and additional framework patterns, see [Examples](references/examples.md).

## Output

After applying these patterns you will have:
- Monorepo with shared Supabase client, typed database access, and centralized migrations
- Multi-tenant RLS isolation using `auth.jwt() ->> 'org_id'` — zero application-level filtering
- Framework-specific integration for Next.js (server/client split) and SvelteKit (hooks)
- Edge Functions, caching layer, job queue, and audit trail (see [Operational Patterns](references/key-components.md))

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing SUPABASE_URL or SUPABASE_ANON_KEY` | Environment variables not set | Check `.env` file and ensure variables are loaded |
| `new row violates row-level security policy` | RLS blocks the operation | Verify `org_id` JWT claim matches the row's `org_id` |
| `Not a member of tenant` | User tried switching to unauthorized tenant | Check `tenant_members` table for the user-tenant pair |
| `TypeError: Cannot read properties of null` | Client singleton not initialized | Ensure env vars are available before first `getSupabaseClient()` call |
| `cron.schedule: permission denied` | `pg_cron` extension not enabled | Enable via dashboard: Database > Extensions > pg_cron |

For the full error reference including RLS debugging and cross-project troubleshooting, see [Error Handling Reference](references/errors.md).

## Examples

### Multi-Tenant Query Flow (TypeScript)

```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

const supabase = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// 1. Sign in
const { data: { session } } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password'
})

// 2. Switch tenant context
const { error: claimError } = await supabase.rpc('set_tenant_claim', {
  tenant_id: 'tenant-uuid-here'
})
if (claimError) throw claimError

// 3. Refresh session to pick up new JWT claims
await supabase.auth.refreshSession()

// 4. All subsequent queries are automatically scoped to this tenant
const { data: projects } = await supabase
  .from('projects')
  .select('id, name, created_at')
  .order('created_at', { ascending: false })

console.log('Tenant projects:', projects)
// Only returns projects where org_id matches the JWT claim
```

For the job queue consumer example and SvelteKit integration, see [Examples](references/examples.md).

## Resources

- [Supabase Architecture](https://supabase.com/docs/guides/getting-started/architecture)
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Multi-Tenant RLS](https://supabase.com/docs/guides/auth/row-level-security#multi-tenant-applications)
- [Edge Functions](https://supabase.com/docs/guides/functions)
- [TypeScript Support](https://supabase.com/docs/reference/javascript/typescript-support)
- [Generating Types](https://supabase.com/docs/guides/api/rest/generating-types)
- [pg_cron Extension](https://supabase.com/docs/guides/database/extensions/pg_cron)
- [Auth JWT Helper](https://supabase.com/docs/guides/auth/jwts)
- [createClient Reference](https://supabase.com/docs/reference/javascript/initializing)

## Next Steps

For performance optimization and indexing strategies, see `supabase-performance-tuning`. For deployment pipelines and CI integration, see `supabase-ci-integration`. For security hardening and policy guardrails, see `supabase-security-basics`.
