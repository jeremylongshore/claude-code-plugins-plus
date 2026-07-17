---
name: supabase-schema-from-requirements
description: 'Design Supabase Postgres schema from business requirements with migrations,
  RLS, and types.

  Use when translating specifications into database tables, creating migration files,

  adding Row Level Security policies, or generating TypeScript types from schema.

  Trigger with phrases like "supabase schema", "design database supabase",

  "schema from requirements", "supabase migration", "supabase tables from spec".

  '
allowed-tools: Read, Write, Edit, Bash(supabase:*), Bash(npx:*), Grep
version: 1.52.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- supabase
- database
- migration
- schema-design
- postgres
- rls
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Supabase Schema from Requirements

## Overview

Translate business requirements into a production-ready Postgres schema inside Supabase. This skill covers the full path from specification document to applied migration: entity extraction, table creation with proper data types and constraints, Row Level Security policies, performance indexes, timestamp triggers, and TypeScript type generation. It is the highest-leverage activity in the early stages of any Supabase project because every downstream feature (auth, storage, realtime, edge functions) depends on well-designed tables.

## Prerequisites

- Supabase CLI installed (`npm install -g supabase`) and project linked (`supabase link`)
- `@supabase/supabase-js` v2+ installed in the project
- Business requirements, PRD, or specification document identifying entities and access rules
- Local Supabase running (`supabase start`) or a linked remote project

## Instructions

### Step 1: Parse Requirements and Create Migration

Read the requirements document and extract entities, attributes, relationships, and access control rules. Map each entity to a Postgres table.

**Entity extraction example** (project management app):

| Entity | Key Columns | Relationships |
|--------|------------|---------------|
| Organization | name, slug, plan | has many Projects, has many Members |
| Project | name, description, status | belongs to Organization, has many Tasks |
| Task | title, priority, status, due_date | belongs to Project, assigned to User |
| Member | role (owner/admin/member) | junction linking User to Organization |

Create the migration file:

```bash
npx supabase migration new create_tables
# Creates: supabase/migrations/<timestamp>_create_tables.sql
```

Write the migration SQL using standard Postgres data types (`uuid`, `text`, `integer`, `boolean`, `timestamptz`, `jsonb`):
Full worked migration (project-management app — tables, FKs, indexes, `moddatetime` triggers): [references/worked-schema-examples.md](references/worked-schema-examples.md).

**Data type selection guide:**

| Use case | Type | Notes |
|----------|------|-------|
| Primary keys | `uuid` | Always with `uuid_generate_v4()` default |
| Names, titles | `text` | Prefer over `varchar` in Postgres |
| Counts, ranks | `integer` | Use `bigint` for sequences |
| Flags | `boolean` | Default explicitly to `true` or `false` |
| Timestamps | `timestamptz` | Never use `timestamp` without timezone |
| Flexible data | `jsonb` | Queryable JSON; use for settings, metadata |
| Lists | `text[]` | Postgres arrays for simple tags or labels |

### Step 2: Add Row Level Security Policies

Every table exposed to the client must have RLS enabled. Write helper functions first to avoid repeating authorization logic across policies.

```sql
-- Helper: check if user is a member of an organization
create or replace function public.is_org_member(org_id uuid)
returns boolean as $$
  select exists (
    select 1 from public.members
    where organization_id = org_id
    and user_id = auth.uid()
  );
$$ language sql security definer stable;

-- Helper: check if user is org admin or owner
create or replace function public.is_org_admin(org_id uuid)
returns boolean as $$
  select exists (
    select 1 from public.members
    where organization_id = org_id
    and user_id = auth.uid()
    and role in ('owner', 'admin')
  );
$$ language sql security definer stable;

-- Organizations RLS
alter table public.organizations enable row level security;

create policy "Users read own orgs"
  on public.organizations for select
  using (public.is_org_member(id));

create policy "Authenticated users create orgs"
  on public.organizations for insert
  with check (auth.uid() is not null);

create policy "Admins update orgs"
  on public.organizations for update
  using (public.is_org_admin(id));

create policy "Owners delete orgs"
  on public.organizations for delete
  using (
    exists (
      select 1 from public.members
      where organization_id = id
      and user_id = auth.uid()
      and role = 'owner'
    )
  );

-- Members RLS
alter table public.members enable row level security;

create policy "Members view org roster"
  on public.members for select
  using (public.is_org_member(organization_id));

create policy "Admins manage members"
  on public.members for all
  using (public.is_org_admin(organization_id));

-- Projects RLS
alter table public.projects enable row level security;

create policy "Members view projects"
  on public.projects for select
  using (public.is_org_member(organization_id));

create policy "Admins manage projects"
  on public.projects for all
  using (public.is_org_admin(organization_id));

-- Tasks RLS
alter table public.tasks enable row level security;

create policy "Members view tasks"
  on public.tasks for select
  using (
    exists (
      select 1 from public.projects p
      where p.id = project_id
      and public.is_org_member(p.organization_id)
    )
  );

create policy "Members create tasks"
  on public.tasks for insert
  with check (
    exists (
      select 1 from public.projects p
      where p.id = project_id
      and public.is_org_member(p.organization_id)
    )
  );

create policy "Assignee or admin updates tasks"
  on public.tasks for update
  using (
    assigned_to = auth.uid()
    or exists (
      select 1 from public.projects p
      where p.id = project_id
      and public.is_org_admin(p.organization_id)
    )
  );
```

