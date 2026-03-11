# Clerk Core Workflow A: Sign-Up & Sign-In - Implementation Guide

Detailed implementation examples and code patterns.

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
            formButtonPrimary: 'bg-blue-500 hover:bg-blue-600',
            card: 'shadow-lg'
          }
        }}
        routing="path"
        path="/sign-in"
        signUpUrl="/sign-up"
      />
    </div>
  )
}

// app/sign-up/[[...sign-up]]/page.tsx
import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignUp
        appearance={{
          elements: {
            formButtonPrimary: 'bg-green-500 hover:bg-green-600'
          }
        }}
        routing="path"
        path="/sign-up"
        signInUrl="/sign-in"
      />
    </div>
  )
}
```

### Step 2: Custom Sign-In Form
```typescript
'use client'
import { useSignIn } from '@clerk/nextjs'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export function CustomSignIn() {
  const { signIn, isLoaded, setActive } = useSignIn()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isLoaded) return

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
      setError(err.errors?.[0]?.message || 'Sign in failed')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
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

export function SocialLogin() {
  const { signIn, isLoaded } = useSignIn()

  const handleOAuth = async (provider: 'oauth_google' | 'oauth_github' | 'oauth_apple') => {
    if (!isLoaded) return

    await signIn.authenticateWithRedirect({
      strategy: provider,
      redirectUrl: '/sso-callback',
      redirectUrlComplete: '/dashboard'
    })
  }

  return (
    <div className="space-y-2">
      <button onClick={() => handleOAuth('oauth_google')}>
        Continue with Google
      </button>
      <button onClick={() => handleOAuth('oauth_github')}>
        Continue with GitHub
      </button>
      <button onClick={() => handleOAuth('oauth_apple')}>
        Continue with Apple
      </button>
    </div>
  )
}

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
  const { signUp, isLoaded, setActive } = useSignUp()
  const [verificationCode, setVerificationCode] = useState('')
  const [pendingVerification, setPendingVerification] = useState(false)

  const handleSignUp = async (email: string, password: string) => {
    if (!isLoaded) return

    await signUp.create({
      emailAddress: email,
      password,
    })

    // Send email verification
    await signUp.prepareEmailAddressVerification({
      strategy: 'email_code'
    })

    setPendingVerification(true)
  }

  const handleVerify = async () => {
    if (!isLoaded) return

    const result = await signUp.attemptEmailAddressVerification({
      code: verificationCode
    })

    if (result.status === 'complete') {
      await setActive({ session: result.createdSessionId })
    }
  }

  if (pendingVerification) {
    return (
      <div>
        <input
          value={verificationCode}
          onChange={(e) => setVerificationCode(e.target.value)}
          placeholder="Verification code"
        />
        <button onClick={handleVerify}>Verify</button>
      </div>
    )
  }

  return <SignUpForm onSubmit={handleSignUp} />
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| form_identifier_not_found | Email not registered | Show sign-up prompt |
| form_password_incorrect | Wrong password | Show error, offer reset |
| session_exists | Already signed in | Redirect to dashboard |
| verification_failed | Wrong code | Allow retry, resend code |

## Examples

### Magic Link Authentication
```typescript
const handleMagicLink = async (email: string) => {
  await signIn.create({
    identifier: email,
    strategy: 'email_link',
    redirectUrl: `${window.location.origin}/verify-magic-link`
  })
}

// app/verify-magic-link/page.tsx
import { EmailLinkComplete } from '@clerk/nextjs'

export default function VerifyMagicLink() {
  return <EmailLinkComplete />
}
```
