---
name: supabase-auth-storage-realtime-core
description: |
  Implement the Supabase trifecta: Auth (signUp, signIn, OAuth, MFA), Storage (upload, download, signed URLs),
  and Realtime (Postgres changes, broadcast, presence).
  Trigger with phrases like "supabase auth", "supabase storage", "supabase realtime",
  "supabase file upload", "supabase oauth", "supabase subscribe".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, auth, storage, realtime]

---
# Supabase Auth + Storage + Realtime

## Overview
Implement the three pillars beyond database queries: user authentication (email, OAuth, MFA), file storage (uploads, downloads, signed URLs), and real-time subscriptions (Postgres changes, broadcast channels, presence tracking).

## Prerequisites
- Completed `supabase-install-auth` setup
- Supabase client initialized with `createClient`

## Instructions

### Auth: Email/Password Signup and Login

```typescript
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_ANON_KEY!)

// Sign up a new user
const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password-123',
  options: {
    data: { username: 'newuser', full_name: 'New User' },  // stored in raw_user_meta_data
  },
})
// If email confirmation enabled: data.user exists but data.session is null
// If email confirmation disabled: both data.user and data.session exist

// Sign in with password
const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password-123',
})
const { user, session } = signInData
// session.access_token contains the JWT for API calls

// Sign in with magic link (passwordless)
const { error } = await supabase.auth.signInWithOtp({
  email: 'user@example.com',
  options: { emailRedirectTo: 'https://myapp.com/auth/callback' },
})
```

### Auth: OAuth Providers

```typescript
// Sign in with Google
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: 'https://myapp.com/auth/callback',
    queryParams: { access_type: 'offline', prompt: 'consent' },
  },
})
// Redirect user to data.url

// Sign in with GitHub
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'github',
  options: { redirectTo: 'https://myapp.com/auth/callback' },
})

// Handle the callback (in your /auth/callback route)
const { data: { session }, error } = await supabase.auth.exchangeCodeForSession(code)
```

### Auth: Session Management

```typescript
// Get current session
const { data: { session } } = await supabase.auth.getSession()

// Get current user
const { data: { user } } = await supabase.auth.getUser()

// Listen for auth state changes
supabase.auth.onAuthStateChange((event, session) => {
  // event: 'SIGNED_IN' | 'SIGNED_OUT' | 'TOKEN_REFRESHED' | 'USER_UPDATED'
  if (event === 'SIGNED_OUT') {
    // Clear local state
  }
})

// Sign out
await supabase.auth.signOut()

// Reset password
await supabase.auth.resetPasswordForEmail('user@example.com', {
  redirectTo: 'https://myapp.com/auth/reset-password',
})
```

### Storage: Upload and Download Files

```typescript
// Upload a file to a bucket
const file = new File(['hello world'], 'hello.txt', { type: 'text/plain' })

const { data, error } = await supabase.storage
  .from('documents')  // bucket name
  .upload('folder/hello.txt', file, {
    cacheControl: '3600',
    upsert: false,  // set true to overwrite existing
    contentType: 'text/plain',
  })

// Download a file
const { data: blob, error: dlError } = await supabase.storage
  .from('documents')
  .download('folder/hello.txt')

// Get public URL (for public buckets)
const { data: { publicUrl } } = supabase.storage
  .from('avatars')
  .getPublicUrl('user123/avatar.png')

// Create a signed URL (for private buckets, expires in seconds)
const { data: signedUrl, error: signError } = await supabase.storage
  .from('documents')
  .createSignedUrl('folder/hello.txt', 3600)  // valid for 1 hour

// List files in a folder
const { data: files, error: listError } = await supabase.storage
  .from('documents')
  .list('folder', { limit: 100, offset: 0, sortBy: { column: 'name', order: 'asc' } })

// Delete files
const { error: removeError } = await supabase.storage
  .from('documents')
  .remove(['folder/hello.txt', 'folder/old-file.pdf'])
```

### Storage: Bucket RLS Policies

```sql
-- Create a storage bucket (via migration)
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true);  -- public bucket

insert into storage.buckets (id, name, public)
values ('documents', 'documents', false);  -- private bucket

-- Allow authenticated users to upload to their own folder
create policy "Users can upload own avatars"
  on storage.objects for insert
  with check (
    bucket_id = 'avatars' and
    auth.uid()::text = (storage.foldername(name))[1]
  );

-- Allow public read of avatars
create policy "Anyone can view avatars"
  on storage.objects for select
  using (bucket_id = 'avatars');

-- Allow users to manage their own documents
create policy "Users manage own documents"
  on storage.objects for all
  using (
    bucket_id = 'documents' and
    auth.uid()::text = (storage.foldername(name))[1]
  );
```

### Realtime: Subscribe to Database Changes

```typescript
// Subscribe to INSERT events on the todos table
const channel = supabase
  .channel('todos-changes')
  .on(
    'postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'todos' },
    (payload) => {
      console.log('New todo:', payload.new)
    }
  )
  .on(
    'postgres_changes',
    { event: 'UPDATE', schema: 'public', table: 'todos', filter: 'is_complete=eq.true' },
    (payload) => {
      console.log('Todo completed:', payload.new)
    }
  )
  .subscribe()

// Unsubscribe when done
supabase.removeChannel(channel)
```

### Realtime: Broadcast (Client-to-Client Messaging)

```typescript
// Create a broadcast channel
const room = supabase.channel('room-1')

// Send a message
room.send({
  type: 'broadcast',
  event: 'cursor-move',
  payload: { x: 120, y: 340, userId: 'abc' },
})

// Listen for messages
room.on('broadcast', { event: 'cursor-move' }, (payload) => {
  console.log('Cursor moved:', payload.payload)
}).subscribe()
```

### Realtime: Presence (Who Is Online)

```typescript
const room = supabase.channel('room-1')

// Track user presence
room.on('presence', { event: 'sync' }, () => {
  const state = room.presenceState()
  console.log('Online users:', Object.keys(state))
})

room.on('presence', { event: 'join' }, ({ key, newPresences }) => {
  console.log('Joined:', newPresences)
})

room.on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
  console.log('Left:', leftPresences)
})

// Subscribe and track
room.subscribe(async (status) => {
  if (status === 'SUBSCRIBED') {
    await room.track({
      user_id: 'abc',
      online_at: new Date().toISOString(),
    })
  }
})
```

## Output
- Auth: signUp, signIn (password, OAuth, magic link), session management, password reset
- Storage: upload, download, signed URLs, public URLs, bucket RLS policies
- Realtime: Postgres change subscriptions, broadcast messaging, presence tracking

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `AuthApiError: User already registered` | Duplicate signup | Use `signInWithPassword` instead |
| `AuthApiError: Invalid login credentials` | Wrong password/email | Verify credentials |
| `StorageApiError: Bucket not found` | Bucket does not exist | Create bucket in dashboard or migration |
| `StorageApiError: new row violates RLS` | Storage policy blocking | Check storage.objects RLS policies |
| `RealtimeSubscription: connection closed` | Network interruption | Channel auto-reconnects; handle `CLOSED` status |

## Resources
- [Auth Guide](https://supabase.com/docs/guides/auth)
- [Storage Guide](https://supabase.com/docs/guides/storage)
- [Realtime Guide](https://supabase.com/docs/guides/realtime)
- [Storage Access Control](https://supabase.com/docs/guides/storage/security/access-control)

## Next Steps
For common errors, see `supabase-common-errors`.
