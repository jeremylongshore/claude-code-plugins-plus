# Supabase Auth + Storage + Realtime — Combined Examples

## Full auth + protected upload flow

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
