# Production Service Patterns

## Service layer pattern (recommended for production)

Wrap Supabase access in a typed service object so callers never touch the raw
client and error handling stays in one place.

```typescript
// services/user-service.ts
import type { Database } from '../lib/database.types'

type User = Database['public']['Tables']['users']['Row']
type UserInsert = Database['public']['Tables']['users']['Insert']

export const UserService = {
  async getById(id: string): Promise<User | null> {
    const { data, error } = await getSupabase()
      .from('users')
      .select('*')
      .eq('id', id)
      .single()

    if (error?.code === 'PGRST116') return null  // Not found
    if (error) throw error
    return data
  },

  async search(query: string, limit = 20): Promise<User[]> {
    const { data, error } = await getSupabase()
      .from('users')
      .select('id, name, email, avatar_url')
      .or(`name.ilike.%${query}%,email.ilike.%${query}%`)
      .order('name')
      .limit(limit)

    if (error) throw error
    return data
  },

  async createOrUpdate(user: UserInsert): Promise<User> {
    const { data, error } = await getSupabase()
      .from('users')
      .upsert(user, { onConflict: 'email' })
      .select()
      .single()

    if (error) throw error
    return data
  },
}
```

## Pagination helper

Use `{ count: 'exact' }` plus `.range()` to return a page of rows and the total
count in a single round trip.

```typescript
async function paginate<T>(
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

  if (error) throw error
  return {
    data: data as T[],
    page,
    pageSize,
    total: count ?? 0,
    totalPages: Math.ceil((count ?? 0) / pageSize),
  }
}

// Usage
const result = await paginate<User>('users', 'id, name, email', { page: 2 })
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
