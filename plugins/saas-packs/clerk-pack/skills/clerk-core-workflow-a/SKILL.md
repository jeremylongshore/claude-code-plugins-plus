---
name: clerk-core-workflow-a
description: |
  Implement user sign-up and sign-in flows with Clerk.
  Use when building authentication UI, customizing sign-in experience,
  or implementing OAuth social login.
  Trigger with phrases like "clerk sign-in", "clerk sign-up",
  "clerk login flow", "clerk OAuth", "clerk social login".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Core Workflow A: Sign-Up & Sign-In

## Overview
Implement comprehensive user authentication flows including pre-built components, custom forms, OAuth social login, and email verification.

## Prerequisites
- Clerk SDK installed and configured (`clerk-install-auth` completed)
- OAuth providers configured in Clerk Dashboard > User & Authentication > Social Connections
- Sign-in/sign-up URLs set in environment variables

## Instructions

### Step 1: Pre-built Components (Quick Start)
```typescript
// app/sign-in/[[...sign-in]]/page.tsx
import { SignIn } from '@clerk/nextjs'

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignIn
        appearance={{
          elements: {
            rootBox: 'mx-auto',
            card: 'shadow-lg',
          },
        }}
        routing="path"
        path="/sign-in"
        signUpUrl="/sign-up"
      />
    </div>
  )
}
```

```typescript
// app/sign-up/[[...sign-up]]/page.tsx
import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" />
    </div>
  )
}
```

Add environment variables for routing:
```bash
# .env.local
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/onboarding
```

### Step 2: Custom Sign-In Form
```typescript
'use client'
import { useSignIn } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export function CustomSignIn() {
  const { signIn, setActive, isLoaded } = useSignIn()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  if (!isLoaded) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const result = await signIn.create({
        identifier: email,
        password,
      })

      if (result.status === 'complete') {
        await setActive({ session: result.createdSessionId })
        router.push('/dashboard')
      }
    } catch (err: any) {
      setError(err.errors?.[0]?.message || 'Sign-in failed')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" required />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" required />
      {error && <p className="text-red-500">{error}</p>}
      <button type="submit">Sign In</button>
    </form>
  )
}
```

### Step 3: OAuth Social Login
```typescript
'use client'
import { useSignIn } from '@clerk/nextjs'

export function OAuthButtons() {
  const { signIn } = useSignIn()

  const signInWith = (strategy: 'oauth_google' | 'oauth_github' | 'oauth_apple') => {
    signIn?.authenticateWithRedirect({
      strategy,
      redirectUrl: '/sso-callback',
      redirectUrlComplete: '/dashboard',
    })
  }

  return (
    <div className="flex flex-col gap-2">
      <button onClick={() => signInWith('oauth_google')}>Continue with Google</button>
      <button onClick={() => signInWith('oauth_github')}>Continue with GitHub</button>
      <button onClick={() => signInWith('oauth_apple')}>Continue with Apple</button>
    </div>
  )
}
```

Create the SSO callback page:
```typescript
// app/sso-callback/page.tsx
import { AuthenticateWithRedirectCallback } from '@clerk/nextjs'

export default function SSOCallback() {
  return <AuthenticateWithRedirectCallback />
}
```

### Step 4: Email Verification Flow
```typescript
'use client'
import { useSignUp } from '@clerk/nextjs'
import { useState } from 'react'

export function EmailVerification() {
  const { signUp, setActive } = useSignUp()
  const [code, setCode] = useState('')
  const [pendingVerification, setPendingVerification] = useState(false)

  const handleSignUp = async (email: string, password: string) => {
    await signUp?.create({ emailAddress: email, password })
    await signUp?.prepareEmailAddressVerification({ strategy: 'email_code' })
    setPendingVerification(true)
  }

  const handleVerify = async () => {
    const result = await signUp?.attemptEmailAddressVerification({ code })
    if (result?.status === 'complete') {
      await setActive!({ session: result.createdSessionId })
    }
  }

  if (pendingVerification) {
    return (
      <div>
        <p>Check your email for a verification code</p>
        <input value={code} onChange={e => setCode(e.target.value)} placeholder="Enter code" />
        <button onClick={handleVerify}>Verify</button>
      </div>
    )
  }

  return <button onClick={() => handleSignUp('user@example.com', 'password123')}>Sign Up</button>
}
```

## Output
- Sign-in and sign-up pages with pre-built or custom UI
- OAuth social login buttons (Google, GitHub, Apple)
- Email verification flow with code confirmation
- Routing environment variables configured

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `form_identifier_not_found` | Email not registered | Show sign-up link or prompt |
| `form_password_incorrect` | Wrong password | Display error, offer password reset |
| `session_exists` | Already signed in | Redirect to dashboard |
| `verification_failed` | Wrong or expired code | Allow retry, offer resend |
| `oauth_callback_error` | OAuth misconfigured | Check redirect URIs in dashboard |

## Examples

### Multi-Factor Authentication Sign-In
```typescript
'use client'
import { useSignIn } from '@clerk/nextjs'
import { useState } from 'react'

export function MFASignIn() {
  const { signIn, setActive } = useSignIn()
  const [needsMFA, setNeedsMFA] = useState(false)
  const [mfaCode, setMfaCode] = useState('')

  const handleSignIn = async (email: string, password: string) => {
    const result = await signIn!.create({ identifier: email, password })

    if (result.status === 'needs_second_factor') {
      setNeedsMFA(true)
    } else if (result.status === 'complete') {
      await setActive!({ session: result.createdSessionId })
    }
  }

  const handleMFA = async () => {
    const result = await signIn!.attemptSecondFactor({
      strategy: 'totp',
      code: mfaCode,
    })
    if (result.status === 'complete') {
      await setActive!({ session: result.createdSessionId })
    }
  }

  if (needsMFA) {
    return (
      <div>
        <input value={mfaCode} onChange={e => setMfaCode(e.target.value)} placeholder="2FA Code" />
        <button onClick={handleMFA}>Verify</button>
      </div>
    )
  }

  return <button onClick={() => handleSignIn('user@example.com', 'pass')}>Sign In</button>
}
```

## Resources
- [Sign-In Component](https://clerk.com/docs/components/authentication/sign-in)
- [Custom Sign-In Flow](https://clerk.com/docs/custom-flows/email-password)
- [OAuth Configuration](https://clerk.com/docs/authentication/social-connections/overview)

## Next Steps
Proceed to `clerk-core-workflow-b` for session management and middleware.
