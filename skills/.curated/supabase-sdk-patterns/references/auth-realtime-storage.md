# Auth, Realtime, and Storage

## Auth — sign up, sign in, get session

```typescript
// Sign up
const { data, error } = await getSupabase().auth.signUp({
  email: 'user@example.com',
  password: 'securepassword',
})

// Sign in with password
const { data, error } = await getSupabase().auth.signInWithPassword({
  email: 'user@example.com',
  password: 'securepassword',
})
// data.session contains access_token, refresh_token
// data.user contains user metadata

// Get current session
const { data: { session } } = await getSupabase().auth.getSession()
if (!session) {
  // User is not authenticated
}

// Sign out
await getSupabase().auth.signOut()

// Listen for auth changes
getSupabase().auth.onAuthStateChange((event, session) => {
  // event: 'SIGNED_IN' | 'SIGNED_OUT' | 'TOKEN_REFRESHED' | ...
  console.log('Auth event:', event, session?.user?.email)
})
```

## Realtime — subscribe to database changes

```typescript
const channel = getSupabase()
  .channel('room-messages')
  .on(
    'postgres_changes',
    {
      event: '*',           // 'INSERT' | 'UPDATE' | 'DELETE' | '*'
      schema: 'public',
      table: 'messages',
      filter: 'room_id=eq.42',  // Optional row-level filter
    },
    (payload) => {
      console.log('Change:', payload.eventType, payload.new)
      // payload.new = the new row (INSERT/UPDATE)
      // payload.old = the old row (UPDATE/DELETE)
    }
  )
  .subscribe((status) => {
    // status: 'SUBSCRIBED' | 'CLOSED' | 'CHANNEL_ERROR'
    console.log('Subscription status:', status)
  })

// Clean up when done
await getSupabase().removeChannel(channel)
```

## Storage — upload, download, get public URL

```typescript
// Upload a file
const { data, error } = await getSupabase().storage
  .from('avatars')          // bucket name
  .upload('users/avatar.png', file, {
    cacheControl: '3600',
    upsert: true,           // overwrite if exists
    contentType: 'image/png',
  })

// Download a file
const { data, error } = await getSupabase().storage
  .from('avatars')
  .download('users/avatar.png')
// data is a Blob

// Get public URL (no auth required if bucket is public)
const { data: { publicUrl } } = getSupabase().storage
  .from('avatars')
  .getPublicUrl('users/avatar.png')

// Get signed URL (time-limited access for private buckets)
const { data, error } = await getSupabase().storage
  .from('documents')
  .createSignedUrl('reports/q4.pdf', 3600)  // expires in 1 hour
// data.signedUrl
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
