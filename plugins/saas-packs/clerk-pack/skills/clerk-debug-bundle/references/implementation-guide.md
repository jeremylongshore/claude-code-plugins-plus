# Clerk Debug Bundle - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Environment Debug Script
```typescript
// scripts/clerk-debug.ts
import { clerkClient } from '@clerk/nextjs/server'

async function collectDebugInfo() {
  const debug = {
    timestamp: new Date().toISOString(),
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      env: process.env.NODE_ENV
    },
    clerk: {
      publishableKey: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.substring(0, 20) + '...',
      hasSecretKey: !!process.env.CLERK_SECRET_KEY,
      signInUrl: process.env.NEXT_PUBLIC_CLERK_SIGN_IN_URL,
      signUpUrl: process.env.NEXT_PUBLIC_CLERK_SIGN_UP_URL
    },
    packages: {}
  }

  // Get package versions
  try {
    const pkg = require('../package.json')
    debug.packages = {
      '@clerk/nextjs': pkg.dependencies?.['@clerk/nextjs'],
      '@clerk/clerk-react': pkg.dependencies?.['@clerk/clerk-react'],
      'next': pkg.dependencies?.['next']
    }
  } catch {}

  console.log('=== CLERK DEBUG INFO ===')
  console.log(JSON.stringify(debug, null, 2))

  return debug
}

collectDebugInfo()
```

### Step 2: Runtime Health Check
```typescript
// app/api/clerk-health/route.ts
import { auth, currentUser, clerkClient } from '@clerk/nextjs/server'

export async function GET() {
  const health = {
    timestamp: new Date().toISOString(),
    status: 'checking',
    checks: {} as Record<string, any>
  }

  // Check 1: Auth function
  try {
    const authResult = await auth()
    health.checks.auth = {
      status: 'ok',
      hasUserId: !!authResult.userId,
      hasSessionId: !!authResult.sessionId
    }
  } catch (err: any) {
    health.checks.auth = { status: 'error', message: err.message }
  }

  // Check 2: Current user (if authenticated)
  try {
    const user = await currentUser()
    health.checks.currentUser = {
      status: 'ok',
      hasUser: !!user,
      userId: user?.id?.substring(0, 10) + '...'
    }
  } catch (err: any) {
    health.checks.currentUser = { status: 'error', message: err.message }
  }

  // Check 3: Clerk client
  try {
    const client = await clerkClient()
    const users = await client.users.getUserList({ limit: 1 })
    health.checks.clerkClient = {
      status: 'ok',
      canListUsers: true,
      totalUsers: users.totalCount
    }
  } catch (err: any) {
    health.checks.clerkClient = { status: 'error', message: err.message }
  }

  // Overall status
  const hasErrors = Object.values(health.checks).some(
    (c: any) => c.status === 'error'
  )
  health.status = hasErrors ? 'degraded' : 'healthy'

  return Response.json(health)
}
```

### Step 3: Client-Side Debug Component
```typescript
'use client'
import { useUser, useAuth, useSession, useClerk } from '@clerk/nextjs'
import { useState } from 'react'

export function ClerkDebugPanel() {
  const { user, isLoaded: userLoaded } = useUser()
  const { userId, sessionId, getToken } = useAuth()
  const { session } = useSession()
  const clerk = useClerk()
  const [tokenInfo, setTokenInfo] = useState<any>(null)

  const inspectToken = async () => {
    const token = await getToken()
    if (token) {
      const parts = token.split('.')
      const payload = JSON.parse(atob(parts[1]))
      setTokenInfo({
        length: token.length,
        expires: new Date(payload.exp * 1000).toISOString(),
        issued: new Date(payload.iat * 1000).toISOString(),
        subject: payload.sub
      })
    }
  }

  return (
    <div className="p-4 bg-gray-100 rounded font-mono text-sm">
      <h3 className="font-bold mb-2">Clerk Debug Panel</h3>

      <section className="mb-4">
        <h4 className="font-semibold">User State</h4>
        <pre>{JSON.stringify({
          loaded: userLoaded,
          userId: userId?.substring(0, 15),
          hasUser: !!user,
          email: user?.primaryEmailAddress?.emailAddress
        }, null, 2)}</pre>
      </section>

      <section className="mb-4">
        <h4 className="font-semibold">Session State</h4>
        <pre>{JSON.stringify({
          sessionId: sessionId?.substring(0, 15),
          status: session?.status,
          lastActive: session?.lastActiveAt
        }, null, 2)}</pre>
      </section>

      <section className="mb-4">
        <h4 className="font-semibold">Token Info</h4>
        <button onClick={inspectToken} className="bg-blue-500 text-white px-2 py-1 rounded mb-2">
          Inspect Token
        </button>
        {tokenInfo && <pre>{JSON.stringify(tokenInfo, null, 2)}</pre>}
      </section>

      <section>
        <h4 className="font-semibold">Clerk Version</h4>
        <pre>{JSON.stringify({
          version: clerk.version,
          loaded: clerk.loaded
        }, null, 2)}</pre>
      </section>
    </div>
  )
}
```

### Step 4: Request Debug Middleware
```typescript
// middleware.ts (add debug logging)
import { clerkMiddleware } from '@clerk/nextjs/server'

export default clerkMiddleware(async (auth, request) => {
  // Debug logging (remove in production)
  if (process.env.CLERK_DEBUG === 'true') {
    console.log('[Clerk Debug]', {
      path: request.nextUrl.pathname,
      method: request.method,
      headers: {
        cookie: request.headers.get('cookie')?.substring(0, 50),
        authorization: request.headers.get('authorization') ? 'present' : 'absent'
      }
    })

    const { userId, sessionId } = await auth()
    console.log('[Clerk Auth]', { userId, sessionId })
  }
})
```

### Step 5: Generate Support Bundle
```bash
#!/bin/bash
# scripts/clerk-support-bundle.sh

echo "=== Clerk Support Bundle ==="
echo "Generated: $(date)"
echo ""

echo "=== Environment ==="
echo "Node: $(node -v)"
echo "npm: $(npm -v)"
echo "OS: $(uname -a)"
echo ""

echo "=== Package Versions ==="
npm list @clerk/nextjs @clerk/clerk-react next react 2>/dev/null
echo ""

echo "=== Environment Variables (sanitized) ==="
echo "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: ${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY:0:20}..."
echo "CLERK_SECRET_KEY: $([ -n "$CLERK_SECRET_KEY" ] && echo "SET" || echo "NOT SET")"
echo ""

echo "=== Middleware Config ==="
cat middleware.ts 2>/dev/null || echo "No middleware.ts found"
echo ""

echo "=== Bundle Complete ==="
```

## Error Handling

| Issue | Debug Action |
|-------|--------------|
| Auth not working | Check /api/clerk-health endpoint |
| Token issues | Use debug panel to inspect token |
| Middleware problems | Enable CLERK_DEBUG=true |
| Session issues | Check session state in debug panel |
