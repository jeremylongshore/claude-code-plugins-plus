---
name: supabase-sdk-patterns
description: |
  Apply production-ready Supabase SDK patterns for TypeScript projects.
  Use when implementing type-safe Supabase queries, building a service layer,
  or establishing team coding standards for @supabase/supabase-js usage.
  Trigger with phrases like "supabase SDK patterns", "supabase best practices",
  "supabase typescript", "idiomatic supabase", "supabase service layer".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, typescript, patterns]

---
# Supabase SDK Patterns

## Overview
Production-ready patterns for `@supabase/supabase-js` v2: typed client singletons, service layer abstraction, error handling, retry logic, and response validation with Zod.

## Prerequisites
- `@supabase/supabase-js` v2 installed
- TypeScript project with generated database types
- Familiarity with async/await

## Instructions

### Pattern 1: Typed Client Singleton

```typescript
// lib/supabase.ts
import { createClient, SupabaseClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

let client: SupabaseClient<Database> | null = null

export function getSupabase(): SupabaseClient<Database> {
  if (!client) {
    client = createClient<Database>(
      process.env.SUPABASE_URL!,
      process.env.SUPABASE_ANON_KEY!,
      {
        auth: {
          autoRefreshToken: true,
          persistSession: true,
        },
        db: {
          schema: 'public',
        },
        global: {
          headers: { 'x-app-name': 'my-app' },
        },
      }
    )
  }
  return client
}
```

### Pattern 2: Service Layer Abstraction

```typescript
// services/todo-service.ts
import { getSupabase } from '../lib/supabase'
import type { Database } from '../lib/database.types'

type Todo = Database['public']['Tables']['todos']['Row']
type TodoInsert = Database['public']['Tables']['todos']['Insert']
type TodoUpdate = Database['public']['Tables']['todos']['Update']

export const TodoService = {
  async list(userId: string, limit = 50): Promise<Todo[]> {
    const { data, error } = await getSupabase()
      .from('todos')
      .select('id, title, is_complete, inserted_at')
      .eq('user_id', userId)
      .order('inserted_at', { ascending: false })
      .limit(limit)

    if (error) throw new SupabaseServiceError('list', error)
    return data
  },

  async create(todo: TodoInsert): Promise<Todo> {
    const { data, error } = await getSupabase()
      .from('todos')
      .insert(todo)
      .select()
      .single()

    if (error) throw new SupabaseServiceError('create', error)
    return data
  },

  async update(id: number, changes: TodoUpdate): Promise<Todo> {
    const { data, error } = await getSupabase()
      .from('todos')
      .update(changes)
      .eq('id', id)
      .select()
      .single()

    if (error) throw new SupabaseServiceError('update', error)
    return data
  },

  async delete(id: number): Promise<void> {
    const { error } = await getSupabase()
      .from('todos')
      .delete()
      .eq('id', id)

    if (error) throw new SupabaseServiceError('delete', error)
  },
}
```

### Pattern 3: Custom Error Class

```typescript
// lib/errors.ts
import { PostgrestError } from '@supabase/supabase-js'

export class SupabaseServiceError extends Error {
  code: string
  details: string
  hint: string

  constructor(operation: string, pgError: PostgrestError) {
    super(`Supabase ${operation} failed: ${pgError.message}`)
    this.name = 'SupabaseServiceError'
    this.code = pgError.code
    this.details = pgError.details
    this.hint = pgError.hint
  }

  get isNotFound(): boolean {
    return this.code === 'PGRST116'
  }

  get isConflict(): boolean {
    return this.code === '23505'
  }

  get isRLSViolation(): boolean {
    return this.code === '42501'
  }
}
```

### Pattern 4: Retry with Exponential Backoff

```typescript
// lib/retry.ts
export async function withRetry<T>(
  fn: () => Promise<T>,
  { maxRetries = 3, baseDelay = 200 } = {}
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error: any) {
      const isRetryable =
        error.code === 'PGRST000' ||  // connection error
        error.message?.includes('timeout') ||
        error.message?.includes('fetch failed')

      if (!isRetryable || attempt === maxRetries) throw error

      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 100
      await new Promise((r) => setTimeout(r, delay))
    }
  }
  throw new Error('Unreachable')
}

// Usage
const todos = await withRetry(() => TodoService.list(userId))
```

### Pattern 5: Response Validation with Zod

```typescript
import { z } from 'zod'

const TodoSchema = z.object({
  id: z.number(),
  title: z.string().min(1),
  is_complete: z.boolean(),
  inserted_at: z.string().datetime(),
})

const TodoListSchema = z.array(TodoSchema)

export async function getValidatedTodos(userId: string) {
  const { data, error } = await getSupabase()
    .from('todos')
    .select('id, title, is_complete, inserted_at')
    .eq('user_id', userId)

  if (error) throw new SupabaseServiceError('list', error)

  const parsed = TodoListSchema.safeParse(data)
  if (!parsed.success) {
    console.error('Schema mismatch:', parsed.error.issues)
    throw new Error('Response validation failed')
  }
  return parsed.data
}
```

### Pattern 6: Pagination Helper

```typescript
export async function paginate<T>(
  table: string,
  select: string,
  { page = 1, pageSize = 20, orderBy = 'id' } = {}
) {
  const from = (page - 1) * pageSize
  const to = from + pageSize - 1

  const { data, error, count } = await getSupabase()
    .from(table)
    .select(select, { count: 'exact' })
    .order(orderBy)
    .range(from, to)

  if (error) throw new SupabaseServiceError('paginate', error)

  return {
    data: data as T[],
    page,
    pageSize,
    total: count ?? 0,
    totalPages: Math.ceil((count ?? 0) / pageSize),
  }
}
```

## Output
- Type-safe client singleton with `Database` generics
- Service layer abstracting Supabase calls behind domain methods
- Custom error class mapping PostgrestError codes
- Retry wrapper for transient failures
- Zod validation for runtime response safety
- Pagination helper for list endpoints

## Error Handling

| Error Code | Meaning | Pattern Response |
|------------|---------|-----------------|
| `PGRST116` | No rows found | Return `null` or throw NotFound |
| `23505` | Unique constraint violation | Return conflict or use `.upsert()` |
| `42501` | RLS policy violation | Check auth state, verify policy |
| `PGRST000` | Connection error | Retry with backoff |
| `42P01` | Table does not exist | Check schema and types |

## Resources
- [Supabase JS API Reference](https://supabase.com/docs/reference/javascript/initializing)
- [TypeScript Support](https://supabase.com/docs/reference/javascript/typescript-support)
- [Generating Types](https://supabase.com/docs/guides/api/rest/generating-types)

## Next Steps
For database schema design, see `supabase-schema-from-requirements`.
