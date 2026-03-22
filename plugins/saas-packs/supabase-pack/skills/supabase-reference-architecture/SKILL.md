---
name: supabase-reference-architecture
description: |
  Implement Supabase reference architecture with layered project structure,
  typed client wrapper, service layer, and health checks.
  Use when designing a new Supabase project, reviewing project structure,
  or establishing architecture standards for a team.
  Trigger with phrases like "supabase architecture", "supabase project structure",
  "how to organize supabase", "supabase best practices layout".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, architecture, patterns]

---
# Supabase Reference Architecture

## Overview
A battle-tested project layout for Supabase applications that separates client initialization, data access, business logic, and API layers. Designed for testability, maintainability, and easy onboarding.

## Prerequisites
- TypeScript project with `@supabase/supabase-js` v2
- Supabase CLI for local development
- Understanding of layered architecture

## Instructions

### Recommended Project Structure

```
my-app/
├── supabase/
│   ├── migrations/          # SQL migrations (version controlled)
│   ├── seed.sql             # Development seed data
│   ├── functions/           # Edge Functions (Deno)
│   │   ├── process-order/index.ts
│   │   └── send-email/index.ts
│   └── config.toml          # Supabase CLI config
├── lib/
│   ├── supabase.ts          # Client singleton (anon key)
│   ├── supabase-admin.ts    # Admin client (service role, server only)
│   ├── database.types.ts    # Auto-generated types
│   └── errors.ts            # Custom error classes
├── services/
│   ├── auth-service.ts      # Auth operations
│   ├── todo-service.ts      # Todo CRUD
│   ├── storage-service.ts   # File operations
│   └── realtime-service.ts  # Subscription management
├── hooks/                   # React hooks (if applicable)
│   ├── use-auth.ts
│   ├── use-todos.ts
│   └── use-realtime.ts
├── api/                     # API routes / server handlers
│   ├── health.ts
│   └── webhooks.ts
└── tests/
    ├── services/
    └── supabase/            # pgTAP tests
```

### Layer 1: Client Initialization

```typescript
// lib/supabase.ts — Browser/Client singleton
import { createClient, SupabaseClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

let browserClient: SupabaseClient<Database> | null = null

export function getSupabase(): SupabaseClient<Database> {
  if (!browserClient) {
    browserClient = createClient<Database>(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  }
  return browserClient
}

// lib/supabase-admin.ts — Server-only admin client
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

export function getSupabaseAdmin() {
  return createClient<Database>(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )
}
```

### Layer 2: Service Layer

```typescript
// services/todo-service.ts
import { getSupabase } from '../lib/supabase'
import { SupabaseServiceError } from '../lib/errors'
import type { Database } from '../lib/database.types'

type Todo = Database['public']['Tables']['todos']['Row']
type TodoInsert = Database['public']['Tables']['todos']['Insert']

export const TodoService = {
  async list(opts: { userId: string; limit?: number; offset?: number }): Promise<Todo[]> {
    const { data, error } = await getSupabase()
      .from('todos')
      .select('id, title, is_complete, inserted_at')
      .eq('user_id', opts.userId)
      .order('inserted_at', { ascending: false })
      .range(opts.offset ?? 0, (opts.offset ?? 0) + (opts.limit ?? 50) - 1)

    if (error) throw new SupabaseServiceError('TodoService.list', error)
    return data
  },

  async create(todo: TodoInsert): Promise<Todo> {
    const { data, error } = await getSupabase()
      .from('todos')
      .insert(todo)
      .select()
      .single()

    if (error) throw new SupabaseServiceError('TodoService.create', error)
    return data
  },

  async toggleComplete(id: number, isComplete: boolean): Promise<Todo> {
    const { data, error } = await getSupabase()
      .from('todos')
      .update({ is_complete: isComplete })
      .eq('id', id)
      .select()
      .single()

    if (error) throw new SupabaseServiceError('TodoService.toggle', error)
    return data
  },
}
```

### Layer 3: React Hooks (Optional)

```typescript
// hooks/use-todos.ts
import { useState, useEffect } from 'react'
import { TodoService } from '../services/todo-service'
import { getSupabase } from '../lib/supabase'

export function useTodos(userId: string) {
  const [todos, setTodos] = useState<Todo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    TodoService.list({ userId }).then(setTodos).finally(() => setLoading(false))

    // Subscribe to real-time changes
    const channel = getSupabase()
      .channel('todos')
      .on('postgres_changes',
        { event: '*', schema: 'public', table: 'todos', filter: `user_id=eq.${userId}` },
        (payload) => {
          if (payload.eventType === 'INSERT') setTodos(prev => [payload.new as Todo, ...prev])
          if (payload.eventType === 'UPDATE') setTodos(prev =>
            prev.map(t => t.id === (payload.new as Todo).id ? payload.new as Todo : t)
          )
          if (payload.eventType === 'DELETE') setTodos(prev =>
            prev.filter(t => t.id !== (payload.old as Todo).id)
          )
        }
      )
      .subscribe()

    return () => { getSupabase().removeChannel(channel) }
  }, [userId])

  return { todos, loading }
}
```

### Layer 4: Error Handling

```typescript
// lib/errors.ts
import { PostgrestError } from '@supabase/supabase-js'

export class SupabaseServiceError extends Error {
  code: string
  operation: string

  constructor(operation: string, pgError: PostgrestError) {
    super(`[${operation}] ${pgError.message}`)
    this.name = 'SupabaseServiceError'
    this.code = pgError.code
    this.operation = operation
  }

  toJSON() {
    return {
      error: this.message,
      code: this.code,
      operation: this.operation,
    }
  }
}
```

### Layer 5: Health Check

```typescript
// api/health.ts
import { getSupabaseAdmin } from '../lib/supabase-admin'

export async function healthCheck() {
  const checks: Record<string, { ok: boolean; latency_ms: number }> = {}

  // Database connectivity
  const dbStart = Date.now()
  const { error: dbError } = await getSupabaseAdmin().rpc('version')
  checks.database = { ok: !dbError, latency_ms: Date.now() - dbStart }

  // Storage connectivity
  const storageStart = Date.now()
  const { error: storageError } = await getSupabaseAdmin().storage.listBuckets()
  checks.storage = { ok: !storageError, latency_ms: Date.now() - storageStart }

  const allHealthy = Object.values(checks).every(c => c.ok)
  return { status: allHealthy ? 'healthy' : 'degraded', checks }
}
```

## Output
- Layered project structure with clear separation of concerns
- Typed client singletons for browser and server
- Service layer abstracting all Supabase operations
- React hooks with built-in Realtime subscriptions
- Custom error classes for consistent error handling
- Health check endpoint covering database and storage

## Resources
- [Supabase Architecture](https://supabase.com/docs/guides/getting-started/architecture)
- [TypeScript Support](https://supabase.com/docs/reference/javascript/typescript-support)
- [Generating Types](https://supabase.com/docs/guides/api/rest/generating-types)

## Next Steps
For multi-environment configuration, see `supabase-multi-env-setup`.
