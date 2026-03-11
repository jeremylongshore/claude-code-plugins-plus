# Clerk Enterprise RBAC - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Configure SAML SSO

#### In Clerk Dashboard
1. Go to Configure > SSO Connections
2. Add SAML Connection
3. Configure IdP settings:
   - ACS URL: `https://clerk.yourapp.com/v1/saml`
   - Entity ID: Provided by Clerk
   - Download SP metadata

#### IdP Configuration (Example: Okta)
```xml
<!-- SAML Attributes to map -->
<saml:Attribute Name="email">
  <saml:AttributeValue>user.email</saml:AttributeValue>
</saml:Attribute>
<saml:Attribute Name="firstName">
  <saml:AttributeValue>user.firstName</saml:AttributeValue>
</saml:Attribute>
<saml:Attribute Name="lastName">
  <saml:AttributeValue>user.lastName</saml:AttributeValue>
</saml:Attribute>
<saml:Attribute Name="role">
  <saml:AttributeValue>user.role</saml:AttributeValue>
</saml:Attribute>
```

### Step 2: Define Roles and Permissions
```typescript
// lib/permissions.ts

// Define all permissions in your system
export const PERMISSIONS = {
  // Resource: Action
  'users:read': 'View user list',
  'users:write': 'Create/update users',
  'users:delete': 'Delete users',
  'settings:read': 'View settings',
  'settings:write': 'Modify settings',
  'billing:read': 'View billing info',
  'billing:write': 'Manage billing',
  'reports:read': 'View reports',
  'reports:export': 'Export reports'
} as const

export type Permission = keyof typeof PERMISSIONS

// Define roles with their permissions
export const ROLES = {
  'org:admin': [
    'users:read', 'users:write', 'users:delete',
    'settings:read', 'settings:write',
    'billing:read', 'billing:write',
    'reports:read', 'reports:export'
  ],
  'org:manager': [
    'users:read', 'users:write',
    'settings:read',
    'reports:read', 'reports:export'
  ],
  'org:member': [
    'users:read',
    'reports:read'
  ],
  'org:viewer': [
    'reports:read'
  ]
} as const satisfies Record<string, Permission[]>

export type Role = keyof typeof ROLES
```

### Step 3: Permission Checking
```typescript
// lib/auth-permissions.ts
import { auth } from '@clerk/nextjs/server'
import { ROLES, Permission, Role } from './permissions'

export async function hasPermission(permission: Permission): Promise<boolean> {
  const { orgRole } = await auth()

  if (!orgRole) return false

  const role = orgRole as Role
  const rolePermissions = ROLES[role]

  if (!rolePermissions) return false

  return rolePermissions.includes(permission)
}

export async function requirePermission(permission: Permission): Promise<void> {
  const allowed = await hasPermission(permission)

  if (!allowed) {
    throw new Error(`Permission denied: ${permission}`)
  }
}

// Decorator pattern for API routes
export function withPermission(permission: Permission) {
  return async function(
    handler: (req: Request) => Promise<Response>
  ): Promise<(req: Request) => Promise<Response>> {
    return async (req: Request) => {
      const allowed = await hasPermission(permission)

      if (!allowed) {
        return Response.json(
          { error: 'Permission denied', required: permission },
          { status: 403 }
        )
      }

      return handler(req)
    }
  }
}
```

### Step 4: Protected Routes with RBAC
```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

const isPublicRoute = createRouteMatcher(['/', '/sign-in(.*)', '/sign-up(.*)'])
const isAdminRoute = createRouteMatcher(['/admin(.*)'])
const isBillingRoute = createRouteMatcher(['/billing(.*)'])

export default clerkMiddleware(async (auth, request) => {
  const { userId, orgRole } = await auth()

  if (isPublicRoute(request)) {
    return NextResponse.next()
  }

  if (!userId) {
    return auth.redirectToSignIn()
  }

  // Admin routes require admin role
  if (isAdminRoute(request)) {
    if (orgRole !== 'org:admin') {
      return NextResponse.redirect(new URL('/unauthorized', request.url))
    }
  }

  // Billing routes require admin or manager
  if (isBillingRoute(request)) {
    if (!['org:admin', 'org:manager'].includes(orgRole || '')) {
      return NextResponse.redirect(new URL('/unauthorized', request.url))
    }
  }

  return NextResponse.next()
})
```

