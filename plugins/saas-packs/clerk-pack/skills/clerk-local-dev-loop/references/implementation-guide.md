# Clerk Local Dev Loop - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Configure Development Instance
```bash
# Use development keys in .env.local
cat > .env.local << 'EOF'
# Development keys (start with pk_test_ and sk_test_)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Optional: Custom sign-in/sign-up URLs
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/onboarding
EOF
```

### Step 2: Set Up Test Users
```typescript
// scripts/create-test-user.ts
// Use Clerk Backend SDK for test user management
import { clerkClient } from '@clerk/nextjs/server'

async function createTestUser() {
  const user = await clerkClient.users.createUser({
    emailAddress: ['test@example.com'],
    password: 'testpassword123',
    firstName: 'Test',
    lastName: 'User'
  })
  console.log('Created test user:', user.id)
}
```

### Step 3: Configure Hot Reload
```typescript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Clerk works with fast refresh out of the box
  reactStrictMode: true,

  // Environment-specific configuration
  env: {
    CLERK_DOMAIN: process.env.NODE_ENV === 'development'
      ? 'clerk.your-dev-domain.com'
      : 'clerk.your-prod-domain.com'
  }
}

module.exports = nextConfig
```

### Step 4: Development Scripts
```json
{
  "scripts": {
    "dev": "next dev",
    "dev:https": "next dev --experimental-https",
    "clerk:dev": "npx @clerk/cli dev",
    "test:auth": "node scripts/test-auth.js"
  }
}
```

### Step 5: Mock Authentication for Tests
```typescript
// __tests__/setup.ts
import { vi } from 'vitest'

// Mock Clerk for unit tests
vi.mock('@clerk/nextjs', () => ({
  auth: () => ({ userId: 'test-user-id' }),
  currentUser: () => ({
    id: 'test-user-id',
    firstName: 'Test',
    emailAddresses: [{ emailAddress: 'test@example.com' }]
  }),
  useUser: () => ({
    user: { id: 'test-user-id', firstName: 'Test' },
    isLoaded: true,
    isSignedIn: true
  })
}))
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Development/Production mismatch | Using prod keys in dev | Use pk_test_/sk_test_ keys locally |
| SSL Required | Clerk needs HTTPS | Use `next dev --experimental-https` |
| Cookies Not Set | Wrong domain config | Check Clerk dashboard domain settings |
| Session Not Persisting | LocalStorage issues | Clear browser storage, check domain |

## Examples

### Environment Switching
```typescript
// lib/clerk.ts
export const clerkConfig = {
  publishableKey: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY!,
  signInUrl: process.env.NEXT_PUBLIC_CLERK_SIGN_IN_URL || '/sign-in',
  signUpUrl: process.env.NEXT_PUBLIC_CLERK_SIGN_UP_URL || '/sign-up',
}

// Validate configuration
if (!clerkConfig.publishableKey.startsWith('pk_')) {
  throw new Error('Invalid Clerk publishable key')
}
```

### Local Webhook Testing
```bash
# Use ngrok or similar for webhook testing
npx ngrok http 3000

# Update webhook URL in Clerk dashboard to ngrok URL
# https://abc123.ngrok.io/api/webhooks/clerk
```
