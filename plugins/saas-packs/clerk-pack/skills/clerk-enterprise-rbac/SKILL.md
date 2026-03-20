---
name: clerk-enterprise-rbac
description: |
  Configure enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls.
  Trigger with phrases like "clerk SSO", "clerk RBAC",
  "clerk enterprise", "clerk roles", "clerk permissions", "clerk SAML".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Enterprise RBAC

## Overview
Implement enterprise-grade SSO, role-based access control, and organization management with Clerk. Covers SAML SSO, custom roles and permissions, organization lifecycle, and multi-tenant access patterns.

## Prerequisites
- Clerk Pro or Enterprise plan (SSO requires paid plan)
- Identity Provider (IdP) with SAML/OIDC support (Okta, Azure AD, Google Workspace)
- Organization feature enabled in Clerk Dashboard

## Instructions

### Step 1: Enable Organizations
Enable Organizations in Clerk Dashboard > Organizations > Settings. Then add the UI component:

```typescript
// app/org-selector/page.tsx
import { OrganizationSwitcher, OrganizationProfile } from '@clerk/nextjs'

export default function OrgPage() {
  return (
    <div>
      <OrganizationSwitcher hidePersonal={false} />
      <OrganizationProfile />
    </div>
  )
}
```

### Step 2: Define Roles and Permissions
Configure in Clerk Dashboard > Organizations > Roles. Common setup:

| Role | Permissions | Description |
|------|-------------|-------------|
| `org:admin` | `org:members:manage`, `org:settings:manage`, `org:data:write` | Full org control |
| `org:manager` | `org:data:write`, `org:data:read`, `org:members:read` | Content management |
| `org:member` | `org:data:read` | Read-only access |

### Step 3: Permission Checking in Server Components
```typescript
// app/admin/page.tsx
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'

export default async function AdminPage() {
  const { userId, orgId, has } = await auth()

  if (!userId) redirect('/sign-in')
  if (!orgId) redirect('/org-selector')

  const canManageMembers = has({ permission: 'org:members:manage' })
  const canManageSettings = has({ permission: 'org:settings:manage' })

  return (
    <div>
      <h1>Admin Panel</h1>
      {canManageMembers && <a href="/admin/members">Manage Members</a>}
      {canManageSettings && <a href="/admin/settings">Organization Settings</a>}
    </div>
  )
}
```

### Step 4: RBAC Middleware
```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isAdminRoute = createRouteMatcher(['/admin(.*)'])
const isManagerRoute = createRouteMatcher(['/manage(.*)'])

export default clerkMiddleware(async (auth, req) => {
  if (isAdminRoute(req)) {
    await auth.protect({ role: 'org:admin' })
  } else if (isManagerRoute(req)) {
    await auth.protect((has) => has({ role: 'org:admin' }) || has({ role: 'org:manager' }))
  }
})
```

### Step 5: Organization Management API
```typescript
// app/api/org/members/route.ts
import { auth, clerkClient } from '@clerk/nextjs/server'

export async function GET() {
  const { orgId, has } = await auth()
  if (!orgId || !has({ permission: 'org:members:read' })) {
    return Response.json({ error: 'Forbidden' }, { status: 403 })
  }

  const client = await clerkClient()
  const members = await client.organizations.getOrganizationMembershipList({
    organizationId: orgId,
  })

  return Response.json({ members: members.data })
}

export async function POST(req: Request) {
  const { orgId, has } = await auth()
  if (!orgId || !has({ permission: 'org:members:manage' })) {
    return Response.json({ error: 'Forbidden' }, { status: 403 })
  }

  const { emailAddress, role } = await req.json()
  const client = await clerkClient()
  const invitation = await client.organizations.createOrganizationInvitation({
    organizationId: orgId,
    emailAddress,
    role,
    inviterUserId: (await auth()).userId!,
  })

  return Response.json({ invitation })
}
```

### Step 6: React Components with RBAC
```typescript
'use client'
import { Protect, useOrganization } from '@clerk/nextjs'

export function AdminSection() {
  const { organization } = useOrganization()

  return (
    <div>
      <h2>{organization?.name}</h2>

      {/* Only render for users with admin role */}
      <Protect role="org:admin" fallback={<p>Admin access required</p>}>
        <DangerZone />
      </Protect>

      {/* Permission-based rendering */}
      <Protect permission="org:data:write">
        <EditForm />
      </Protect>
    </div>
  )
}
```

## Output
- Organizations enabled with role hierarchy (admin, manager, member)
- RBAC middleware enforcing role-based route protection
- Server-side and client-side permission checks
- Organization member management API
- Invitation system for adding members

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| SSO login fails | Misconfigured IdP metadata | Verify ACS URL and Entity ID in IdP settings |
| Permission denied | Role missing or wrong org | Check role assignment in Dashboard > Organizations |
| `orgId` is null | User has no active org | Redirect to org selector, show `<OrganizationSwitcher />` |
| Invitation fails | Email already in org | Check existing membership before inviting |

## Examples

### Custom SAML SSO Configuration
Configure in Clerk Dashboard > SSO Connections > Add SAML Connection:
1. Set **ACS URL**: `https://your-clerk-domain.clerk.accounts.dev/v1/saml/acs`
2. Set **Entity ID**: `https://your-clerk-domain.clerk.accounts.dev/v1/saml/metadata`
3. Upload IdP metadata XML from your provider (Okta, Azure AD)
4. Map attributes: `email`, `firstName`, `lastName`

## Resources
- [Clerk Organizations](https://clerk.com/docs/organizations/overview)
- [Roles & Permissions](https://clerk.com/docs/organizations/roles-permissions)
- [SAML SSO Guide](https://clerk.com/docs/authentication/saml/overview)

## Next Steps
Proceed to `clerk-migration-deep-dive` for auth provider migration.
