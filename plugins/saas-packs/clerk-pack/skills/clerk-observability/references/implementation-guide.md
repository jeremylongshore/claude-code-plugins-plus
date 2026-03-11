# Clerk Observability - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Authentication Event Logging
```typescript
// lib/auth-logger.ts
import { auth, currentUser } from '@clerk/nextjs/server'

interface AuthEvent {
  type: string
  userId: string | null
  timestamp: string
  metadata: Record<string, any>
}

class AuthLogger {
  private events: AuthEvent[] = []

  log(type: string, metadata: Record<string, any> = {}) {
    const event: AuthEvent = {
      type,
      userId: null, // Set after auth
      timestamp: new Date().toISOString(),
      metadata
    }

    this.events.push(event)
    console.log('[Auth Event]', JSON.stringify(event))

    // Send to monitoring service
    this.sendToMonitoring(event)
  }

  async logWithAuth(type: string, metadata: Record<string, any> = {}) {
    const { userId, sessionId } = await auth()

    const event: AuthEvent = {
      type,
      userId,
      timestamp: new Date().toISOString(),
      metadata: {
        ...metadata,
        sessionId,
        hasUser: !!userId
      }
    }

    this.events.push(event)
    console.log('[Auth Event]', JSON.stringify(event))
    this.sendToMonitoring(event)
  }

  private sendToMonitoring(event: AuthEvent) {
    // DataDog example
    if (process.env.DD_API_KEY) {
      fetch('https://http-intake.logs.datadoghq.com/v1/input', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'DD-API-KEY': process.env.DD_API_KEY
        },
        body: JSON.stringify({
          ddsource: 'clerk',
          ddtags: 'env:production',
          message: event
        })
      }).catch(console.error)
    }
  }
}

export const authLogger = new AuthLogger()
```

### Step 2: Middleware Monitoring
```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

const isPublicRoute = createRouteMatcher(['/', '/sign-in(.*)', '/sign-up(.*)'])

export default clerkMiddleware(async (auth, request) => {
  const start = performance.now()
  const { userId, sessionId } = await auth()

  // Log auth check
  const authDuration = performance.now() - start

  // Add monitoring headers
  const response = NextResponse.next()
  response.headers.set('x-auth-duration', String(authDuration.toFixed(2)))
  response.headers.set('x-auth-user', userId || 'anonymous')

  // Log slow auth
  if (authDuration > 100) {
    console.warn('[Clerk Perf] Slow auth check:', {
      duration: authDuration,
      path: request.nextUrl.pathname,
      userId
    })
  }

  // Metrics
  recordMetric('clerk.auth.duration', authDuration)
  recordMetric('clerk.auth.success', userId ? 1 : 0)

  return response
})

function recordMetric(name: string, value: number) {
  // Send to your metrics provider
  console.log(`[Metric] ${name}: ${value}`)
}
```

### Step 3: Session Analytics
```typescript
// lib/session-analytics.ts
import { clerkClient } from '@clerk/nextjs/server'

interface SessionMetrics {
  totalSessions: number
  activeSessions: number
  averageSessionDuration: number
  sessionsByDevice: Record<string, number>
}

export async function getSessionMetrics(userId: string): Promise<SessionMetrics> {
  const client = await clerkClient()

  const sessions = await client.sessions.getSessionList({
    userId,
    status: 'active'
  })

  const sessionsByDevice: Record<string, number> = {}
  let totalDuration = 0

  for (const session of sessions.data) {
    // Parse user agent for device type
    const device = parseDeviceType(session.userAgent || '')
    sessionsByDevice[device] = (sessionsByDevice[device] || 0) + 1

    // Calculate duration
    const duration = Date.now() - new Date(session.createdAt).getTime()
    totalDuration += duration
  }

  return {
    totalSessions: sessions.totalCount,
    activeSessions: sessions.data.length,
    averageSessionDuration: totalDuration / sessions.data.length || 0,
    sessionsByDevice
  }
}

function parseDeviceType(userAgent: string): string {
  if (/mobile/i.test(userAgent)) return 'mobile'
  if (/tablet/i.test(userAgent)) return 'tablet'
  return 'desktop'
}
```

