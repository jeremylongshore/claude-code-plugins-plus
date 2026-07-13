# Clerk Core Workflow B - Implementation Details

## Clerk Middleware Configuration

```typescript
// middleware.ts (project root)
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

const isPublicRoute = createRouteMatcher([
  '/', '/sign-in(.*)', '/sign-up(.*)', '/api/webhooks(.*)', '/pricing', '/about',
]);

const isAdminRoute = createRouteMatcher(['/admin(.*)', '/api/admin(.*)']);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) await auth.protect();
  if (isAdminRoute(req)) await auth.protect({ role: 'org:admin' });
});

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};
```

## API Route Protection

```typescript
// app/api/protected/route.ts
import { auth } from '@clerk/nextjs/server';

export async function GET() {
  const { userId, orgId, sessionClaims } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  return NextResponse.json({ userId, orgId, role: sessionClaims?.metadata?.role });
}

// Organization-scoped route
export async function POST(req: Request) {
  const { userId, orgId, has } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  if (!orgId) return NextResponse.json({ error: 'Organization required' }, { status: 403 });
  if (!has({ permission: 'org:data:write' })) return NextResponse.json({ error: 'Insufficient permissions' }, { status: 403 });
  const body = await req.json();
  return NextResponse.json({ success: true });
}
```

## Session Claims and JWT Tokens

```typescript
// app/api/session/route.ts
import { auth, currentUser } from '@clerk/nextjs/server';

export async function GET() {
  const { userId, sessionId, getToken } = await auth();
  const user = await currentUser();
  if (!userId || !user) return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });

  const token = await getToken({ template: 'supabase' }); // JWT for external APIs
  return NextResponse.json({
    userId, sessionId,
    email: user.emailAddresses[0]?.emailAddress,
    fullName: `${user.firstName} ${user.lastName}`,
    publicMetadata: user.publicMetadata,
    externalToken: token ? 'present' : 'not configured',
  });
}
```

## Server Component Auth Checks

```typescript
// app/dashboard/page.tsx
import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const { userId, orgId, has } = await auth();
  if (!userId) redirect('/sign-in');

  const isAdmin = has({ role: 'org:admin' });
  const canManageBilling = has({ permission: 'org:billing:manage' });

  return (
    <div>
      <h1>Dashboard</h1>
      {isAdmin && <AdminPanel />}
      {canManageBilling && <BillingSection />}
    </div>
  );
}

// Reusable auth guard
async function AuthGuard({ children, permission }: { children: React.ReactNode; permission?: string }) {
  const { userId, has } = await auth();
  if (!userId) return null;
  if (permission && !has({ permission })) return null;
  return <>{children}</>;
}
```

## Role-Based Navigation

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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