### Step 5: Organization Management
```typescript
// lib/organization.ts
import { clerkClient, auth } from '@clerk/nextjs/server'

export async function createOrganization(name: string, slug: string) {
  const { userId } = await auth()
  const client = await clerkClient()

  const org = await client.organizations.createOrganization({
    name,
    slug,
    createdBy: userId!
  })

  return org
}

export async function inviteToOrganization(
  orgId: string,
  email: string,
  role: string
) {
  const client = await clerkClient()

  const invitation = await client.organizations.createOrganizationInvitation({
    organizationId: orgId,
    emailAddress: email,
    role,
    inviterUserId: (await auth()).userId!
  })

  return invitation
}

export async function updateMemberRole(
  orgId: string,
  userId: string,
  role: string
) {
  const client = await clerkClient()

  await client.organizations.updateOrganizationMembership({
    organizationId: orgId,
    userId,
    role
  })
}

export async function getOrganizationMembers(orgId: string) {
  const client = await clerkClient()

  const { data: members } = await client.organizations.getOrganizationMembershipList({
    organizationId: orgId
  })

  return members
}
```

### Step 6: React Components with RBAC
```typescript
// components/permission-gate.tsx
'use client'
import { useAuth, useOrganization } from '@clerk/nextjs'
import { ROLES, Permission, Role } from '@/lib/permissions'

interface PermissionGateProps {
  permission: Permission
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function PermissionGate({
  permission,
  children,
  fallback = null
}: PermissionGateProps) {
  const { orgRole } = useAuth()

  if (!orgRole) return fallback

  const role = orgRole as Role
  const permissions = ROLES[role] || []

  if (!permissions.includes(permission)) {
    return fallback
  }

  return <>{children}</>
}

// Usage
function AdminPanel() {
  return (
    <div>
      <h1>Dashboard</h1>

      <PermissionGate permission="users:write">
        <button>Add User</button>
      </PermissionGate>

      <PermissionGate permission="billing:read">
        <BillingSection />
      </PermissionGate>

      <PermissionGate
        permission="settings:write"
        fallback={<p>Contact admin for settings access</p>}
      >
        <SettingsForm />
      </PermissionGate>
    </div>
  )
}
```

### Step 7: API Route Protection
```typescript
// app/api/admin/users/route.ts
import { auth } from '@clerk/nextjs/server'
import { hasPermission } from '@/lib/auth-permissions'

export async function GET() {
  const { userId, orgId } = await auth()

  if (!userId || !orgId) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!await hasPermission('users:read')) {
    return Response.json({ error: 'Forbidden' }, { status: 403 })
  }

  // Fetch users scoped to organization
  const users = await db.user.findMany({
    where: { organizationId: orgId }
  })

  return Response.json(users)
}

export async function POST(request: Request) {
  const { userId, orgId } = await auth()

  if (!userId || !orgId) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!await hasPermission('users:write')) {
    return Response.json({ error: 'Forbidden' }, { status: 403 })
  }

  const data = await request.json()

  const user = await db.user.create({
    data: {
      ...data,
      organizationId: orgId,
      createdBy: userId
    }
  })

  return Response.json(user)
}
```

## SSO Configuration Matrix

| IdP | Protocol | Setup Guide |
|-----|----------|-------------|
| Okta | SAML 2.0 | Clerk Dashboard > SSO |
| Azure AD | OIDC/SAML | Clerk Dashboard > SSO |
| Google Workspace | OIDC | Clerk Dashboard > SSO |
| OneLogin | SAML 2.0 | Clerk Dashboard > SSO |
