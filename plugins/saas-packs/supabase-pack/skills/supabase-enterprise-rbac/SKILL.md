---
name: supabase-enterprise-rbac
description: |
  Implement custom role-based access control via JWT claims in Supabase: app_metadata.role,
  RLS policies with auth.jwt() ->> 'role', organization-scoped access, and API key scoping.
  Use when implementing role-based permissions, configuring organization-level access,
  building admin/member/viewer hierarchies, or scoping API keys per role.
  Trigger: "supabase RBAC", "supabase roles", "supabase permissions", "supabase JWT claims",
  "supabase organization access", "supabase custom roles", "supabase app_metadata".
allowed-tools: Read, Write, Edit, Bash(npx supabase:*), Bash(supabase:*), Bash(psql:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, rbac, security, enterprise, roles, permissions]
---

# Supabase Enterprise RBAC

## Overview

Supabase supports custom role-based access control (RBAC) by storing role information in `app_metadata` on the user's JWT, then reading those claims in RLS policies via `auth.jwt() ->> 'role'`. This skill implements a complete RBAC system: defining roles in `app_metadata`, writing RLS policies that enforce role hierarchies, scoping access by organization, managing roles through the Admin API, and protecting API endpoints with role checks — all using real `createClient` from `@supabase/supabase-js`.

**When to use:** Building multi-role applications (admin/editor/viewer), implementing organization-scoped access, creating custom permission systems beyond Supabase's built-in `anon`/`authenticated` roles, or scoping API operations by user role.

## Prerequisites

- `@supabase/supabase-js` v2+ with service role key for admin operations
- Understanding of JWT claims and Supabase's `auth.jwt()` SQL function
- Database access via SQL Editor or `psql` for RLS policy creation
- Supabase project with authentication configured

## Instructions

### Step 1: Define Roles via app_metadata and JWT Claims

Store custom roles in the user's `app_metadata` using the Admin API. These claims appear in every JWT the user receives and are available in RLS policies.

**Set user roles with the Admin API:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

// Define the role hierarchy
type AppRole = 'admin' | 'editor' | 'viewer' | 'member';

interface AppMetadata {
  role: AppRole;
  org_id: string;
  permissions?: string[];
}

// Assign a role to a user (admin operation)
async function setUserRole(userId: string, role: AppRole, orgId: string) {
  const { data, error } = await supabase.auth.admin.updateUserById(userId, {
    app_metadata: {
      role,
      org_id: orgId,
    },
  });

  if (error) throw new Error(`Failed to set role: ${error.message}`);

  console.log(`User ${userId} assigned role "${role}" in org "${orgId}"`);
  return data.user;
}

// Assign granular permissions (optional, for fine-grained control)
async function setUserPermissions(
  userId: string,
  permissions: string[]
) {
  const { data, error } = await supabase.auth.admin.updateUserById(userId, {
    app_metadata: { permissions },
  });

  if (error) throw new Error(`Failed to set permissions: ${error.message}`);
  return data.user;
}

// Bulk role assignment (e.g., onboarding a team)
async function assignTeamRoles(
  orgId: string,
  assignments: { userId: string; role: AppRole }[]
) {
  const results = await Promise.allSettled(
    assignments.map(({ userId, role }) => setUserRole(userId, role, orgId))
  );

  const succeeded = results.filter((r) => r.status === 'fulfilled').length;
  const failed = results.filter((r) => r.status === 'rejected').length;
  console.log(`Assigned ${succeeded} roles, ${failed} failures`);
}
```

**Read roles from the JWT in application code:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Get the current user's role from their JWT
async function getCurrentUserRole(): Promise<AppRole | null> {
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) return null;

  return (user.app_metadata?.role as AppRole) ?? null;
}

// Get the current user's organization
async function getCurrentOrg(): Promise<string | null> {
  const { data: { user } } = await supabase.auth.getUser();
  return user?.app_metadata?.org_id ?? null;
}

// Check if current user has a specific role or higher
function hasRole(userRole: AppRole, requiredRole: AppRole): boolean {
  const hierarchy: Record<AppRole, number> = {
    admin: 4,
    editor: 3,
    member: 2,
    viewer: 1,
  };
  return hierarchy[userRole] >= hierarchy[requiredRole];
}

// Middleware-style role check for API routes
async function requireRole(requiredRole: AppRole) {
  const role = await getCurrentUserRole();
  if (!role || !hasRole(role, requiredRole)) {
    throw new Error(
      `Access denied: requires "${requiredRole}" role, user has "${role ?? 'none'}"`
    );
  }
}
```

