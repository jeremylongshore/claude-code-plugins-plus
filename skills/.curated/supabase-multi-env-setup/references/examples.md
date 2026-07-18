# Supabase Multi-Environment — Examples

Worked examples for the three-tier Supabase setup. Example 1 is the fastest path to a
working three-env split; Examples 2 and 3 show environment-aware guards in application
code.

## Example 1 — Quick three-env bootstrap

```bash
# Initialize Supabase in existing project
npx supabase init

# Start local
npx supabase start
# Copy output keys to .env.local

# Create staging + production projects in dashboard
# Copy their URLs and keys to .env.staging / .env.production

# Create first migration
npx supabase migration new create_users
# Edit the migration, then:
npx supabase db reset  # Test locally

# Promote to staging
npx supabase link --project-ref abcdefghijklmnop
npx supabase db push

# Promote to production
npx supabase link --project-ref qrstuvwxyz123456
npx supabase db push
```

## Example 2 — Next.js middleware for environment validation

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Add environment header for observability
  const env = process.env.SUPABASE_ENV ?? 'unknown';
  response.headers.set('x-supabase-env', env);

  // Block admin routes in production unless authenticated
  if (env === 'production' && request.nextUrl.pathname.startsWith('/admin/seed')) {
    return NextResponse.json({ error: 'Not available in production' }, { status: 403 });
  }

  return response;
}
```

## Example 3 — Verify environment before destructive operations

```typescript
import { getEnvironment, requireNonProduction } from '@/lib/env';

async function adminResetHandler(req: Request) {
  const env = getEnvironment();
  console.log(`[admin-reset] Running in ${env} environment`);

  requireNonProduction('admin-reset');

  // Safe to proceed — we're in local or staging
  const { error } = await supabase.rpc('reset_test_data');
  if (error) throw error;

  return Response.json({ status: 'reset complete', environment: env });
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
