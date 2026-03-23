---
name: supabase-auth-storage-realtime-core
description: |
  Implement Supabase Auth (signUp, signIn, OAuth, session management), Storage
  (upload, download, signed URLs, bucket policies), and Realtime (Postgres changes,
  broadcast, presence). Use when building user auth flows, file upload features,
  or live-updating UIs with Supabase. Trigger with phrases like "supabase auth",
  "supabase storage upload", "supabase realtime subscribe", "supabase oauth",
  "supabase file upload", "supabase presence", "supabase rls storage".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, cursor
tags: [saas, supabase, auth, storage, realtime, rls]
---

# Supabase Auth + Storage + Realtime Core

## Overview

Implement the three pillars that turn a Supabase database into a full application backend: user authentication (email/password, OAuth, magic links, session lifecycle), file storage (uploads, downloads, signed URLs, bucket-level RLS policies), and real-time subscriptions (Postgres change events, client-to-client broadcast, presence tracking). Every operation integrates with Row-Level Security through `auth.uid()`.

## Prerequisites

- Supabase project created at [supabase.com/dashboard](https://supabase.com/dashboard)
- `@supabase/supabase-js` v2 installed (`npm install @supabase/supabase-js`)
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` available from project Settings > API
- For Python: `pip install supabase` (wraps `postgrest-py`, `gotrue-py`, `storage3`, `realtime-py`)

## Instructions

### Step 1: Auth — User Registration, Login, and OAuth

Initialize the client and implement the three primary auth flows: email/password, OAuth provider, and passwordless magic link.

**TypeScript**

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// ── Sign up a new user ──
const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password-123',
  options: {
    data: { username: 'newuser', full_name: 'New User' },  // → raw_user_meta_data
  },
})
// If email confirmation enabled: data.user exists but data.session is null
// If email confirmation disabled: both data.user and data.session are present

// ── Sign in with password ──
const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password-123',
})
const { user, session } = signInData
// session.access_token → JWT for authenticated API calls

// ── Sign in with OAuth (Google) ──
const { data: oauthData, error: oauthError } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: 'https://myapp.com/auth/callback',
    queryParams: { access_type: 'offline', prompt: 'consent' },
  },
})
// Redirect user to oauthData.url in the browser

// ── Sign in with GitHub ──
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'github',
  options: { redirectTo: 'https://myapp.com/auth/callback' },
})

// ── Passwordless magic link ──
const { error: otpError } = await supabase.auth.signInWithOtp({
  email: 'user@example.com',
  options: { emailRedirectTo: 'https://myapp.com/auth/callback' },
})

// ── Handle OAuth/magic link callback (in /auth/callback route) ──
const { data: { session: cbSession }, error: cbError } =
  await supabase.auth.exchangeCodeForSession(code)
```

**Session management — every app needs these:**

```typescript
// Get current session (reads from local storage, no network call)
const { data: { session } } = await supabase.auth.getSession()

// Get current user (validates JWT against server)
const { data: { user } } = await supabase.auth.getUser()

// Listen for auth state changes — critical for reactive UIs
const { data: { subscription } } = supabase.auth.onAuthStateChange(
  (event, session) => {
    // event: 'SIGNED_IN' | 'SIGNED_OUT' | 'TOKEN_REFRESHED' | 'USER_UPDATED'
    //        'INITIAL_SESSION' | 'PASSWORD_RECOVERY' | 'MFA_CHALLENGE_VERIFIED'
    console.log('Auth event:', event, session?.user?.email)
  }
)
// Clean up when component unmounts
subscription.unsubscribe()

// Sign out (clears session from storage)
await supabase.auth.signOut()

// Password reset (sends email with reset link)
await supabase.auth.resetPasswordForEmail('user@example.com', {
  redirectTo: 'https://myapp.com/auth/reset-password',
})
```

**Python**

```python
from supabase import create_client

supabase = create_client(
    "https://your-project.supabase.co",
    "your-anon-key"
)

# Sign up
result = supabase.auth.sign_up({
    "email": "user@example.com",
    "password": "secure-password-123",
    "options": {"data": {"username": "newuser"}},
})

# Sign in with password
result = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "secure-password-123",
})
access_token = result.session.access_token

# Get current session
session = supabase.auth.get_session()

# Sign out
supabase.auth.sign_out()
```

### Step 2: Storage — Upload, Download, and Secure with Bucket Policies

Supabase Storage organizes files into buckets. Public buckets serve files via CDN URLs; private buckets require signed URLs or authenticated requests.

**TypeScript**

```typescript
// ── Upload a file ──
const file = new File(['hello world'], 'hello.txt', { type: 'text/plain' })
const { data, error } = await supabase.storage
  .from('avatars')  // bucket name
  .upload('user123/avatar.png', file, {
    cacheControl: '3600',
    upsert: false,       // true → overwrite existing
    contentType: 'image/png',
  })
// data.path → 'user123/avatar.png'

// ── Download a file ──
const { data: blob, error: dlError } = await supabase.storage
  .from('avatars')
  .download('user123/avatar.png')
// blob is a Blob object — use URL.createObjectURL(blob) for display

// ── Get public URL (public buckets only, no auth required) ──
const { data: { publicUrl } } = supabase.storage
  .from('avatars')
  .getPublicUrl('user123/avatar.png')
// publicUrl → 'https://<project>.supabase.co/storage/v1/object/public/avatars/user123/avatar.png'

// ── Create signed URL (private buckets, time-limited access) ──
const { data: signedUrlData, error: signError } = await supabase.storage
  .from('documents')
  .createSignedUrl('reports/q4-2025.pdf', 3600)  // expires in 1 hour
// signedUrlData.signedUrl → one-time use URL with token parameter

// ── List files in a path ──
const { data: files, error: listError } = await supabase.storage
  .from('documents')
  .list('reports', {
    limit: 100,
    offset: 0,
    sortBy: { column: 'name', order: 'asc' },
  })

// ── Delete files ──
const { error: removeError } = await supabase.storage
  .from('documents')
  .remove(['reports/old-report.pdf', 'reports/draft.docx'])
```

**Bucket RLS policies — enforce access control in SQL migrations:**

```sql
-- Create buckets (run in a migration or SQL editor)
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true);   -- public: anyone can read

INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', false);  -- private: signed URLs only

-- Allow authenticated users to upload to their own folder
-- Convention: store files at <user_id>/filename.ext
CREATE POLICY "avatar_upload"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'avatars'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- Allow anyone to view avatars (public bucket)
CREATE POLICY "avatar_public_read"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'avatars');

-- Allow users to manage only their own documents (all operations)
CREATE POLICY "documents_user_crud"
  ON storage.objects FOR ALL
  USING (
    bucket_id = 'documents'
    AND auth.uid()::text = (storage.foldername(name))[1]
  )
  WITH CHECK (
    bucket_id = 'documents'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- Allow users to delete only files they uploaded
CREATE POLICY "documents_owner_delete"
  ON storage.objects FOR DELETE
  USING (
    bucket_id = 'documents'
    AND auth.uid() = owner
  );
```

**Python**

```python
# Upload
with open("report.pdf", "rb") as f:
    result = supabase.storage.from_("documents").upload(
        "user123/report.pdf", f,
        {"content-type": "application/pdf", "cache-control": "3600"}
    )

# Download
data = supabase.storage.from_("documents").download("user123/report.pdf")

# Public URL
url = supabase.storage.from_("avatars").get_public_url("user123/avatar.png")

# Signed URL (3600 seconds)
result = supabase.storage.from_("documents").create_signed_url(
    "user123/report.pdf", 3600
)
signed_url = result["signedURL"]

# List files
files = supabase.storage.from_("documents").list("user123")

# Delete
supabase.storage.from_("documents").remove(["user123/old-file.pdf"])
```

### Step 3: Realtime — Postgres Changes, Broadcast, and Presence

Supabase Realtime provides three channel types: database change listeners, client-to-client broadcast, and presence tracking for online status.

**Postgres Changes (listen to INSERT/UPDATE/DELETE on tables):**

```typescript
// Subscribe to new messages in a chat table
const channel = supabase
  .channel('chat-room')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'messages',
    },
    (payload) => {
      console.log('New message:', payload.new)
      // payload.new → full row data
      // payload.old → null for INSERT
    }
  )
  .on(
    'postgres_changes',
    {
      event: 'UPDATE',
      schema: 'public',
      table: 'messages',
      filter: 'room_id=eq.42',  // server-side filter
    },
    (payload) => {
      console.log('Updated:', payload.old, '→', payload.new)
    }
  )
  .on(
    'postgres_changes',
    {
      event: 'DELETE',
      schema: 'public',
      table: 'messages',
    },
    (payload) => {
      console.log('Deleted:', payload.old)
      // payload.new → null for DELETE
    }
  )
  .subscribe((status) => {
    console.log('Channel status:', status)
    // 'SUBSCRIBED' | 'TIMED_OUT' | 'CLOSED' | 'CHANNEL_ERROR'
  })

// Enable Realtime on the table (required one-time setup in SQL)
// ALTER PUBLICATION supabase_realtime ADD TABLE messages;

// Unsubscribe when done
supabase.removeChannel(channel)
```

**RLS integration — Realtime respects row-level security:**

```sql
-- Only receive changes for rows the user owns
CREATE POLICY "users_own_messages"
  ON messages FOR SELECT
  USING (auth.uid() = user_id);

-- The Realtime listener will only fire for rows passing this policy
```

**Broadcast (client-to-client, no database involved):**

```typescript
const room = supabase.channel('collab-room')

// Listen for cursor movements from other users
room.on('broadcast', { event: 'cursor-move' }, ({ payload }) => {
  console.log(`User ${payload.userId} at (${payload.x}, ${payload.y})`)
})

// Subscribe first, then send
room.subscribe((status) => {
  if (status === 'SUBSCRIBED') {
    // Send cursor position to all other clients
    room.send({
      type: 'broadcast',
      event: 'cursor-move',
      payload: { userId: 'abc', x: 120, y: 340 },
    })
  }
})
```

**Presence (track who is online):**

```typescript
const room = supabase.channel('app-presence')

// Sync event fires whenever the presence state changes
room.on('presence', { event: 'sync' }, () => {
  const state = room.presenceState()
  // state → { 'user-abc': [{ user_id: 'abc', online_at: '...' }], ... }
  const onlineUsers = Object.keys(state)
  console.log('Online:', onlineUsers.length, 'users')
})

room.on('presence', { event: 'join' }, ({ key, newPresences }) => {
  console.log('Joined:', key, newPresences)
})

room.on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
  console.log('Left:', key, leftPresences)
})

// Subscribe and track this user's presence
room.subscribe(async (status) => {
  if (status === 'SUBSCRIBED') {
    await room.track({
      user_id: currentUser.id,
      username: currentUser.email,
      online_at: new Date().toISOString(),
    })
  }
})

// Untrack when leaving (e.g., on component unmount)
await room.untrack()
```

**Python Realtime:**

```python
# Python realtime uses callbacks (requires running event loop)
def handle_insert(payload):
    print("New row:", payload["new"])

channel = supabase.channel("room")
channel.on_postgres_changes(
    event="INSERT",
    schema="public",
    table="messages",
    callback=handle_insert,
)
channel.subscribe()

# When done
supabase.remove_channel(channel)
```

## Output

- Auth: user registration, password login, OAuth flow (Google/GitHub), magic link, session lifecycle with `onAuthStateChange`, password reset
- Storage: file upload/download, public URLs for CDN-served assets, time-limited signed URLs for private files, bucket-level RLS policies using `auth.uid()` and `storage.foldername()`
- Realtime: Postgres change subscriptions with server-side filters, broadcast channels for client-to-client messaging, presence tracking for online status

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `AuthApiError: User already registered` | Duplicate email signup | Use `signInWithPassword` or check existence first |
| `AuthApiError: Invalid login credentials` | Wrong email or password | Verify credentials; check email confirmation status |
| `AuthApiError: Email not confirmed` | User has not clicked confirmation link | Resend with `resend({ type: 'signup', email })` |
| `StorageApiError: Bucket not found` | Bucket does not exist | Create via dashboard or `INSERT INTO storage.buckets` |
| `StorageApiError: new row violates row-level security` | RLS policy blocking the operation | Verify `storage.objects` policies match the user and bucket |
| `StorageApiError: The resource already exists` | File exists and `upsert: false` | Set `upsert: true` to overwrite or use a unique path |
| `Realtime: channel error` or `TIMED_OUT` | Network issues or Realtime not enabled | Check `ALTER PUBLICATION supabase_realtime ADD TABLE <name>` |
| `Realtime: too many channels` | Exceeded concurrent channel limit | Unsubscribe unused channels with `removeChannel()` |

## Examples

**Full auth + protected upload flow:**

```typescript
// 1. Sign in
const { data: { session } } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password-123',
})

// 2. Upload avatar to user's folder (RLS enforces ownership)
const { data } = await supabase.storage
  .from('avatars')
  .upload(`${session.user.id}/avatar.png`, file, { upsert: true })

// 3. Get public URL for display
const { data: { publicUrl } } = supabase.storage
  .from('avatars')
  .getPublicUrl(`${session.user.id}/avatar.png`)

// 4. Subscribe to profile changes in real time
const channel = supabase
  .channel('profile-updates')
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'public',
    table: 'profiles',
    filter: `id=eq.${session.user.id}`,
  }, (payload) => {
    console.log('Profile updated:', payload.new)
  })
  .subscribe()
```

## Resources

- [Auth Guide](https://supabase.com/docs/guides/auth)
- [Auth API Reference](https://supabase.com/docs/reference/javascript/auth-signup)
- [Storage Guide](https://supabase.com/docs/guides/storage)
- [Storage Access Control](https://supabase.com/docs/guides/storage/security/access-control)
- [Realtime Guide](https://supabase.com/docs/guides/realtime)
- [Realtime Postgres Changes](https://supabase.com/docs/guides/realtime/postgres-changes)
- [Realtime Broadcast](https://supabase.com/docs/guides/realtime/broadcast)
- [Realtime Presence](https://supabase.com/docs/guides/realtime/presence)

## Next Steps

For common Supabase errors and debugging, see `supabase-common-errors`.
For database queries and CRUD operations, see `supabase-crud-core`.
