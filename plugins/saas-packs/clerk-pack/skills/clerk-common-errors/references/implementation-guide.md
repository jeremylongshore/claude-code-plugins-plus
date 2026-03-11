# Clerk Common Errors - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Error Category 1: Configuration Errors

#### Invalid API Key
```
Error: Clerk: Invalid API key
```
**Cause:** Publishable or secret key is incorrect or mismatched.
**Solution:**
```bash
# Verify keys in .env.local match Clerk dashboard
# Publishable key starts with pk_test_ or pk_live_
# Secret key starts with sk_test_ or sk_live_

# Check for trailing whitespace
cat -A .env.local | grep CLERK

# Ensure correct environment
echo $NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
```

#### ClerkProvider Not Found
```
Error: useAuth can only be used within the <ClerkProvider /> component
```
**Cause:** Component using Clerk hooks is outside ClerkProvider.
**Solution:**
```typescript
// Ensure ClerkProvider wraps entire app in layout.tsx
import { ClerkProvider } from '@clerk/nextjs'

export default function RootLayout({ children }) {
  return (
    <ClerkProvider>
      <html><body>{children}</body></html>
    </ClerkProvider>
  )
}
```

### Error Category 2: Authentication Errors

#### Session Not Found
```
Error: Session not found
```
**Cause:** User session expired or was revoked.
**Solution:**
```typescript
// Handle gracefully in your app
const { userId } = await auth()
if (!userId) {
  redirect('/sign-in')
}
```

#### Form Identifier Not Found
```
Error: form_identifier_not_found
```
**Cause:** Email/username not registered.
**Solution:**
```typescript
// Show helpful message to user
catch (err: any) {
  if (err.errors?.[0]?.code === 'form_identifier_not_found') {
    setError('No account found with this email. Please sign up.')
  }
}
```

#### Password Incorrect
```
Error: form_password_incorrect
```
**Cause:** Wrong password entered.
**Solution:**
```typescript
catch (err: any) {
  if (err.errors?.[0]?.code === 'form_password_incorrect') {
    setError('Incorrect password. Try again or reset your password.')
  }
}
```

### Error Category 3: Middleware Errors

#### Infinite Redirect Loop
```
Error: Too many redirects
```
**Cause:** Middleware matcher includes sign-in page.
**Solution:**
```typescript
// middleware.ts
const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',  // Must include sign-in pages
  '/sign-up(.*)',
  '/'
])

export default clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect()
  }
})
```

#### Middleware Not Executing
```
Error: Routes not protected
```
**Cause:** Matcher not matching routes correctly.
**Solution:**
```typescript
export const config = {
  matcher: [
    // Skip static files and _next
    '/((?!_next|[^?]*\\.(?:html?|css|js|jpe?g|webp|png|gif|svg|ttf|woff2?|ico)).*)',
    '/',
    '/(api|trpc)(.*)'
  ]
}
```

### Error Category 4: Server/Client Errors

#### Hydration Mismatch
```
Error: Text content does not match server-rendered HTML
```
**Cause:** Auth state differs between server and client.
**Solution:**
```typescript
'use client'
import { useUser } from '@clerk/nextjs'

export function UserGreeting() {
  const { user, isLoaded } = useUser()

  // Prevent hydration mismatch by waiting for load
  if (!isLoaded) {
    return <div>Loading...</div>
  }

  return <div>Hello, {user?.firstName}</div>
}
```

#### Cannot Read Properties of Undefined
```
Error: Cannot read properties of undefined (reading 'userId')
```
**Cause:** Using auth() in client component or non-server context.
**Solution:**
```typescript
// Server Component - use auth()
import { auth } from '@clerk/nextjs/server'
const { userId } = await auth()

// Client Component - use useAuth()
'use client'
import { useAuth } from '@clerk/nextjs'
const { userId } = useAuth()
```

### Error Category 5: Webhook Errors

#### Webhook Verification Failed
```
Error: Webhook signature verification failed
```
**Cause:** Incorrect webhook secret or missing headers.
**Solution:**
```typescript
// app/api/webhooks/clerk/route.ts
import { Webhook } from 'svix'
import { headers } from 'next/headers'

export async function POST(req: Request) {
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET!

  const headerPayload = await headers()
  const svix_id = headerPayload.get('svix-id')
  const svix_timestamp = headerPayload.get('svix-timestamp')
  const svix_signature = headerPayload.get('svix-signature')

  const body = await req.text()

  const wh = new Webhook(WEBHOOK_SECRET)
  const evt = wh.verify(body, {
    'svix-id': svix_id!,
    'svix-timestamp': svix_timestamp!,
    'svix-signature': svix_signature!
  })

  // Process event
}
```

## Diagnostic Commands

```bash
# Check Clerk version
npm list @clerk/nextjs

# Verify environment variables
npx next info

# Check for multiple Clerk instances
npm list | grep clerk

# Clear Next.js cache
rm -rf .next && npm run dev
```

## Quick Reference Table

| Error Code | Meaning | Quick Fix |
|------------|---------|-----------|
| `form_identifier_not_found` | User doesn't exist | Show sign-up link |
| `form_password_incorrect` | Wrong password | Show reset link |
| `session_exists` | Already logged in | Redirect to app |
| `verification_expired` | Code expired | Resend code |
| `rate_limit_exceeded` | Too many attempts | Wait and retry |
