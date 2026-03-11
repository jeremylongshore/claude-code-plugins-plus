---
name: clerk-hello-world
description: |
  Create your first authenticated request with Clerk.
  Use when making initial API calls, testing authentication,
  or verifying Clerk integration works correctly.
  Trigger with phrases like "clerk hello world", "first clerk request",
  "test clerk auth", "verify clerk setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Hello World

## Overview
Make your first authenticated request using Clerk to verify the integration works.

## Prerequisites
- Clerk SDK installed (`clerk-install-auth` completed)
- Environment variables configured
- ClerkProvider wrapping application

## Instructions

### Step 1: Create Protected Page
```typescript
// app/dashboard/page.tsx
import { auth, currentUser } from '@clerk/nextjs/server'

export default async function DashboardPage() {
  const { userId } = await auth()
  const user = await currentUser()

  if (!userId) {
    return <div>Please sign in to access this page</div>
  }

  return (
    <div>
      <h1>Hello, {user?.firstName || 'User'}!</h1>
      <p>Your user ID: {userId}</p>
      <p>Email: {user?.emailAddresses[0]?.emailAddress}</p>
    </div>
  )
}
```

### Step 2: Create Protected API Route
```typescript
// app/api/hello/route.ts
import { auth } from '@clerk/nextjs/server'

export async function GET() {
  const { userId } = await auth()

  if (!userId) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })  # HTTP 401 Unauthorized
  }

  return Response.json({
    message: 'Hello from Clerk!',
    userId,
    timestamp: new Date().toISOString()
  })
}
```

### Step 3: Test Authentication Flow
```typescript
// Client-side test component
'use client'
import { useUser, useAuth } from '@clerk/nextjs'

export function AuthTest() {
  const { user, isLoaded, isSignedIn } = useUser()
  const { getToken } = useAuth()

  if (!isLoaded) return <div>Loading...</div>
  if (!isSignedIn) return <div>Not signed in</div>

  const testAPI = async () => {
    const token = await getToken()
    const res = await fetch('/api/hello', {
      headers: { Authorization: `Bearer ${token}` }
    })
    console.log(await res.json())
  }

  return (
    <div>
      <p>Signed in as: {user.primaryEmailAddress?.emailAddress}</p>
      <button onClick={testAPI}>Test API</button>
    </div>
  )
}
```

## Output
- Protected page showing user information
- API route returning authenticated user data
- Successful request/response verification

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| userId is null | User not authenticated | Redirect to sign-in or check middleware |
| currentUser returns null | Session expired | Refresh page or re-authenticate |
| 401 Unauthorized | Token missing or invalid | Check Authorization header |
| Hydration Error | Server/client mismatch | Use 'use client' for client hooks |

## Examples

### Using with React Hooks
```typescript
'use client'
import { useUser, useClerk } from '@clerk/nextjs'

export function UserProfile() {
  const { user } = useUser()
  const { signOut } = useClerk()

  return (
    <div>
      <img src={user?.imageUrl} alt="Profile" />
      <h2>{user?.fullName}</h2>
      <button onClick={() => signOut()}>Sign Out</button>
    </div>
  )
}
```

### Express.js Example
```typescript
import { clerkMiddleware, requireAuth } from '@clerk/express'

app.use(clerkMiddleware())

app.get('/api/protected', requireAuth(), (req, res) => {
  res.json({
    message: 'Hello!',
    userId: req.auth.userId
  })
})
```

## Resources
- [Clerk Auth Object](https://clerk.com/docs/references/nextjs/auth)
- [Clerk Hooks](https://clerk.com/docs/references/react/use-user)
- [Protected Routes](https://clerk.com/docs/references/nextjs/auth-middleware)

## Next Steps
Proceed to `clerk-local-dev-loop` for local development workflow setup.