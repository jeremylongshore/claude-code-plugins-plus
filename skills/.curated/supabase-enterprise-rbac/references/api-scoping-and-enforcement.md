# API Key Scoping and Role Enforcement

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
