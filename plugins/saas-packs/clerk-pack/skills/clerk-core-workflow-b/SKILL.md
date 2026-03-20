---
name: clerk-core-workflow-b
description: |
  Implement session management and middleware with Clerk.
  Use when managing user sessions, configuring route protection,
  or implementing token refresh logic.
  Trigger with phrases like "clerk session", "clerk middleware",
  "clerk route protection", "clerk token", "clerk JWT".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Core Workflow B: Session & Middleware

## Overview
Implement session management and route protection with Clerk middleware. Covers Next.js middleware configuration, API route protection, role-based access control, and organization-scoped sessions.

## Prerequisites
- Clerk account with application created
- `@clerk/nextjs` package installed
- Next.js 14+ with App Router
- Sign-in/sign-up flows working (`clerk-core-workflow-a` completed)

## Instructions

### Step 1: Configure Clerk Middleware
```typescript
// middleware.ts (project root)
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks(.*)',
])

const isAdminRoute = createRouteMatcher(['/admin(.*)'])

export default clerkMiddleware(async (auth, req) => {
  // Allow public routes
  if (isPublicRoute(req)) return

  // Require admin role for admin routes
  if (isAdminRoute(req)) {
    await auth.protect({ role: 'org:admin' })
    return
  }

  // Require authentication for all other routes
  await auth.protect()
})

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
}
```

### Step 2: Protect API Routes
```typescript
// app/api/data/route.ts
import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

export async function GET() {
  const { userId, orgId, has } = await auth()

  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Check specific permission
  if (!has({ permission: 'org:data:read' })) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  return NextResponse.json({
    data: 'Protected content',
    userId,
    orgId,
  })
}
```

### Step 3: Handle Session Claims and JWT
```typescript
// app/api/external/route.ts
import { auth } from '@clerk/nextjs/server'

export async function GET() {
  const { userId, getToken, sessionClaims } = await auth()

  // Get custom JWT for external service (e.g., Supabase)
  const supabaseToken = await getToken({ template: 'supabase' })

  // Access session claims
  const userRole = sessionClaims?.metadata?.role

  return Response.json({
    userId,
    role: userRole,
    hasSupabaseToken: !!supabaseToken,
  })
}
```

### Step 4: Server Component Auth
```typescript
// app/dashboard/page.tsx
import { auth, currentUser } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const { userId, has } = await auth()

  if (!userId) redirect('/sign-in')

  const user = await currentUser()
  const isAdmin = has({ role: 'org:admin' })

  return (
    <div>
      <h1>Welcome, {user?.firstName}</h1>
      {isAdmin && <a href="/admin">Admin Panel</a>}
    </div>
  )
}
```

### Step 5: Organization-Scoped Sessions
```typescript
'use client'
import { useOrganizationList, useOrganization } from '@clerk/nextjs'

export function OrgSwitcher() {
  const { organizationList, setActive } = useOrganizationList()
  const { organization } = useOrganization()

  return (
    <div>
      <p>Current: {organization?.name || 'Personal'}</p>
      <ul>
        {organizationList?.map(({ organization: org }) => (
          <li key={org.id}>
            <button onClick={() => setActive({ organization: org.id })}>
              {org.name}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

## Output
- Middleware protecting all non-public routes
- API routes with auth and permission checks
- Server components with role-based rendering
- JWT tokens configured for external services
- Organization-scoped session switching

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Middleware redirect loop | Public route not in matcher | Add route to `isPublicRoute` |
| 401 on API route | Token not forwarded | Ensure fetch includes credentials |
| Missing org context | User not in organization | Check `orgId` before org-scoped ops |
| Session expired | Token TTL exceeded | Configure session lifetime in dashboard |
| `has()` returns false | Permission not assigned | Check role in Clerk Dashboard > Organizations |

## Examples

### Quick Permission Check
```typescript
// Inline permission guard for server actions
import { auth } from '@clerk/nextjs/server'

export async function deleteItem(itemId: string) {
  const { has } = await auth()
  if (!has({ permission: 'org:items:delete' })) {
    throw new Error('Permission denied')
  }
  // proceed with deletion
}
```

## Resources
- [Clerk Middleware](https://clerk.com/docs/references/nextjs/clerk-middleware)
- [Auth Helper](https://clerk.com/docs/references/nextjs/auth)
- [Organizations](https://clerk.com/docs/organizations/overview)

## Next Steps
Proceed to `clerk-webhooks-events` for webhook and event handling.
