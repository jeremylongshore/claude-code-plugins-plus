# Row Level Security policies — full worked example

This is the complete RLS policy set for the project-management schema (organizations,
members, projects, tasks). Every table exposed to the client has RLS enabled, and
authorization logic is factored into reusable `security definer` helper functions so it
is written once and referenced from many policies.

## Helper functions

Write helper functions first to avoid repeating authorization logic across policies.

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
```

## Table policies

```sql
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

**RLS policy naming convention:** Use short, descriptive names that state who and what
action: `"Users read own"`, `"Admins manage members"`, `"Assignee updates tasks"`.
