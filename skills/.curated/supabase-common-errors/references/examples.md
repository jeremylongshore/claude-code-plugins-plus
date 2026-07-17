# Supabase Common Errors — Worked Examples

Full copy-paste examples for the most common Supabase failure modes. SKILL.md
carries the first example inline; all four are reproduced here.

## Example 1 — Handling `.single()` on optional data (PGRST116)

```typescript
// BAD — crashes when user has no profile
const { data: profile } = await supabase
  .from('profiles')
  .select('*')
  .eq('user_id', userId)
  .single()  // throws PGRST116 if no row exists

// GOOD — returns null instead of erroring
const { data: profile, error } = await supabase
  .from('profiles')
  .select('*')
  .eq('user_id', userId)
  .maybeSingle()

if (!profile) {
  // Create a default profile
  const { data: newProfile } = await supabase
    .from('profiles')
    .insert({ user_id: userId, display_name: 'New User' })
    .select()
    .single()
}
```

## Example 2 — Upsert to avoid unique constraint (23505)

```typescript
// BAD — fails if row already exists
const { error } = await supabase
  .from('user_settings')
  .insert({ user_id: userId, theme: 'dark' })
// error.code === '23505' — unique constraint on user_id

// GOOD — inserts or updates based on conflict column
const { data, error } = await supabase
  .from('user_settings')
  .upsert(
    { user_id: userId, theme: 'dark' },
    { onConflict: 'user_id' }
  )
  .select()
  .single()
```

## Example 3 — Realtime subscription with error handling

```typescript
const channel = supabase
  .channel('todos-changes')
  .on(
    'postgres_changes',
    { event: '*', schema: 'public', table: 'todos' },
    (payload) => {
      console.log('Change received:', payload.eventType, payload.new)
    }
  )
  .subscribe((status, err) => {
    switch (status) {
      case 'SUBSCRIBED':
        console.log('Realtime connected')
        break
      case 'CHANNEL_ERROR':
        console.error('Realtime error — is the table in the publication?', err)
        // Fix: ALTER PUBLICATION supabase_realtime ADD TABLE todos;
        break
      case 'TIMED_OUT':
        console.error('Realtime timed out — check network')
        break
      case 'CLOSED':
        console.log('Channel closed')
        break
    }
  })

// Always clean up on unmount / exit
process.on('SIGINT', async () => {
  await supabase.removeChannel(channel)
  process.exit(0)
})
```

## Example 4 — Connection pool exhaustion (PGRST000) in serverless

```typescript
// BAD — creates a new client per request in serverless (Lambda, Edge Functions)
export async function handler(req: Request) {
  const supabase = createClient(url, key)  // new connection every invocation
  const { data } = await supabase.from('todos').select('*')
  return Response.json(data)
}

// GOOD — reuse client across warm invocations
const supabase = createClient(url, key, {
  auth: { autoRefreshToken: false, persistSession: false }
})

export async function handler(req: Request) {
  const { data, error } = await supabase.from('todos').select('*')
  if (error) {
    if (error.code === 'PGRST000') {
      // Pool exhausted — return 503 so the caller retries
      return new Response('Service temporarily unavailable', { status: 503 })
    }
    return Response.json({ error: error.message }, { status: 400 })
  }
  return Response.json(data)
}
```

## Quick Diagnostic Commands

```bash
# Check Supabase status
curl -s https://status.supabase.com

# Verify API connectivity
curl -I https://api.supabase.com

# Check local configuration
env | grep SUPABASE
```

### Escalation Path

1. Collect evidence with `supabase-debug-bundle`
2. Check Supabase status page
3. Contact support with request ID

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