### Step 2: RLS Policies with JWT Role Claims

Write Row Level Security policies that read `auth.jwt() ->> 'role'` and `auth.jwt() -> 'app_metadata' ->> 'org_id'` to enforce role-based and organization-scoped access.

**Role-based RLS policies:**

```sql
-- Create a helper function to extract role from JWT
CREATE OR REPLACE FUNCTION public.get_user_role()
RETURNS text AS $$
  SELECT coalesce(
    auth.jwt() -> 'app_metadata' ->> 'role',
    'viewer'  -- default role if not set
  );
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Create a helper function to extract org_id from JWT
CREATE OR REPLACE FUNCTION public.get_user_org_id()
RETURNS text AS $$
  SELECT auth.jwt() -> 'app_metadata' ->> 'org_id';
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Enable RLS on all tables
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_members ENABLE ROW LEVEL SECURITY;

-- Projects: org members can read, editors+ can create/update, admins can delete
CREATE POLICY "org_members_read_projects" ON public.projects
  FOR SELECT USING (
    org_id = get_user_org_id()
  );

CREATE POLICY "editors_create_projects" ON public.projects
  FOR INSERT WITH CHECK (
    org_id = get_user_org_id()
    AND get_user_role() IN ('admin', 'editor')
  );

CREATE POLICY "editors_update_projects" ON public.projects
  FOR UPDATE USING (
    org_id = get_user_org_id()
    AND get_user_role() IN ('admin', 'editor')
  );

CREATE POLICY "admins_delete_projects" ON public.projects
  FOR DELETE USING (
    org_id = get_user_org_id()
    AND get_user_role() = 'admin'
  );

-- Documents: org-scoped with role-based write access
CREATE POLICY "org_read_documents" ON public.documents
  FOR SELECT USING (
    org_id = get_user_org_id()
  );

CREATE POLICY "editors_write_documents" ON public.documents
  FOR INSERT WITH CHECK (
    org_id = get_user_org_id()
    AND get_user_role() IN ('admin', 'editor')
  );

CREATE POLICY "owner_or_admin_update_documents" ON public.documents
  FOR UPDATE USING (
    org_id = get_user_org_id()
    AND (
      created_by = auth.uid()
      OR get_user_role() = 'admin'
    )
  );

-- Team members: admins manage team, members can read
CREATE POLICY "org_read_team" ON public.team_members
  FOR SELECT USING (
    org_id = get_user_org_id()
  );

CREATE POLICY "admins_manage_team" ON public.team_members
  FOR ALL USING (
    org_id = get_user_org_id()
    AND get_user_role() = 'admin'
  );
```

**Organization-scoped access table schema:**

```sql
-- Organizations table
CREATE TABLE public.organizations (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Team members junction table
CREATE TABLE public.team_members (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  org_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'editor', 'member', 'viewer')),
  invited_by uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now(),
  UNIQUE(org_id, user_id)
);

-- Projects scoped to organizations
CREATE TABLE public.projects (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  org_id uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
  name text NOT NULL,
  created_by uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now()
);

-- Index for fast org-scoped queries
CREATE INDEX idx_team_members_org ON public.team_members(org_id);
CREATE INDEX idx_team_members_user ON public.team_members(user_id);
CREATE INDEX idx_projects_org ON public.projects(org_id);
```