**RLS policy naming convention:** Use short, descriptive names that state who and what action: `"Users read own"`, `"Admins manage members"`, `"Assignee updates tasks"`.

### Step 3: Apply Migration and Generate Types

```bash
# Apply migration locally
npx supabase db reset

# Or push to a linked remote project
npx supabase db push

# Generate TypeScript types from the live schema
npx supabase gen types typescript --local > types/supabase.ts
```

Use the generated types with the Supabase client:

```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from './types/supabase'

const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Typed insert
const { data: org, error } = await supabase
  .from('organizations')
  .insert({ name: 'Acme Corp', slug: 'acme', plan: 'pro' })
  .select()
  .single()

// Typed select with foreign key join
const { data: tasks } = await supabase
  .from('tasks')
  .select('*, project:project_id(name, organization_id)')
  .eq('status', 'todo')
  .order('due_date', { ascending: true })

// Nested join across multiple tables
const { data: orgWithProjects } = await supabase
  .from('organizations')
  .select(`
    id, name, slug,
    projects:projects(
      id, name, status,
      tasks:tasks(id, title, status, assigned_to)
    )
  `)
  .eq('slug', 'acme')
  .single()
```

Verify RLS is working:

```typescript
// This should return only rows the authenticated user can see
const { data, error } = await supabase.from('organizations').select('*')

if (error) {
  console.error('RLS check failed:', error.message)
}
console.log(`User can see ${data?.length ?? 0} organizations`)
```

## Output

- SQL migration file under `supabase/migrations/` with all tables, constraints, and indexes
- RLS policies matching the access control rules from requirements
- Helper functions (`is_org_member`, `is_org_admin`) for reusable authorization checks
- `moddatetime` triggers for automatic `updated_at` management
- Generated TypeScript types at `types/supabase.ts` for type-safe client queries
- Partial indexes on frequently filtered columns (status, due_date)

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `42P07: relation already exists` | Table name collision in migration | Use `create table if not exists` or rename the table |
| `23503: foreign key violation` | Insert references a nonexistent parent row | Insert parent rows first, or check the UUID |
| `42501: insufficient privilege` | RLS helper function permissions | Add `security definer` to the function definition |
| `42883: function uuid_generate_v4() does not exist` | Extension not enabled | Add `create extension if not exists "uuid-ossp"` |
| `supabase db push` succeeds but tables missing | Migration was already recorded | Check `supabase_migrations.schema_migrations` and repair |
| `PGRST204: column not found` | TypeScript types out of sync | Re-run `npx supabase gen types typescript --local > types/supabase.ts` |
| `new row violates row-level security` | RLS policy blocks the operation | Verify `auth.uid()` matches expected value; check policy `using` clause |
| `moddatetime` trigger fails | Extension not enabled | Add `create extension if not exists "moddatetime"` at top of migration |

## Examples

**E-commerce schema** (different domain, same pattern):

Complete e-commerce migration SQL: [references/worked-schema-examples.md](references/worked-schema-examples.md).

**Querying the e-commerce schema from the client:**

```typescript
// Products with store info
const { data: products } = await supabase
  .from('products')
  .select('*, store:store_id(name, slug)')
  .eq('is_active', true)
  .gte('inventory', 1)
  .order('price', { ascending: true })
  .limit(20)
```

## Resources

- [Row Level Security Guide](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Database Migrations](https://supabase.com/docs/guides/deployment/database-migrations)
- [Supabase CLI Reference](https://supabase.com/docs/reference/cli)
- [JavaScript Client — Select](https://supabase.com/docs/reference/javascript/select)
- [TypeScript Support](https://supabase.com/docs/guides/api/rest/generating-types)
- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)

## Next Steps

For auth integration, file storage, and realtime subscriptions on top of this schema, proceed to `supabase-auth-storage-realtime-core`.
