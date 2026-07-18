# Role Assignment via app_metadata and JWT Claims

Store custom roles in the user's `app_metadata` using the Admin API. These claims appear in every JWT the user receives and are available in RLS policies.

## Set user roles with the Admin API

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

## Read roles from the JWT in application code

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
