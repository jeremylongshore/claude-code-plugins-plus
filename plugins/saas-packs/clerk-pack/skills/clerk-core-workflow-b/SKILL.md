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
- Understanding of JWT session tokens

## Instructions

### Step 1: Configure Clerk Middleware
```typescript
// middleware.ts (project root)
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks(.*)',
  '/pricing',
  '/about',
]);

const isAdminRoute = createRouteMatcher([
  '/admin(.*)',
  '/api/admin(.*)',
]);

export default clerkMiddleware(async (auth, req) => {
  // Protect non-public routes
  if (!isPublicRoute(req)) {
    await auth.protect();
  }

  // Admin routes require admin role
  if (isAdminRoute(req)) {
    await auth.protect({
      role: 'org:admin',
    });
  }
});

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};
```

### Step 2: API Route Protection
```typescript
// app/api/protected/route.ts
import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

export async function GET() {
  const { userId, orgId, sessionClaims } = await auth();

  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  return NextResponse.json({
    userId,
    orgId,
    role: sessionClaims?.metadata?.role,
    sessionExpiry: sessionClaims?.exp,
  });
}

// Organization-scoped API route
export async function POST(req: Request) {
  const { userId, orgId, has } = await auth();

  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  if (!orgId) {
    return NextResponse.json({ error: 'Organization required' }, { status: 403 });
  }

  // Check organization permission
  if (!has({ permission: 'org:data:write' })) {
    return NextResponse.json({ error: 'Insufficient permissions' }, { status: 403 });
  }

  const body = await req.json();
  // Process request...
  return NextResponse.json({ success: true });
}
```

### Step 3: Session Claims and Custom Data
```typescript
// app/api/session/route.ts
import { auth, currentUser } from '@clerk/nextjs/server';

export async function GET() {
  const { userId, sessionId, getToken } = await auth();
  const user = await currentUser();

  if (!userId || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  // Get JWT token for external API calls
  const token = await getToken({ template: 'supabase' });

  return NextResponse.json({
    userId,
    sessionId,
    email: user.emailAddresses[0]?.emailAddress,
    fullName: `${user.firstName} ${user.lastName}`,
    imageUrl: user.imageUrl,
    publicMetadata: user.publicMetadata,
    externalToken: token ? 'present' : 'not configured',
  });
}
```

### Step 4: Server Component Auth Checks
```typescript
// app/dashboard/page.tsx
import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const { userId, orgId, has } = await auth();

  if (!userId) {
    redirect('/sign-in');
  }

  const isAdmin = has({ role: 'org:admin' });
  const canManageBilling = has({ permission: 'org:billing:manage' });

  return (
    <div>
      <h1>Dashboard</h1>
      <p>User: {userId}</p>
      {orgId && <p>Organization: {orgId}</p>}
      {isAdmin && <AdminPanel />}
      {canManageBilling && <BillingSection />}
    </div>
  );
}

// Reusable auth guard component
async function AuthGuard({
  children,
  permission,
}: {
  children: React.ReactNode;
  permission?: string;
}) {
  const { userId, has } = await auth();

  if (!userId) return null;
  if (permission && !has({ permission })) return null;

  return <>{children}</>;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Middleware redirect loop | Public route not in matcher | Add route to `isPublicRoute` |
| 401 on API route | Token not forwarded | Ensure fetch includes credentials |
| Missing org context | User not in organization | Check `orgId` before org-scoped operations |
| Session expired | Token TTL exceeded | Configure session lifetime in Clerk dashboard |

## Examples

### Role-Based Navigation
```typescript
// components/NavBar.tsx
import { auth } from '@clerk/nextjs/server';

export async function NavBar() {
  const { userId, has } = await auth();

  return (
    <nav>
      <a href="/">Home</a>
      {userId && <a href="/dashboard">Dashboard</a>}
      {has({ role: 'org:admin' }) && <a href="/admin">Admin</a>}
      {!userId && <a href="/sign-in">Sign In</a>}
    </nav>
  );
}
```

## Resources
- [Clerk Middleware](https://clerk.com/docs/references/nextjs/clerk-middleware)
- [Clerk Auth Helper](https://clerk.com/docs/references/nextjs/auth)
- [Clerk Organizations](https://clerk.com/docs/organizations/overview)
