# Clerk Multi-Environment Setup - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Create Clerk Instances

Create separate Clerk instances for each environment in the Clerk Dashboard:
- `myapp-dev` - Development
- `myapp-staging` - Staging
- `myapp-prod` - Production

### Step 2: Environment Configuration

```bash
# .env.development.local
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_dev_...
CLERK_SECRET_KEY=sk_test_dev_...
NEXT_PUBLIC_APP_ENV=development

# .env.staging.local
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_staging_...
CLERK_SECRET_KEY=sk_test_staging_...
NEXT_PUBLIC_APP_ENV=staging

# .env.production.local
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
NEXT_PUBLIC_APP_ENV=production
```

### Step 3: Environment-Aware Configuration
```typescript
// lib/clerk-config.ts
type Environment = 'development' | 'staging' | 'production'

interface ClerkConfig {
  signInUrl: string
  signUpUrl: string
  afterSignInUrl: string
  afterSignUpUrl: string
  debug: boolean
}

const configs: Record<Environment, ClerkConfig> = {
  development: {
    signInUrl: '/sign-in',
    signUpUrl: '/sign-up',
    afterSignInUrl: '/dashboard',
    afterSignUpUrl: '/onboarding',
    debug: true
  },
  staging: {
    signInUrl: '/sign-in',
    signUpUrl: '/sign-up',
    afterSignInUrl: '/dashboard',
    afterSignUpUrl: '/onboarding',
    debug: true
  },
  production: {
    signInUrl: '/sign-in',
    signUpUrl: '/sign-up',
    afterSignInUrl: '/dashboard',
    afterSignUpUrl: '/onboarding',
    debug: false
  }
}

export function getClerkConfig(): ClerkConfig {
  const env = (process.env.NEXT_PUBLIC_APP_ENV as Environment) || 'development'
  return configs[env]
}

// Validate environment at startup
export function validateClerkEnvironment() {
  const pk = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  const env = process.env.NEXT_PUBLIC_APP_ENV

  if (env === 'production' && pk?.startsWith('pk_test_')) {
    throw new Error('Production environment using test keys!')
  }

  if (env !== 'production' && pk?.startsWith('pk_live_')) {
    console.warn('Non-production environment using live keys')
  }
}
```

### Step 4: ClerkProvider Configuration
```typescript
// app/layout.tsx
import { ClerkProvider } from '@clerk/nextjs'
import { getClerkConfig, validateClerkEnvironment } from '@/lib/clerk-config'

// Validate on startup
validateClerkEnvironment()

export default function RootLayout({ children }) {
  const config = getClerkConfig()

  return (
    <ClerkProvider
      signInUrl={config.signInUrl}
      signUpUrl={config.signUpUrl}
      afterSignInUrl={config.afterSignInUrl}
      afterSignUpUrl={config.afterSignUpUrl}
    >
      <html>
        <body>
          {config.debug && <EnvironmentBanner />}
          {children}
        </body>
      </html>
    </ClerkProvider>
  )
}

function EnvironmentBanner() {
  const env = process.env.NEXT_PUBLIC_APP_ENV

  if (env === 'production') return null

  const colors = {
    development: 'bg-green-500',
    staging: 'bg-yellow-500'
  }

  return (
    <div className={`${colors[env]} text-white text-center text-sm py-1`}>
      {env?.toUpperCase()} ENVIRONMENT
    </div>
  )
}
```

### Step 5: Webhook Configuration Per Environment
```typescript
// app/api/webhooks/clerk/route.ts
import { headers } from 'next/headers'

const WEBHOOK_SECRETS = {
  development: process.env.CLERK_WEBHOOK_SECRET_DEV,
  staging: process.env.CLERK_WEBHOOK_SECRET_STAGING,
  production: process.env.CLERK_WEBHOOK_SECRET
}

export async function POST(req: Request) {
  const env = process.env.NEXT_PUBLIC_APP_ENV as keyof typeof WEBHOOK_SECRETS
  const WEBHOOK_SECRET = WEBHOOK_SECRETS[env]

  if (!WEBHOOK_SECRET) {
    console.error(`No webhook secret for environment: ${env}`)
    return Response.json({ error: 'Configuration error' }, { status: 500 })
  }

  // ... rest of webhook handling
}
```

### Step 6: CI/CD Environment Promotion
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main, staging]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set environment
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "DEPLOY_ENV=production" >> $GITHUB_ENV
            echo "CLERK_PUBLISHABLE_KEY=${{ secrets.CLERK_PUBLISHABLE_KEY_PROD }}" >> $GITHUB_ENV
            echo "CLERK_SECRET_KEY=${{ secrets.CLERK_SECRET_KEY_PROD }}" >> $GITHUB_ENV
          else
            echo "DEPLOY_ENV=staging" >> $GITHUB_ENV
            echo "CLERK_PUBLISHABLE_KEY=${{ secrets.CLERK_PUBLISHABLE_KEY_STAGING }}" >> $GITHUB_ENV
            echo "CLERK_SECRET_KEY=${{ secrets.CLERK_SECRET_KEY_STAGING }}" >> $GITHUB_ENV
          fi

      - name: Build
        run: npm run build
        env:
          NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: ${{ env.CLERK_PUBLISHABLE_KEY }}
          NEXT_PUBLIC_APP_ENV: ${{ env.DEPLOY_ENV }}

      - name: Deploy to Vercel
        run: vercel deploy --prod
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
```

### Step 7: User Data Isolation
```typescript
// lib/user-sync.ts
// Ensure user data doesn't leak between environments

export async function syncUser(clerkUser: any) {
  const env = process.env.NEXT_PUBLIC_APP_ENV

  await db.user.upsert({
    where: {
      clerkId_environment: {
        clerkId: clerkUser.id,
        environment: env
      }
    },
    update: { /* ... */ },
    create: {
      clerkId: clerkUser.id,
      environment: env,
      // ... other fields
    }
  })
}
```
