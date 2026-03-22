---
name: supabase-enterprise-rbac
description: |
  Configure Supabase enterprise RBAC with custom roles, SAML SSO,
  organization-scoped permissions, and JWT custom claims.
  Use when implementing role-based access, configuring SSO,
  or building multi-tenant organization features.
  Trigger with phrases like "supabase SSO", "supabase RBAC",
  "supabase enterprise", "supabase roles", "supabase SAML", "supabase permissions".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, rbac, enterprise, sso]

---
# Supabase Enterprise RBAC

## Overview
Implement enterprise-grade role-based access control in Supabase: custom role definitions stored in Postgres, JWT custom claims via Auth Hooks, organization-scoped RLS policies, and SAML SSO integration.

## Prerequisites
- Supabase Pro or Enterprise plan (SSO requires Enterprise)
- Understanding of JWT and RLS concepts
- Identity Provider for SSO (Okta, Azure AD, Google Workspace)

## Instructions

### Step 1: Define Role Schema

```sql
-- Roles and permissions schema
create type public.app_role as enum ('owner', 'admin', 'editor', 'viewer');

create table public.organizations (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  slug text unique not null,
  created_at timestamptz default now()
);

create table public.organization_members (
  id uuid default gen_random_uuid() primary key,
  organization_id uuid references public.organizations(id) on delete cascade not null,
  user_id uuid references auth.users(id) on delete cascade not null,
  role public.app_role default 'viewer' not null,
  invited_by uuid references auth.users(id),
  created_at timestamptz default now(),
  unique (organization_id, user_id)
);

create index idx_org_members_user on public.organization_members(user_id);
create index idx_org_members_org on public.organization_members(organization_id);
```

### Step 2: Authorization Helper Functions

```sql
-- Check user's role in an organization
create or replace function public.get_user_role(org_id uuid)
returns public.app_role as $$
  select role from public.organization_members
  where organization_id = org_id and user_id = auth.uid()
$$ language sql security definer stable;

-- Check minimum role level
create or replace function public.has_role(org_id uuid, min_role public.app_role)
returns boolean as $$
  select exists (
    select 1 from public.organization_members
    where organization_id = org_id
    and user_id = auth.uid()
    and role <= min_role  -- enum ordering: owner < admin < editor < viewer
  )
$$ language sql security definer stable;

-- Check if user is org member
create or replace function public.is_member(org_id uuid)
returns boolean as $$
  select exists (
    select 1 from public.organization_members
    where organization_id = org_id and user_id = auth.uid()
  )
$$ language sql security definer stable;
```

### Step 3: Role-Based RLS Policies

```sql
-- Enable RLS
alter table public.organizations enable row level security;
alter table public.organization_members enable row level security;

-- Organizations: members can view, admins can update
create policy "Members can view their orgs"
  on public.organizations for select
  using (public.is_member(id));

create policy "Admins can update orgs"
  on public.organizations for update
  using (public.has_role(id, 'admin'));

-- Members: members can view, admins can manage
create policy "Members can view org members"
  on public.organization_members for select
  using (public.is_member(organization_id));

create policy "Admins can insert members"
  on public.organization_members for insert
  with check (public.has_role(organization_id, 'admin'));

create policy "Admins can update member roles"
  on public.organization_members for update
  using (public.has_role(organization_id, 'admin'))
  with check (
    -- Prevent non-owners from promoting to owner
    case when new.role = 'owner'
      then public.has_role(organization_id, 'owner')
      else true
    end
  );

create policy "Admins can remove members"
  on public.organization_members for delete
  using (
    public.has_role(organization_id, 'admin')
    or user_id = auth.uid()  -- users can remove themselves
  );

-- Example: projects within an organization
create policy "Editors+ can create projects"
  on public.projects for insert
  with check (public.has_role(organization_id, 'editor'));

create policy "Viewers+ can view projects"
  on public.projects for select
  using (public.is_member(organization_id));
```

### Step 4: JWT Custom Claims (Auth Hook)

```sql
-- Add user's roles to the JWT so RLS can check without extra queries
create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb as $$
declare
  user_roles jsonb;
begin
  -- Collect all organization memberships
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'org_id', om.organization_id,
        'role', om.role
      )
    ),
    '[]'::jsonb
  ) into user_roles
  from public.organization_members om
  where om.user_id = (event->>'user_id')::uuid;

  -- Inject into JWT claims
  event := jsonb_set(
    event,
    '{claims,org_roles}',
    user_roles
  );

  return event;
end;
$$ language plpgsql stable;

-- Register hook in Dashboard > Auth > Hooks
-- Set "Custom Access Token Hook" to this function
```

```typescript
// Reading custom claims from the JWT client-side
const { data: { session } } = await supabase.auth.getSession()
const orgRoles = session?.user?.app_metadata?.org_roles ?? []

// Find user's role in a specific organization
const userRole = orgRoles.find((r: any) => r.org_id === currentOrgId)?.role
```

### Step 5: SAML SSO Configuration

```bash
# Configure SAML SSO (Enterprise plan required)
# Dashboard > Auth > SSO > Add provider

# Or via Supabase Management API:
curl -X POST "https://api.supabase.com/v1/projects/<ref>/config/auth/sso/providers" \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "saml",
    "metadata_url": "https://login.microsoftonline.com/<tenant>/federationmetadata/2007-06/federationmetadata.xml",
    "domains": ["yourcompany.com"],
    "attribute_mapping": {
      "keys": {
        "email": { "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress" },
        "name": { "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name" }
      }
    }
  }'
```

```typescript
// Initiate SSO login
const { data, error } = await supabase.auth.signInWithSSO({
  domain: 'yourcompany.com',  // matches configured domain
  options: { redirectTo: 'https://app.example.com/auth/callback' },
})
if (data?.url) window.location.href = data.url
```

### Step 6: Middleware Permission Check

```typescript
// middleware/auth.ts
export async function requireRole(
  supabase: SupabaseClient,
  orgId: string,
  minRole: 'owner' | 'admin' | 'editor' | 'viewer'
) {
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('Not authenticated')

  const { data: member } = await supabase
    .from('organization_members')
    .select('role')
    .eq('organization_id', orgId)
    .eq('user_id', user.id)
    .single()

  if (!member) throw new Error('Not a member of this organization')

  const roleHierarchy = ['owner', 'admin', 'editor', 'viewer']
  const userLevel = roleHierarchy.indexOf(member.role)
  const requiredLevel = roleHierarchy.indexOf(minRole)

  if (userLevel > requiredLevel) {
    throw new Error(`Role '${member.role}' insufficient; requires '${minRole}'`)
  }

  return { user, role: member.role }
}
```

## Output
- Role schema with organization-scoped membership
- Authorization helper functions reusable across RLS policies
- RLS policies enforcing role-based access at the database level
- JWT custom claims injecting roles into tokens
- SAML SSO configuration for enterprise identity providers
- Middleware permission check for API-level enforcement

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `42501: RLS violation` on member operations | Insufficient role | Check role hierarchy; verify user is admin+ |
| JWT missing `org_roles` claim | Auth hook not configured | Register hook in Dashboard > Auth > Hooks |
| SSO redirect failing | Wrong domain mapping | Verify domain matches SAML provider config |
| Role escalation attempt | Missing `with check` on update | Add owner-only guard for owner role assignment |

## Resources
- [Supabase Auth SSO](https://supabase.com/docs/guides/auth/enterprise-sso)
- [Auth Hooks](https://supabase.com/docs/guides/auth/auth-hooks)
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)

## Next Steps
For major migration strategies, see `supabase-migration-deep-dive`.
