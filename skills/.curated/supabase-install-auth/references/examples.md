# Supabase Install & Auth — Examples

## TypeScript — Full setup with auth

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_KEY!
)

// Sign up a new user
const { data: signUp, error: signUpError } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password-123',
})

// Sign in an existing user
const { data: signIn, error: signInError } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password-123',
})

// Get the current session
const { data: { session } } = await supabase.auth.getSession()
console.log('Logged in as:', session?.user.email)

// Sign out
await supabase.auth.signOut()
```

## Python — Full setup with auth

```python
import os
from supabase import create_client

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
supabase = create_client(url, key)

# Sign up a new user
result = supabase.auth.sign_up({
    "email": "user@example.com",
    "password": "secure-password-123",
})

# Sign in an existing user
result = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "secure-password-123",
})

# Get the current session
session = supabase.auth.get_session()
print(f"Logged in as: {session.user.email}")

# Sign out
supabase.auth.sign_out()
```

## TypeScript — SSR with Next.js App Router

```typescript
// app/lib/supabase-server.ts
import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'

export function createServerClient() {
  const cookieStore = cookies()
  return createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_KEY!,
    {
      auth: {
        persistSession: false,
      },
    }
  )
}
```

## TypeScript — Type-safe client with generated types

```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

const supabase = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_KEY!
)

// Fully typed query — IDE autocomplete for table and column names
const { data: users, error } = await supabase
  .from('profiles')
  .select('id, username, avatar_url')
  .eq('is_active', true)
  .order('created_at', { ascending: false })
  .limit(10)
```