### Step 3: API Key Scoping and Role Enforcement in Application Code

Enforce roles at the application layer to complement RLS, and scope API operations by role.

**Server-side role enforcement middleware:**

```typescript
import { createClient } from '@supabase/supabase-js';
import type { NextRequest } from 'next/server';

// Create a per-request client with the user's JWT
function createRequestClient(request: NextRequest) {
  const token = request.headers.get('Authorization')?.replace('Bearer ', '');

  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      global: {
        headers: { Authorization: `Bearer ${token}` },
      },
    }
  );
}

// Role enforcement for API routes
async function withRole(
  request: NextRequest,
  requiredRole: AppRole,
  handler: (supabase: ReturnType<typeof createClient>, user: any) => Promise<Response>
) {
  const supabase = createRequestClient(request);

  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const userRole = user.app_metadata?.role as AppRole;
  if (!userRole || !hasRole(userRole, requiredRole)) {
    return Response.json(
      { error: `Forbidden: requires "${requiredRole}" role` },
      { status: 403 }
    );
  }

  return handler(supabase, user);
}

// Usage in Next.js App Router
export async function DELETE(request: NextRequest) {
  return withRole(request, 'admin', async (supabase, user) => {
    const projectId = request.nextUrl.searchParams.get('id');

    const { error } = await supabase
      .from('projects')
      .delete()
      .eq('id', projectId);

    if (error) return Response.json({ error: error.message }, { status: 400 });
    return Response.json({ deleted: true });
  });
}
```

**Admin panel — manage user roles:**

```typescript
import { createClient } from '@supabase/supabase-js';

const adminClient = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

// List all users in an organization with their roles
async function listOrgMembers(orgId: string) {
  const { data, error } = await adminClient
    .from('team_members')
    .select(`
      user_id,
      role,
      created_at,
      profiles!inner(email, full_name)
    `)
    .eq('org_id', orgId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data;
}

// Invite a user to an organization
async function inviteToOrg(
  email: string,
  orgId: string,
  role: AppRole,
  invitedBy: string
) {
  // Create or get the user
  const { data: existingUsers } = await adminClient
    .from('profiles')
    .select('id')
    .eq('email', email)
    .single();

  const userId = existingUsers?.id;
  if (!userId) {
    // Send invite email via Supabase Auth
    const { error } = await adminClient.auth.admin.inviteUserByEmail(email, {
      data: { org_id: orgId, role },
    });
    if (error) throw error;
    return { status: 'invited' };
  }

  // Add existing user to org
  const { error } = await adminClient.from('team_members').insert({
    org_id: orgId,
    user_id: userId,
    role,
    invited_by: invitedBy,
  });

  if (error) throw error;

  // Update user's app_metadata with org and role
  await setUserRole(userId, role, orgId);

  return { status: 'added', userId };
}

// Change a user's role (admin only)
async function changeUserRole(
  orgId: string,
  targetUserId: string,
  newRole: AppRole
) {
  // Update team_members table
  const { error: dbError } = await adminClient
    .from('team_members')
    .update({ role: newRole })
    .eq('org_id', orgId)
    .eq('user_id', targetUserId);

  if (dbError) throw dbError;

  // Update JWT claims
  await setUserRole(targetUserId, newRole, orgId);

  console.log(`User ${targetUserId} role changed to "${newRole}" in org ${orgId}`);
}
```

## Output

After completing this skill, you will have:

- **Role assignment via app_metadata** — `admin.updateUserById()` sets role claims on user JWTs
- **JWT claim extraction** — `get_user_role()` and `get_user_org_id()` SQL helper functions
- **Role-based RLS policies** — SELECT/INSERT/UPDATE/DELETE scoped by role hierarchy (admin > editor > member > viewer)
- **Organization-scoped access** — multi-tenant isolation via `org_id` in JWT claims and RLS policies
- **Application-layer enforcement** — `withRole()` middleware for API routes with proper 401/403 responses
- **Admin panel operations** — list members, invite users, change roles with both database and JWT updates
- **Role hierarchy checking** — `hasRole()` function supporting role escalation comparison

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `app_metadata.role` is null in JWT | Role not set or user needs to re-login | Call `admin.updateUserById()` to set role; user must refresh their session |
| RLS policy returns empty results | JWT claims don't match policy conditions | Check `auth.jwt()` output in SQL Editor; verify `app_metadata` was set correctly |
| `permission denied for function` | Helper function not created or wrong schema | Create `get_user_role()` in the `public` schema with `SECURITY DEFINER` |
| User role changes not reflected | JWT cached with old claims | User must sign out and sign in again, or call `supabase.auth.refreshSession()` |
| `duplicate key value violates unique constraint` | User already in organization | Check `team_members` table for existing entry before inserting |
| `foreign key violation` on team_members | User or org doesn't exist | Verify both `user_id` and `org_id` exist before inserting membership |
| Role hierarchy bypass | Direct database access with service role | Service role bypasses RLS by design — restrict its use to server-side admin operations only |

## Examples

**Example 1 — Quick role check in a component:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, anonKey);

async function canEditProject(): Promise<boolean> {
  const { data: { user } } = await supabase.auth.getUser();
  const role = user?.app_metadata?.role;
  return role === 'admin' || role === 'editor';
}
```

**Example 2 — Verify RLS policies work correctly:**

```sql
-- Test as an editor in org-123
SET request.jwt.claims = '{"sub": "user-uuid", "role": "authenticated", "app_metadata": {"role": "editor", "org_id": "org-123"}}';

-- Should return only org-123 projects
SELECT * FROM projects;

-- Should succeed (editors can create)
INSERT INTO projects (org_id, name, created_by) VALUES ('org-123', 'Test', 'user-uuid');

-- Should fail (editors cannot delete)
DELETE FROM projects WHERE id = 'some-project-id';

RESET request.jwt.claims;
```

**Example 3 — Onboard a new organization:**

```typescript
async function onboardOrganization(orgName: string, adminEmail: string) {
  // 1. Create the organization
  const { data: org } = await adminClient
    .from('organizations')
    .insert({ name: orgName, slug: orgName.toLowerCase().replace(/\s+/g, '-') })
    .select('id')
    .single();

  // 2. Assign the creator as admin
  const { data: { users } } = await adminClient.auth.admin.listUsers();
  const adminUser = users.find((u) => u.email === adminEmail);

  if (adminUser && org) {
    await setUserRole(adminUser.id, 'admin', org.id);
    await adminClient.from('team_members').insert({
      org_id: org.id,
      user_id: adminUser.id,
      role: 'admin',
    });
  }

  return org;
}
```

## Resources

- [Custom Claims and RBAC — Supabase Docs](https://supabase.com/docs/guides/database/postgres/custom-claims-and-role-based-access-control-rbac)
- [Auth Admin updateUserById — Supabase Docs](https://supabase.com/docs/reference/javascript/auth-admin-updateuserbyid)
- [Row Level Security — Supabase Docs](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [auth.jwt() Function — Supabase Docs](https://supabase.com/docs/guides/database/postgres/row-level-security#helper-functions)
- [Multi-tenancy Patterns — Supabase Docs](https://supabase.com/docs/guides/getting-started/architecture#multi-tenancy)
- [inviteUserByEmail — Supabase Docs](https://supabase.com/docs/reference/javascript/auth-admin-inviteuserbyemail)

## Next Steps

- For database migration patterns, see `supabase-migration-deep-dive`
- For security hardening and API key scoping, see `supabase-security-basics`
- For data handling and GDPR compliance, see `supabase-data-handling`
