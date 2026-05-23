## Serverless (Edge Functions) and Multi-Tenant Patterns

### Edge Functions with Per-Request Clients

Edge Functions create a new Supabase client per request, extracting the user's JWT from the Authorization header. This ensures proper RLS scoping.

```typescript
// supabase/functions/api/index.ts
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

Deno.serve(async (req) => {
  // Per-request client with the user's JWT for RLS
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!,
    {
      global: {
        headers: { Authorization: req.headers.get('Authorization')! },
      },
    }
  )

  // This client respects RLS using the user's JWT
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 })
  }

  // Queries are scoped to the authenticated user via RLS
  const { data, error } = await supabase
    .from('todos')
    .select('id, title, is_complete')
    .order('created_at', { ascending: false })

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }

  return new Response(JSON.stringify(data), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

### Edge Function with Admin Operations

```typescript
// supabase/functions/admin-task/index.ts
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

Deno.serve(async (req) => {
  // Verify the request has a valid admin JWT first
  const userClient = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!,
    { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
  )

  const { data: { user } } = await userClient.auth.getUser()
  if (!user) {
    return new Response('Unauthorized', { status: 401 })
  }

  // Check if user is admin
  const { data: profile } = await userClient
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  if (profile?.role !== 'admin') {
    return new Response('Forbidden', { status: 403 })
  }

  // Now use service_role for admin operations
  const adminClient = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // Admin operation: get all users
  const { data, error } = await adminClient.auth.admin.listUsers()
  if (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }

  return new Response(JSON.stringify({ users: data.users.length }))
})
```

### Multi-Tenant: RLS-Based Isolation (Recommended)

The simplest multi-tenant approach uses a single database with RLS policies scoping all queries to the tenant.

```sql
-- Schema for RLS-based multi-tenancy
CREATE TABLE public.tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  plan text DEFAULT 'free',
  created_at timestamptz DEFAULT now()
);

CREATE TABLE public.tenant_members (
  tenant_id uuid REFERENCES public.tenants(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
  PRIMARY KEY (tenant_id, user_id)
);

-- Store current tenant in user's JWT claims (set via custom claims hook)
-- Or look up from tenant_members table

CREATE TABLE public.projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES public.tenants(id),
  name text NOT NULL,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- RLS: users can only see projects belonging to their tenant
CREATE POLICY "tenant_isolation" ON public.projects
  FOR ALL USING (
    tenant_id IN (
      SELECT tenant_id FROM public.tenant_members
      WHERE user_id = auth.uid()
    )
  );

CREATE INDEX idx_projects_tenant_id ON public.projects(tenant_id);
CREATE INDEX idx_tenant_members_user_id ON public.tenant_members(user_id);
```

```typescript
// lib/supabase-tenant.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// All queries are automatically scoped to the user's tenant via RLS
export async function getTenantProjects() {
  const { data, error } = await supabase
    .from('projects')
    .select('id, name, created_at, tenant_id')
    .order('created_at', { ascending: false })

  if (error) throw new Error(`Failed to load projects: ${error.message}`)
  return data  // Only returns projects for the authenticated user's tenant(s)
}

// Switch active tenant (for users in multiple tenants)
export async function getUserTenants() {
  const { data, error } = await supabase
    .from('tenant_members')
    .select(`
      role,
      tenants:tenant_id (id, name, slug, plan)
    `)

  if (error) throw new Error(`Failed to load tenants: ${error.message}`)
  return data
}

// Create project in a specific tenant
export async function createProject(tenantId: string, name: string) {
  const { data, error } = await supabase
    .from('projects')
    .insert({ tenant_id: tenantId, name })
    .select('id, name, tenant_id, created_at')
    .single()

  if (error) throw new Error(`Failed to create project: ${error.message}`)
  return data
}
```

## Output

- Next.js SSR setup with server client (cookies-based auth), browser client, and middleware
- Server Actions using admin client with service_role for privileged operations
- SPA pattern with singleton client, React Query integration, and auth state listener
- React Native setup with AsyncStorage, deep link OAuth, and in-app browser
- Edge Function patterns for per-request auth and admin escalation
- Multi-tenant RLS isolation with tenant_members lookup and scoped queries
- Decision matrix for choosing the right architecture per stack

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `AuthSessionMissingError` in Server Component | Cookies not passed to Supabase client | Use `createServerClient` from `@supabase/ssr` with cookie handlers |
| OAuth redirect fails in React Native | Missing deep link scheme | Add `scheme` to app.json and configure Supabase redirect URL |
| service_role key in client bundle | Wrong env var prefix (`NEXT_PUBLIC_`) | Remove `NEXT_PUBLIC_` prefix; only server code should access it |
| Multi-tenant data leak | Missing RLS policy or missing tenant_id filter | Verify RLS is enabled and policies check `tenant_members` |
| Edge Function `auth.getUser()` returns null | Missing Authorization header | Forward user's JWT from the client call |
| Session not persisting on mobile | AsyncStorage not configured | Pass `AsyncStorage` in auth config; ensure package is installed |

## Examples

### Test Auth Flow End-to-End (Next.js)

```typescript
// app/auth/callback/route.ts
import { createSupabaseServer } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const code = searchParams.get('code')

  if (code) {
    const supabase = await createSupabaseServer()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    if (error) {
      return NextResponse.redirect(new URL('/login?error=auth_failed', request.url))
    }
  }

  return NextResponse.redirect(new URL('/dashboard', request.url))
}
```

### Verify Tenant Isolation

```sql
-- Test that RLS properly isolates tenants
SET request.jwt.claims = '{"sub": "user-uuid-1"}';

-- Should only return projects for user-uuid-1's tenant
SELECT * FROM public.projects;
```

## Resources

- [Supabase SSR (Next.js)](https://supabase.com/docs/guides/auth/server-side/nextjs)
- [Supabase React Native](https://supabase.com/docs/guides/getting-started/tutorials/with-expo-react-native)
- [Supabase Edge Functions](https://supabase.com/docs/guides/functions)
- [Multi-Tenant with RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase Auth Deep Linking](https://supabase.com/docs/guides/auth/native-mobile-deep-linking)
- [@supabase/ssr Package](https://supabase.com/docs/guides/auth/server-side/overview)

## Next Steps

For common mistakes and anti-patterns to avoid, see `supabase-known-pitfalls`.
