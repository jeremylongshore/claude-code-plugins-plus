# Clerk SDK Patterns - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Pattern 1: Server-Side Authentication
```typescript
// app/api/protected/route.ts
import { auth, currentUser } from '@clerk/nextjs/server'

export async function GET() {
  // Quick auth check
  const { userId, sessionId, orgId } = await auth()

  if (!userId) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Full user data when needed
  const user = await currentUser()

  return Response.json({
    userId,
    sessionId,
    orgId,
    email: user?.primaryEmailAddress?.emailAddress
  })
}
```

### Pattern 2: Client-Side Hooks
```typescript
'use client'
import { useUser, useAuth, useClerk, useSession } from '@clerk/nextjs'

export function AuthenticatedComponent() {
  // User data and loading state
  const { user, isLoaded, isSignedIn } = useUser()

  // Auth utilities
  const { userId, getToken, signOut } = useAuth()

  // Full Clerk instance
  const clerk = useClerk()

  // Session info
  const { session } = useSession()

  // Get JWT token for API calls
  const callExternalAPI = async () => {
    const token = await getToken({ template: 'supabase' }) // or custom template
    const res = await fetch('https://api.example.com', {
      headers: { Authorization: `Bearer ${token}` }
    })
  }

  if (!isLoaded) return <div>Loading...</div>
  if (!isSignedIn) return <div>Please sign in</div>

  return <div>Welcome, {user.firstName}</div>
}
```

### Pattern 3: Protected Routes with Middleware
```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks(.*)'
])

const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/api/protected(.*)'
])

export default clerkMiddleware(async (auth, request) => {
  if (isProtectedRoute(request)) {
    await auth.protect()
  }
})

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)']
}
```

### Pattern 4: Organization-Aware Queries
```typescript
import { auth } from '@clerk/nextjs/server'

export async function GET() {
  const { userId, orgId, orgRole } = await auth()

  // Check organization membership
  if (!orgId) {
    return Response.json({ error: 'No organization selected' }, { status: 400 })
  }

  // Check role-based access
  if (orgRole !== 'org:admin') {
    return Response.json({ error: 'Admin access required' }, { status: 403 })
  }

  // Query with organization scope
  const data = await db.query.resources.findMany({
    where: eq(resources.organizationId, orgId)
  })

  return Response.json(data)
}
```

### Pattern 5: Custom JWT Templates
```typescript
// Use custom JWT claims for external services
const { getToken } = useAuth()

// Standard Clerk token
const clerkToken = await getToken()

// Custom template for Supabase
const supabaseToken = await getToken({ template: 'supabase' })

// Custom template for Hasura
const hasuraToken = await getToken({ template: 'hasura' })
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| auth() returns null | Not in server context | Use in Server Components or API routes |
| useUser() not updating | Component not re-rendering | Check ClerkProvider placement |
| getToken() fails | Template not configured | Configure JWT template in dashboard |
| orgId is null | No organization selected | Prompt user to select organization |

## Examples

### Complete Protected Page Pattern
```typescript
// app/dashboard/page.tsx
import { auth, currentUser } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const { userId } = await auth()

  if (!userId) {
    redirect('/sign-in')
  }

  const user = await currentUser()

  return (
    <main>
      <h1>Dashboard</h1>
      <UserProfile user={user} />
      <DashboardContent userId={userId} />
    </main>
  )
}
```

### Typed User Metadata
```typescript
// types/clerk.d.ts
interface UserPublicMetadata {
  tier: 'free' | 'pro' | 'enterprise'
  onboarded: boolean
}

interface UserPrivateMetadata {
  stripeCustomerId?: string
}

// Usage
const user = await currentUser()
const tier = user?.publicMetadata?.tier ?? 'free'
```
