# Clerk Performance Tuning - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Optimize Middleware
```typescript
// middleware.ts - Optimized configuration
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

// Pre-compile route matchers (done once at startup)
const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/public(.*)',
  '/api/webhooks(.*)'
])

// Exclude static files from middleware processing
export const config = {
  matcher: [
    // Skip all static files and images
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)'
  ]
}

export default clerkMiddleware(async (auth, request) => {
  // Quick return for public routes
  if (isPublicRoute(request)) {
    return
  }

  // Protect other routes
  await auth.protect()
})
```

### Step 2: Implement User Data Caching
```typescript
// lib/cached-user.ts
import { unstable_cache } from 'next/cache'
import { clerkClient, currentUser } from '@clerk/nextjs/server'

// Cache user data with Next.js cache
export const getCachedUser = unstable_cache(
  async (userId: string) => {
    const client = await clerkClient()
    return client.users.getUser(userId)
  },
  ['user-data'],
  {
    revalidate: 60, // 1 minute cache
    tags: ['users']
  }
)

// In-memory cache for very frequent lookups
const userCache = new Map<string, { data: any; expiry: number }>()

export async function getUserFast(userId: string) {
  const cached = userCache.get(userId)
  const now = Date.now()

  if (cached && cached.expiry > now) {
    return cached.data
  }

  const user = await getCachedUser(userId)
  userCache.set(userId, {
    data: user,
    expiry: now + 30000 // 30 seconds
  })

  return user
}

// Invalidate cache on user update
export function invalidateUserCache(userId: string) {
  userCache.delete(userId)
}
```

### Step 3: Optimize Token Handling
```typescript
// lib/optimized-auth.ts
'use client'
import { useAuth } from '@clerk/nextjs'
import { useRef } from 'react'

// Cache tokens to avoid repeated async calls
export function useOptimizedAuth() {
  const { getToken, userId, isLoaded } = useAuth()
  const tokenCache = useRef<{
    token: string | null
    expiry: number
  } | null>(null)

  const getCachedToken = async () => {
    const now = Date.now()

    // Return cached token if still valid (with 5 min buffer)
    if (tokenCache.current &&
        tokenCache.current.token &&
        tokenCache.current.expiry > now + 300000) {
      return tokenCache.current.token
    }

    // Get fresh token
    const token = await getToken()

    if (token) {
      // Parse expiry from JWT
      const payload = JSON.parse(atob(token.split('.')[1]))
      tokenCache.current = {
        token,
        expiry: payload.exp * 1000
      }
    }

    return token
  }

  return { getCachedToken, userId, isLoaded }
}

// Optimized fetch with token
export function useAuthFetch() {
  const { getCachedToken } = useOptimizedAuth()

  return async (url: string, options: RequestInit = {}) => {
    const token = await getCachedToken()

    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
  }
}
```

### Step 4: Lazy Load Auth Components
```typescript
// components/lazy-auth.tsx
'use client'
import dynamic from 'next/dynamic'
import { Suspense } from 'react'

// Lazy load heavy auth components
const UserButton = dynamic(
  () => import('@clerk/nextjs').then(mod => mod.UserButton),
  {
    loading: () => <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse" />,
    ssr: false
  }
)

const SignInButton = dynamic(
  () => import('@clerk/nextjs').then(mod => mod.SignInButton),
  {
    loading: () => <button className="btn" disabled>Sign In</button>,
    ssr: false
  }
)

export function LazyUserButton() {
  return (
    <Suspense fallback={<div className="w-8 h-8 bg-gray-200 rounded-full" />}>
      <UserButton afterSignOutUrl="/" />
    </Suspense>
  )
}
```

### Step 5: Optimize Server Components
```typescript
// app/dashboard/page.tsx
import { auth } from '@clerk/nextjs/server'
import { Suspense } from 'react'

// Use streaming for auth-dependent content
export default async function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>

      {/* Stream user-specific content */}
      <Suspense fallback={<UserDataSkeleton />}>
        <UserData />
      </Suspense>

      {/* Non-auth content renders immediately */}
      <StaticContent />
    </div>
  )
}

async function UserData() {
  const { userId } = await auth()

  // Parallel data fetching
  const [user, stats, notifications] = await Promise.all([
    getUser(userId!),
    getUserStats(userId!),
    getNotifications(userId!)
  ])

  return (
    <div>
      <UserProfile user={user} />
      <UserStats stats={stats} />
      <Notifications items={notifications} />
    </div>
  )
}
```

### Step 6: Edge Runtime Optimization
```typescript
// app/api/fast-auth/route.ts
import { auth } from '@clerk/nextjs/server'

// Use Edge runtime for faster cold starts
export const runtime = 'edge'

export async function GET() {
  const { userId } = await auth()

  if (!userId) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Edge-compatible response
  return Response.json({ userId })
}
```

## Performance Metrics

| Operation | Target | Optimization |
|-----------|--------|--------------|
| Middleware check | < 10ms | Route matcher pre-compilation |
| Token validation | < 50ms | JWT caching |
| User fetch | < 100ms | Multi-level caching |
| Page load (auth) | < 200ms | Streaming + lazy load |

## Monitoring

```typescript
// lib/performance-monitor.ts
export function measureAuthPerformance<T>(
  name: string,
  operation: () => Promise<T>
): Promise<T> {
  const start = performance.now()

  return operation().finally(() => {
    const duration = performance.now() - start
    console.log(`[Clerk Perf] ${name}: ${duration.toFixed(2)}ms`)

    // Send to monitoring (DataDog, etc.)
    if (duration > 100) {
      console.warn(`[Clerk Perf] Slow operation: ${name}`)
    }
  })
}

// Usage
const user = await measureAuthPerformance('getUser', () =>
  clerkClient.users.getUser(userId)
)
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Slow page loads | Blocking auth calls | Use Suspense boundaries |
| High latency | No caching | Implement token/user cache |
| Bundle size | All components loaded | Lazy load auth components |
| Cold starts | Node runtime | Use Edge runtime |