### Step 4: Webhook Event Tracking
```typescript
// app/api/webhooks/clerk/route.ts
import { Webhook } from 'svix'
import { headers } from 'next/headers'
import { WebhookEvent } from '@clerk/nextjs/server'

const webhookMetrics = {
  received: 0,
  processed: 0,
  failed: 0,
  byType: {} as Record<string, number>
}

export async function POST(req: Request) {
  webhookMetrics.received++

  const start = performance.now()
  const headerPayload = await headers()
  const svix_id = headerPayload.get('svix-id')!

  // ... verification code ...

  try {
    const evt = wh.verify(body, headers) as WebhookEvent
    const eventType = evt.type

    // Track by type
    webhookMetrics.byType[eventType] = (webhookMetrics.byType[eventType] || 0) + 1

    // Process event
    await processEvent(evt)

    webhookMetrics.processed++

    // Log success
    console.log('[Webhook]', {
      type: eventType,
      id: svix_id,
      duration: performance.now() - start,
      status: 'success'
    })

    return Response.json({ success: true })
  } catch (error) {
    webhookMetrics.failed++

    console.error('[Webhook Error]', {
      id: svix_id,
      error: error.message,
      duration: performance.now() - start
    })

    return Response.json({ error: 'Processing failed' }, { status: 500 })
  }
}

// Expose metrics endpoint
export async function GET() {
  return Response.json(webhookMetrics)
}
```

### Step 5: Error Tracking with Sentry
```typescript
// lib/sentry-clerk.ts
import * as Sentry from '@sentry/nextjs'
import { auth, currentUser } from '@clerk/nextjs/server'

export async function initSentryWithClerk() {
  const { userId, orgId } = await auth()

  if (userId) {
    Sentry.setUser({
      id: userId,
      // Don't include email unless necessary for privacy
    })

    Sentry.setContext('clerk', {
      userId,
      orgId,
      hasOrg: !!orgId
    })
  }
}

// Wrapper for auth operations with error tracking
export async function withAuthErrorTracking<T>(
  operation: () => Promise<T>,
  context: string
): Promise<T> {
  try {
    return await operation()
  } catch (error) {
    Sentry.captureException(error, {
      tags: {
        component: 'clerk',
        operation: context
      }
    })
    throw error
  }
}

// Usage
const user = await withAuthErrorTracking(
  () => currentUser(),
  'get-current-user'
)
```

### Step 6: Health Check Endpoint
```typescript
// app/api/health/clerk/route.ts
import { auth, clerkClient } from '@clerk/nextjs/server'

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  checks: {
    auth: { status: string; latency: number }
    api: { status: string; latency: number }
    webhooks: { status: string; lastReceived: string | null }
  }
  timestamp: string
}

export async function GET() {
  const health: HealthStatus = {
    status: 'healthy',
    checks: {
      auth: { status: 'unknown', latency: 0 },
      api: { status: 'unknown', latency: 0 },
      webhooks: { status: 'unknown', lastReceived: null }
    },
    timestamp: new Date().toISOString()
  }

  // Check auth function
  const authStart = performance.now()
  try {
    await auth()
    health.checks.auth = {
      status: 'ok',
      latency: performance.now() - authStart
    }
  } catch {
    health.checks.auth = {
      status: 'error',
      latency: performance.now() - authStart
    }
    health.status = 'degraded'
  }

  // Check API connectivity
  const apiStart = performance.now()
  try {
    const client = await clerkClient()
    await client.users.getUserList({ limit: 1 })
    health.checks.api = {
      status: 'ok',
      latency: performance.now() - apiStart
    }
  } catch {
    health.checks.api = {
      status: 'error',
      latency: performance.now() - apiStart
    }
    health.status = 'unhealthy'
  }

  return Response.json(health)
}
```

## Dashboard Metrics

Track these key metrics:
- Authentication success/failure rate
- Auth latency (p50, p95, p99)
- Active sessions over time
- Webhook processing time
- Error rate by type

## Error Handling

| Issue | Monitoring Action |
|-------|-------------------|
| High auth latency | Alert on p95 > 200ms |
| Failed webhooks | Alert on failure rate > 1% |
| Session anomalies | Track unusual session patterns |
| API errors | Capture with Sentry context |
