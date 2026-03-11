---
name: clerk-install-auth
description: |
  Install and configure Clerk SDK/CLI authentication.
  Use when setting up a new Clerk integration, configuring API keys,
  or initializing Clerk in your project.
  Trigger with phrases like "install clerk", "setup clerk",
  "clerk auth", "configure clerk API key", "add clerk to project".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Install & Auth

## Overview
Set up Clerk SDK and configure authentication credentials for your application.

## Prerequisites
- Node.js 18+ (Next.js, React, Express, etc.)
- Package manager (npm, pnpm, or yarn)
- Clerk account with API access
- Publishable and Secret keys from Clerk dashboard

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Next.js
npm install @clerk/nextjs

# React
npm install @clerk/clerk-react

# Express/Node.js
npm install @clerk/express

# Remix
npm install @clerk/remix
```

### Step 2: Configure Environment Variables
```bash
# Create .env.local file
cat >> .env.local << 'EOF'
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
EOF
```

### Step 3: Add ClerkProvider (Next.js App Router)
```typescript
// app/layout.tsx
import { ClerkProvider } from '@clerk/nextjs'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  )
}
```

### Step 4: Add Middleware
```typescript
// middleware.ts
import { clerkMiddleware } from '@clerk/nextjs/server'

export default clerkMiddleware()

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
}
```

### Step 5: Verify Connection
```typescript
import { auth } from '@clerk/nextjs/server'

export async function GET() {
  const { userId } = await auth()
  return Response.json({ authenticated: !!userId })
}
```

## Output
- Installed SDK package in node_modules
- Environment variables configured in .env.local
- ClerkProvider wrapping application
- Middleware protecting routes

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or mismatched keys | Verify keys in Clerk dashboard match environment |
| ClerkProvider Missing | SDK used outside provider | Wrap app root with ClerkProvider |
| Middleware Not Running | Matcher misconfigured | Check matcher regex in middleware.ts |
| Module Not Found | Installation failed | Run `npm install @clerk/nextjs` again |

## Examples

### Next.js App Router Setup
```typescript
// app/layout.tsx
import { ClerkProvider, SignInButton, SignedIn, SignedOut, UserButton } from '@clerk/nextjs'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>
          <header>
            <SignedOut>
              <SignInButton />
            </SignedOut>
            <SignedIn>
              <UserButton />
            </SignedIn>
          </header>
          {children}
        </body>
      </html>
    </ClerkProvider>
  )
}
```

### React SPA Setup
```typescript
import { ClerkProvider } from '@clerk/clerk-react'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

function App() {
  return (
    <ClerkProvider publishableKey={PUBLISHABLE_KEY}>
      <Router />
    </ClerkProvider>
  )
}
```

## Resources
- [Clerk Documentation](https://clerk.com/docs)
- [Clerk Dashboard](https://dashboard.clerk.com)
- [Clerk Status](https://status.clerk.com)

## Next Steps
After successful auth, proceed to `clerk-hello-world` for your first authenticated request.