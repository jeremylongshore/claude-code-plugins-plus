---
name: supabase-schema-from-requirements
description: |
  Generate Supabase database schema from requirements with RLS policies, indexes, and migrations.
  Use when starting a new project, designing tables from specifications,
  or creating migrations with Row Level Security from business requirements.
  Trigger with phrases like "supabase schema", "database design supabase",
  "generate schema", "supabase migration from requirements", "supabase tables".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, database, migration, schema-design]

---
# Supabase Schema from Requirements

## Overview
Translate business requirements into a well-structured Postgres schema with Row Level Security policies, appropriate indexes, and foreign key constraints. This is the highest-leverage activity in the early stages of a Supabase project.

## Prerequisites
- Supabase CLI installed and project linked
- Business requirements or specification document
- Understanding of PostgreSQL data types

## Instructions

### Step 1: Parse Requirements into Entities

Identify entities, attributes, relationships, and access control rules from the requirements. Example for a project management app:

| Entity | Attributes | Relationships |
|--------|-----------|---------------|
| Organization | name, slug, plan | has many Projects |
| Project | name, description, status | belongs to Org, has many Tasks |
| Task | title, description, priority, status, due_date | belongs to Project, assigned to User |
| Member | role (owner/admin/member) | links User to Organization |

### Step 2: Write the Migration

```bash
supabase migration new create_project_management_schema
```

```sql
-- supabase/migrations/<timestamp>_create_project_management_schema.sql

-- Organizations
create table public.organizations (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  slug text unique not null,
  plan text default 'free' check (plan in ('free', 'pro', 'enterprise')),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Organization members (junction table)
create table public.members (
  id uuid default gen_random_uuid() primary key,
  organization_id uuid references public.organizations(id) on delete cascade not null,
  user_id uuid references auth.users(id) on delete cascade not null,
  role text default 'member' check (role in ('owner', 'admin', 'member')),
  created_at timestamptz default now(),
  unique (organization_id, user_id)
);

-- Projects
create table public.projects (
  id uuid default gen_random_uuid() primary key,
  organization_id uuid references public.organizations(id) on delete cascade not null,
  name text not null,
  description text,
  status text default 'active' check (status in ('active', 'archived', 'deleted')),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Tasks
create table public.tasks (
  id uuid default gen_random_uuid() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  assigned_to uuid references auth.users(id) on delete set null,
  title text not null,
  description text,
  priority int default 0 check (priority between 0 and 4),
  status text default 'todo' check (status in ('todo', 'in_progress', 'done', 'cancelled')),
  due_date date,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Indexes for common query patterns
create index idx_members_user_id on public.members(user_id);
create index idx_members_org_id on public.members(organization_id);
create index idx_projects_org_id on public.projects(organization_id);
create index idx_tasks_project_id on public.tasks(project_id);
create index idx_tasks_assigned_to on public.tasks(assigned_to);
create index idx_tasks_status on public.tasks(status) where status != 'cancelled';

-- Updated_at trigger function
create or replace function public.update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger set_updated_at before update on public.organizations
  for each row execute procedure public.update_updated_at();
create trigger set_updated_at before update on public.projects
  for each row execute procedure public.update_updated_at();
create trigger set_updated_at before update on public.tasks
  for each row execute procedure public.update_updated_at();
```

### Step 3: Add Row Level Security

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

create policy "Members can view their orgs"
  on public.organizations for select
  using (public.is_org_member(id));

create policy "Authenticated users can create orgs"
  on public.organizations for insert
  with check (auth.uid() is not null);

create policy "Admins can update orgs"
  on public.organizations for update
  using (public.is_org_admin(id));

-- Members RLS
alter table public.members enable row level security;

create policy "Members can view org members"
  on public.members for select
  using (public.is_org_member(organization_id));

create policy "Admins can manage members"
  on public.members for all
  using (public.is_org_admin(organization_id));

-- Projects RLS
alter table public.projects enable row level security;

create policy "Members can view projects"
  on public.projects for select
  using (public.is_org_member(organization_id));

create policy "Admins can manage projects"
  on public.projects for all
  using (public.is_org_admin(organization_id));

-- Tasks RLS
alter table public.tasks enable row level security;

create policy "Members can view tasks in their projects"
  on public.tasks for select
  using (
    exists (
      select 1 from public.projects p
      where p.id = project_id
      and public.is_org_member(p.organization_id)
    )
  );

create policy "Members can create and update tasks"
  on public.tasks for insert
  with check (
    exists (
      select 1 from public.projects p
      where p.id = project_id
      and public.is_org_member(p.organization_id)
    )
  );
```

### Step 4: Apply and Verify

```bash
# Apply migration
supabase db reset   # locally
supabase db push    # remote

# Regenerate types
supabase gen types typescript --linked > lib/database.types.ts

# Verify RLS with a test query
supabase db test    # if pgTAP tests are configured
```

## Output
- Complete SQL migration with tables, constraints, and indexes
- RLS policies matching access control requirements
- Helper functions for reusable authorization checks
- `updated_at` triggers for timestamp management
- Generated TypeScript types reflecting the new schema

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `42P07: relation already exists` | Table name collision | Use `if not exists` or choose unique name |
| `23503: foreign key violation` | Referenced row missing | Insert parent rows before children |
| `42501: insufficient privilege` | RLS helper function permissions | Add `security definer` to function |
| `supabase db push` fails silently | Migration already applied | Check `supabase_migrations.schema_migrations` table |

## Resources
- [Row Level Security Guide](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Database Migrations](https://supabase.com/docs/guides/deployment/database-migrations)
- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)

## Next Steps
For auth, storage, and realtime on top of this schema, see `supabase-auth-storage-realtime-core`.
