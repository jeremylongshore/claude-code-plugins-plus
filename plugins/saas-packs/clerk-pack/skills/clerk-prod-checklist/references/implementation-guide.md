# Clerk Production Checklist - Implementation Guide

Detailed implementation examples and code patterns.

## Production Checklist

### 1. Environment Configuration

#### API Keys
- [ ] Switch from test keys (`pk_test_`, `sk_test_`) to live keys (`pk_live_`, `sk_live_`)
- [ ] Store secret key in secure secrets manager (not environment files)
- [ ] Remove any hardcoded keys from codebase

```bash
# Verify production keys
echo "Publishable key starts with: ${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY:0:8}"
# Should output: pk_live_
```

#### Environment Variables
```bash
# Required production variables
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
CLERK_WEBHOOK_SECRET=whsec_...

# Optional but recommended
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/onboarding
```

### 2. Clerk Dashboard Configuration

#### Domain Settings
- [ ] Add production domain in Clerk Dashboard
- [ ] Configure allowed origins for CORS
- [ ] Set up custom domain for Clerk (optional)

#### Authentication Settings
- [ ] Review and configure allowed sign-in methods
- [ ] Configure password requirements
- [ ] Set session token lifetime
- [ ] Configure multi-session behavior

#### OAuth Providers
- [ ] Switch OAuth apps to production mode
- [ ] Update redirect URLs to production domain
- [ ] Verify OAuth scopes are minimal needed

### 3. Security Configuration

#### Middleware
```typescript
// middleware.ts - Production configuration
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks(.*)',
  '/api/public(.*)'
])

export default clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect()
  }
})
```

#### Security Headers
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff
- [ ] Strict-Transport-Security enabled
- [ ] Content-Security-Policy configured

### 4. Webhooks Setup

- [ ] Configure production webhook endpoint
- [ ] Set webhook secret in environment
- [ ] Subscribe to required events:
  - `user.created`
  - `user.updated`
  - `user.deleted`
  - `session.created`
  - `session.revoked`
  - `organization.created` (if using orgs)

```typescript
// Verify webhook endpoint is accessible
// POST https://yourdomain.com/api/webhooks/clerk
```

### 5. Error Handling

- [ ] Custom error pages configured
- [ ] Error logging to monitoring service
- [ ] Fallback UI for auth failures

```typescript
// app/error.tsx
'use client'

export default function Error({ error, reset }: {
  error: Error
  reset: () => void
}) {
  return (
    <div>
      <h2>Authentication Error</h2>
      <p>{error.message}</p>
      <button onClick={reset}>Try again</button>
    </div>
  )
}
```

### 6. Performance Optimization

- [ ] Enable ISR/SSG where possible
- [ ] Configure CDN caching headers
- [ ] Implement user data caching
- [ ] Optimize middleware matcher

```typescript
// Optimized middleware matcher
export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)'
  ]
}
```

### 7. Monitoring & Logging

- [ ] Error tracking configured (Sentry, etc.)
- [ ] Authentication events logged
- [ ] Rate limit monitoring
- [ ] Uptime monitoring for auth endpoints

```typescript
// Example: Sentry integration
import * as Sentry from '@sentry/nextjs'

export async function POST(request: Request) {
  try {
    // ... auth logic
  } catch (error) {
    Sentry.captureException(error, {
      tags: { component: 'clerk-auth' }
    })
    throw error
  }
}
```

### 8. Testing

- [ ] E2E tests for sign-in/sign-up flows
- [ ] API route authentication tests
- [ ] Webhook handling tests
- [ ] Load testing completed

```typescript
// Example: Playwright test
test('user can sign in', async ({ page }) => {
  await page.goto('/sign-in')
  await page.fill('input[name="email"]', 'test@example.com')
  await page.fill('input[name="password"]', 'password123')
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/dashboard')
})
```

### 9. Documentation

- [ ] Document environment variable requirements
- [ ] Document webhook event handling
- [ ] Document custom authentication flows
- [ ] Runbook for auth-related incidents

### 10. Backup & Recovery

- [ ] Understand Clerk's data retention
- [ ] Document user export procedures
- [ ] Plan for Clerk service disruption

## Validation Script

```bash
#!/bin/bash
# scripts/validate-production.sh

echo "=== Clerk Production Validation ==="

# Check environment
if [[ $NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY != pk_live_* ]]; then
  echo "ERROR: Not using production publishable key"
  exit 1
fi

if [[ -z "$CLERK_SECRET_KEY" ]]; then
  echo "ERROR: CLERK_SECRET_KEY not set"
  exit 1
fi

if [[ -z "$CLERK_WEBHOOK_SECRET" ]]; then
  echo "WARNING: CLERK_WEBHOOK_SECRET not set"
fi

# Check middleware exists
if [[ ! -f "middleware.ts" ]]; then
  echo "WARNING: middleware.ts not found"
fi

echo "=== Validation Complete ==="
```
