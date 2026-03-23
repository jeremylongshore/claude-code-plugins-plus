---
name: supabase-architecture-variants
description: |
  Implement Supabase across different app architectures: Next.js SSR with
  server components using service_role and client components with anon key,
  SPA (React/Vue), mobile (React Native), serverless (Edge Functions),
  and multi-tenant with schema-per-tenant or RLS isolation.
  Use when choosing how to integrate Supabase into your specific stack,
  setting up SSR auth flows, configuring mobile deep links,
  or designing multi-tenant data isolation.
  Trigger with phrases like "supabase next.js", "supabase SSR",
  "supabase react native", "supabase SPA", "supabase serverless",
  "supabase multi-tenant", "supabase server component",
  "supabase architecture", "supabase service_role server".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, architecture, nextjs, ssr, spa, mobile, multi-tenant, serverless]
---

# Supabase Architecture Variants

## Overview

Different application architectures require fundamentally different Supabase `createClient` configurations. The critical distinction is **where the client runs** (browser vs server) and **which key it uses** (anon key respects RLS; service_role bypasses it). This skill provides production-ready patterns for five architectures: **Next.js SSR** (server components with service_role, client components with anon), **SPA** (React/Vue with browser-only client), **Mobile** (React Native with deep link auth), **Serverless** (Edge Functions with per-request clients), and **Multi-tenant** (RLS-based or schema-per-tenant isolation).

## Prerequisites

- `@supabase/supabase-js` v2+ installed
- `@supabase/ssr` package for Next.js SSR (v0.5+)
- Supabase project with URL, anon key, and service role key
- TypeScript project with generated database types (`supabase gen types typescript`)
- For mobile: React Native with Expo or bare workflow

## Step 1 — Next.js SSR (App Router with Server and Client Components)

Next.js App Router requires **two separate clients**: a server-side client using cookies for auth (with `@supabase/ssr`) and a browser client for client components. Never expose `service_role` to the client.

### Server-Side Client (for Server Components, Route Handlers, Server Actions)

```typescript
// lib/supabase/server.ts
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import type { Database } from '../database.types'

export async function createSupabaseServer() {
  const cookieStore = await cookies()

  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // Called from Server Component — cookies are read-only
          }
        },
      },
    }
  )
}

// Admin client for server-only operations (bypasses RLS)
// NEVER import this in client components or expose to the browser
import { createClient } from '@supabase/supabase-js'

export function createSupabaseAdmin() {
  return createClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,  // NOT NEXT_PUBLIC_ — server only
    {
      auth: { autoRefreshToken: false, persistSession: false },
    }
  )
}
```

### Client-Side Client (for Client Components)

```typescript
// lib/supabase/client.ts
'use client'

import { createBrowserClient } from '@supabase/ssr'
import type { Database } from '../database.types'

let client: ReturnType<typeof createBrowserClient<Database>> | null = null

export function createSupabaseBrowser() {
  if (client) return client

  client = createBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!  // anon key only — respects RLS
  )

  return client
}
```

### Middleware for Auth Session Refresh

```typescript
// middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          )
          response = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // Refresh session — this is the critical call
  await supabase.auth.getUser()

  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'],
}
```

### Server Component Usage

```typescript
// app/dashboard/page.tsx
import { createSupabaseServer } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const supabase = await createSupabaseServer()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: projects, error } = await supabase
    .from('projects')
    .select('id, name, status, created_at')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })

  if (error) throw new Error(`Failed to load projects: ${error.message}`)

  return (
    <div>
      <h1>My Projects</h1>
      {projects.map(p => <ProjectCard key={p.id} project={p} />)}
    </div>
  )
}
```

### Server Action with Admin Client

```typescript
// app/actions/admin.ts
'use server'

import { createSupabaseAdmin } from '@/lib/supabase/server'

export async function deleteUserAccount(userId: string) {
  const supabase = createSupabaseAdmin()

  // Admin operation — bypasses RLS
  const { error: deleteError } = await supabase
    .from('user_data')
    .delete()
    .eq('user_id', userId)

  if (deleteError) throw new Error(`Data deletion failed: ${deleteError.message}`)

  // Delete auth user
  const { error: authError } = await supabase.auth.admin.deleteUser(userId)
  if (authError) throw new Error(`Auth deletion failed: ${authError.message}`)
}
```

## Step 2 — SPA (React/Vue) and Mobile (React Native)

### SPA Architecture (React with Vite)

SPAs use a single browser client with the anon key. All authorization is enforced via RLS. The service_role key is never present in the SPA bundle.

```typescript
// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

// Singleton client — one instance for the entire SPA
export const supabase = createClient<Database>(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,  // handles OAuth redirects
      storage: window.localStorage,
    },
  }
)

// Auth state listener — call once at app initialization
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_OUT') {
    // Clear local caches
    queryClient.clear()  // React Query
  }
  if (event === 'TOKEN_REFRESHED') {
    console.log('Token refreshed')
  }
})
```

### React Hook for Auth-Protected Queries

```typescript
// src/hooks/useSupabaseQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { supabase } from '../lib/supabase'

export function useTodos() {
  return useQuery({
    queryKey: ['todos'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('todos')
        .select('id, title, is_complete, created_at')
        .order('created_at', { ascending: false })

      if (error) throw new Error(`Failed to load todos: ${error.message}`)
      return data
    },
  })
}

export function useCreateTodo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (title: string) => {
      const { data, error } = await supabase
        .from('todos')
        .insert({ title })
        .select('id, title, is_complete, created_at')
        .single()

      if (error) throw new Error(`Failed to create todo: ${error.message}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })
}
```

### Mobile Architecture (React Native with Expo)

React Native needs `AsyncStorage` for session persistence and deep link handling for OAuth.

```typescript
// lib/supabase.ts (React Native)
import { createClient } from '@supabase/supabase-js'
import AsyncStorage from '@react-native-async-storage/async-storage'
import type { Database } from './database.types'

export const supabase = createClient<Database>(
  process.env.EXPO_PUBLIC_SUPABASE_URL!,
  process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY!,
  {
    auth: {
      storage: AsyncStorage,
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false,  // disabled for React Native
    },
  }
)
```

### Mobile OAuth with Deep Links

```typescript
// lib/auth.ts (React Native)
import { supabase } from './supabase'
import * as Linking from 'expo-linking'
import * as WebBrowser from 'expo-web-browser'

const redirectUrl = Linking.createURL('auth/callback')

export async function signInWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: redirectUrl,
      skipBrowserRedirect: true,  // handle manually for RN
    },
  })

  if (error) throw new Error(`OAuth failed: ${error.message}`)
  if (!data.url) throw new Error('No OAuth URL returned')

  // Open in-app browser
  const result = await WebBrowser.openAuthSessionAsync(data.url, redirectUrl)

  if (result.type === 'success') {
    const url = new URL(result.url)
    const params = new URLSearchParams(url.hash.substring(1))
    const accessToken = params.get('access_token')
    const refreshToken = params.get('refresh_token')

    if (accessToken && refreshToken) {
      const { error: sessionError } = await supabase.auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken,
      })
      if (sessionError) throw sessionError
    }
  }
}
```

### App.json Deep Link Configuration (Expo)

```json
{
  "expo": {
    "scheme": "myapp",
    "plugins": [
      [
        "expo-linking",
        {
          "scheme": "myapp"
        }
      ]
    ]
  }
}
```

## Step 3 — Serverless (Edge Functions) and Multi-Tenant

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
