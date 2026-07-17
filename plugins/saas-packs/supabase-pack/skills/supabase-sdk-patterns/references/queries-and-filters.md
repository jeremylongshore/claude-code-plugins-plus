# Queries, Filters, and Mutations

**All queries return `{ data, error }`.** Always destructure and check error before using data.

## Select with filters and chaining

```typescript
const { data, error } = await getSupabase()
  .from('users')
  .select('id, name, email')
  .eq('active', true)       // WHERE active = true
  .gt('age', 18)            // AND age > 18
  .ilike('name', '%john%')  // AND name ILIKE '%john%'
  .in('role', ['admin', 'editor'])  // AND role IN (...)
  .order('name', { ascending: true })
  .limit(10)

if (error) throw error
// data is typed as Pick<User, 'id' | 'name' | 'email'>[]
```

## Insert with select (return the inserted row)

```typescript
const { data: newUser, error } = await getSupabase()
  .from('users')
  .insert({ name: 'Alice', email: 'alice@example.com', active: true })
  .select()       // Without .select(), data is null
  .single()       // Unwrap from array to single object

if (error) throw error
// newUser is the full row with server-generated id, created_at, etc.
```

## Upsert (insert or update on conflict)

```typescript
const { data, error } = await getSupabase()
  .from('users')
  .upsert(
    { email: 'alice@example.com', name: 'Alice Updated' },
    { onConflict: 'email' }   // Match on unique column
  )
  .select()
  .single()
```

## Update and delete

```typescript
// Update
const { data, error } = await getSupabase()
  .from('users')
  .update({ active: false })
  .eq('id', userId)
  .select()
  .single()

// Delete
const { error } = await getSupabase()
  .from('users')
  .delete()
  .eq('id', userId)
```

## RPC — call a Postgres function

```typescript
const { data, error } = await getSupabase()
  .rpc('my_function', { arg1: 'value', arg2: 42 })

if (error) throw error
// data is the function's return value
```

## Complete filter reference

| Filter | SQL Equivalent | Example |
| -------- | --------------- | --------- |
| `.eq(col, val)` | `= val` | `.eq('status', 'active')` |
| `.neq(col, val)` | `!= val` | `.neq('role', 'guest')` |
| `.gt(col, val)` | `> val` | `.gt('age', 18)` |
| `.gte(col, val)` | `>= val` | `.gte('score', 90)` |
| `.lt(col, val)` | `< val` | `.lt('price', 100)` |
| `.lte(col, val)` | `<= val` | `.lte('quantity', 0)` |
| `.like(col, pat)` | `LIKE pat` | `.like('name', '%son')` |
| `.ilike(col, pat)` | `ILIKE pat` | `.ilike('email', '%@gmail%')` |
| `.is(col, val)` | `IS val` | `.is('deleted_at', null)` |
| `.in(col, arr)` | `IN (...)` | `.in('id', [1, 2, 3])` |
| `.contains(col, val)` | `@> val` | `.contains('tags', ['urgent'])` |
| `.range(from, to)` | `OFFSET/LIMIT` | `.range(0, 9)` (first 10 rows) |

## Python equivalent

```python
# Select with filters
result = get_supabase() \
    .table('users') \
    .select('id, name, email') \
    .eq('active', True) \
    .gt('age', 18) \
    .order('name') \
    .limit(10) \
    .execute()

if result.data is None:
    raise Exception(f"Query failed")

# Insert
result = get_supabase().table('users').insert({
    "name": "Alice", "email": "alice@example.com"
}).execute()

# Upsert
result = get_supabase().table('users').upsert({
    "email": "alice@example.com", "name": "Alice Updated"
}).execute()

# RPC
result = get_supabase().rpc('my_function', {"arg1": "value"}).execute()
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
