# Clerk Security Basics - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Secure Environment Variables
```bash
# .env.local (development)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# .env.production (production - use secrets manager)
# NEVER commit production keys to git
# Use Vercel/Railway/AWS Secrets Manager

# .gitignore
.env.local
.env.production
.env*.local
```

```typescript
// lib/env.ts - Validate environment at startup
const requiredEnvVars = [
  'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY',
  'CLERK_SECRET_KEY'
]

export function validateEnv() {
  for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
      throw new Error(`Missing required environment variable: ${envVar}`)
    }
  }

  // Validate key format
  const pk = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY!
  if (!pk.startsWith('pk_test_') && !pk.startsWith('pk_live_')) {
    throw new Error('Invalid publishable key format')
  }
}
```

### Step 2: Secure Middleware Configuration
```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks(.*)'
])

const isAdminRoute = createRouteMatcher(['/admin(.*)'])
const isSensitiveRoute = createRouteMatcher(['/api/admin(.*)', '/api/billing(.*)'])

export default clerkMiddleware(async (auth, request) => {
  const { userId, orgRole } = await auth()

  // Security headers
  const response = NextResponse.next()
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')

  // Protect routes
  if (!isPublicRoute(request)) {
    if (!userId) {
      return NextResponse.redirect(new URL('/sign-in', request.url))
    }
  }

  // Admin routes require admin role
  if (isAdminRoute(request) && orgRole !== 'org:admin') {
    return NextResponse.redirect(new URL('/unauthorized', request.url))
  }

  // Log sensitive route access
  if (isSensitiveRoute(request)) {
    console.log('Sensitive route accessed:', {
      path: request.nextUrl.pathname,
      userId,
      timestamp: new Date().toISOString()
    })
  }

  return response
})
```

### Step 3: Secure API Routes
```typescript
// app/api/protected/route.ts
import { auth } from '@clerk/nextjs/server'
import { headers } from 'next/headers'

export async function POST(request: Request) {
  // 1. Verify authentication
  const { userId, sessionId } = await auth()
  if (!userId) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // 2. Validate request origin (CSRF protection)
  const headersList = await headers()
  const origin = headersList.get('origin')
  const allowedOrigins = [
    process.env.NEXT_PUBLIC_APP_URL,
    'https://yourdomain.com'
  ]

  if (origin && !allowedOrigins.includes(origin)) {
    return Response.json({ error: 'Invalid origin' }, { status: 403 })
  }

  // 3. Validate content type
  const contentType = headersList.get('content-type')
  if (!contentType?.includes('application/json')) {
    return Response.json({ error: 'Invalid content type' }, { status: 400 })
  }

  // 4. Parse and validate body
  let body
  try {
    body = await request.json()
  } catch {
    return Response.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  // 5. Process request
  return Response.json({ success: true })
}
```

### Step 4: Secure Webhook Handling
```typescript
// app/api/webhooks/clerk/route.ts
import { Webhook } from 'svix'
import { headers } from 'next/headers'
import { WebhookEvent } from '@clerk/nextjs/server'

export async function POST(req: Request) {
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET

  if (!WEBHOOK_SECRET) {
    console.error('CLERK_WEBHOOK_SECRET not configured')
    return Response.json({ error: 'Configuration error' }, { status: 500 })
  }

  // Get headers
  const headerPayload = await headers()
  const svix_id = headerPayload.get('svix-id')
  const svix_timestamp = headerPayload.get('svix-timestamp')
  const svix_signature = headerPayload.get('svix-signature')

  // Validate required headers
  if (!svix_id || !svix_timestamp || !svix_signature) {
    return Response.json({ error: 'Missing svix headers' }, { status: 400 })
  }

  // Verify webhook
  const body = await req.text()
  const wh = new Webhook(WEBHOOK_SECRET)

  let evt: WebhookEvent

  try {
    evt = wh.verify(body, {
      'svix-id': svix_id,
      'svix-timestamp': svix_timestamp,
      'svix-signature': svix_signature
    }) as WebhookEvent
  } catch (err) {
    console.error('Webhook verification failed:', err)
    return Response.json({ error: 'Invalid signature' }, { status: 400 })
  }

  // Process verified event
  const eventType = evt.type

  // Idempotency check (prevent replay attacks)
  const processed = await checkIfProcessed(svix_id)
  if (processed) {
    return Response.json({ message: 'Already processed' })
  }

  // Handle event
  await processWebhookEvent(evt)

  // Mark as processed
  await markAsProcessed(svix_id)

  return Response.json({ success: true })
}
```

### Step 5: Session Security
```typescript
// lib/session-security.ts
import { auth } from '@clerk/nextjs/server'

export async function validateSession() {
  const { userId, sessionClaims } = await auth()

  if (!userId) {
    throw new Error('No session')
  }

  // Check session age
  const issuedAt = sessionClaims?.iat
  const maxAge = 60 * 60 // 1 hour in seconds

  if (issuedAt && Date.now() / 1000 - issuedAt > maxAge) {
    throw new Error('Session too old, please re-authenticate')
  }

  return { userId, sessionClaims }
}

// Force re-authentication for sensitive operations
export async function requireFreshAuth() {
  const { userId, sessionClaims } = await auth()

  if (!userId) {
    throw new Error('Not authenticated')
  }

  const issuedAt = sessionClaims?.iat
  const freshThreshold = 5 * 60 // 5 minutes

  if (issuedAt && Date.now() / 1000 - issuedAt > freshThreshold) {
    throw new Error('Please re-authenticate for this action')
  }

  return { userId }
}
```

## Security Checklist

- [ ] Production keys stored in secrets manager
- [ ] Environment variables validated at startup
- [ ] Middleware protects all sensitive routes
- [ ] API routes validate authentication
- [ ] Webhooks verified with svix
- [ ] Security headers configured
- [ ] HTTPS enforced in production
- [ ] Session timeouts configured
