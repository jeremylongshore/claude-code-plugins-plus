# Supabase Auth — Full Walkthrough

Initialize the client and implement the three primary auth flows: email/password, OAuth provider, and passwordless magic link.

## TypeScript

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

## Session management — every app needs these

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

Python equivalents for every auth call: [python-examples.md](python-examples.md).
