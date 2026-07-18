# Worked Schema Examples

Extracted from SKILL.md. Two complete, runnable migrations that follow the
skill's pattern: UUID primary keys, `timestamptz` everywhere, `moddatetime`
triggers for `updated_at`, and RLS enabled per table.

## Project-management app — full migration

```sql
-- supabase/migrations/<timestamp>_create_tables.sql

-- Enable required extensions
create extension if not exists "uuid-ossp";
create extension if not exists "moddatetime";

-- Organizations
create table public.organizations (
  id uuid default uuid_generate_v4() primary key,
  name text not null,
  slug text unique not null,
  plan text default 'free' check (plan in ('free', 'pro', 'enterprise')),
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

-- Organization members (junction table)
create table public.members (
  id uuid default uuid_generate_v4() primary key,
  organization_id uuid references public.organizations(id) on delete cascade not null,
  user_id uuid references auth.users(id) on delete cascade not null,
  role text default 'member' check (role in ('owner', 'admin', 'member')),
  created_at timestamptz default now() not null,
  unique (organization_id, user_id)
);

-- Projects
create table public.projects (
  id uuid default uuid_generate_v4() primary key,
  organization_id uuid references public.organizations(id) on delete cascade not null,
  name text not null,
  description text,
  status text default 'active' check (status in ('active', 'archived', 'deleted')),
  settings jsonb default '{}'::jsonb,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

-- Tasks
create table public.tasks (
  id uuid default uuid_generate_v4() primary key,
  project_id uuid references public.projects(id) on delete cascade not null,
  assigned_to uuid references auth.users(id) on delete set null,
  title text not null,
  description text,
  priority integer default 0 check (priority between 0 and 4),
  status text default 'todo' check (status in ('todo', 'in_progress', 'done', 'cancelled')),
  due_date date,
  tags text[] default '{}',
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

-- Indexes for common query patterns
create index idx_members_user on public.members(user_id);
create index idx_members_org on public.members(organization_id);
create index idx_projects_org on public.projects(organization_id);
create index idx_tasks_project on public.tasks(project_id);
create index idx_tasks_assigned on public.tasks(assigned_to);
create index idx_tasks_status on public.tasks(status) where status not in ('done', 'cancelled');
create index idx_tasks_due on public.tasks(due_date) where due_date is not null;
create index idx_orgs_slug on public.organizations(slug);

-- Automatic updated_at triggers via moddatetime extension
create trigger handle_updated_at before update on public.organizations
  for each row execute procedure moddatetime(updated_at);
create trigger handle_updated_at before update on public.projects
  for each row execute procedure moddatetime(updated_at);
create trigger handle_updated_at before update on public.tasks
  for each row execute procedure moddatetime(updated_at);
```

## E-commerce schema — different domain, same pattern

```sql
create table public.products (
  id uuid default uuid_generate_v4() primary key,
  store_id uuid references public.stores(id) on delete cascade not null,
  name text not null,
  price integer not null check (price >= 0),  -- cents
  currency text default 'usd',
  inventory integer default 0 check (inventory >= 0),
  metadata jsonb default '{}'::jsonb,
  is_active boolean default true,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

alter table public.products enable row level security;

create policy "Anyone reads active products"
  on public.products for select
  using (is_active = true);

create policy "Store owners manage products"
  on public.products for all
  using (
    exists (
      select 1 from public.stores s
      where s.id = store_id and s.owner_id = auth.uid()
    )
  );

create trigger handle_updated_at before update on public.products
  for each row execute procedure moddatetime(updated_at);
```
