# Next.js SSR (App Router with Server and Client Components)

Next.js App Router requires **two separate clients**: a server-side client using cookies for auth (with `@supabase/ssr`) and a browser client for client components. Never expose `service_role` to the client.

## Server-Side Client (for Server Components, Route Handlers, Server Actions)

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

## Client-Side Client (for Client Components)

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

## Middleware for Auth Session Refresh

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

## Server Component Usage

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

## Server Action with Admin Client

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

## Auth Callback Route (OAuth / magic link exchange)

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
