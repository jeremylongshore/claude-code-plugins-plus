# Clerk Cost Tuning - Implementation Guide

Detailed implementation examples and code patterns.

## Clerk Pricing Model

### Pricing Tiers (as of February 2026)

| Tier | MRU Included | Price | Features |
|------|--------------|-------|----------|
| Free (Hobby) | 50,000 | $0 | Basic auth, 3 social connections, custom domain, unlimited apps |
| Pro | 50,000 | $25/mo ($20/mo billed annually) | Remove Clerk branding, passkeys, MFA, custom email templates |
| Business | 50,000 | $300/mo ($250/mo billed annually) | 10 dashboard seats, SOC 2 report, priority support |
| Enterprise | Custom | Custom | SSO, SLA, dedicated support |

### Per-User Pricing (after included MRU)

- Pro: $0.02 per MRU above 50,000 (volume discounts at higher tiers)

### What Counts as MRU?

- A user who returns to your app 24+ hours after signing up ("first day free")
- Users who sign up and never come back = not counted
- Multiple visits in a month = counted once

## Cost Optimization Strategies

### Strategy 1: Reduce Unnecessary Sessions

```typescript
// lib/session-optimization.ts
import { auth } from '@clerk/nextjs/server'

// Use session efficiently - avoid creating multiple sessions
export async function getOrCreateSession() {
  const { userId, sessionId } = await auth()

  // Prefer existing session over creating new ones
  if (sessionId) {
    return { userId, sessionId, isNew: false }
  }

  // Only create session when absolutely needed
  return { userId, sessionId: null, isNew: true }
}

// Configure session lifetime appropriately
// Clerk Dashboard > Configure > Sessions
// Longer sessions = fewer re-authentications
```

### Strategy 2: Implement Guest Users

```typescript
// lib/guest-users.ts
// Use guest mode for non-essential features to reduce MRU

export function useGuestOrAuth() {
  const { userId, isLoaded, isSignedIn } = useUser()

  // Allow limited functionality without sign-in
  const guestId = useMemo(() => {
    if (typeof window === 'undefined') return null
    let id = localStorage.getItem('guest_id')
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem('guest_id', id)
    }
    return id
  }, [])

  return {
    userId: isSignedIn ? userId : null,
    guestId: !isSignedIn ? guestId : null,
    isGuest: !isSignedIn && !!guestId,
    isLoaded
  }
}

// Use guest ID for features that don't require auth
export async function savePreference(key: string, value: any) {
  const { userId, guestId } = useGuestOrAuth()

  if (userId) {
    // Authenticated - save to user profile
    await saveToUserProfile(userId, key, value)
  } else if (guestId) {
    // Guest - save to localStorage (no Clerk MRU cost)
    localStorage.setItem(`pref_${key}`, JSON.stringify(value))
  }
}
```

### Strategy 3: Defer Authentication

```typescript
// Delay requiring sign-in until necessary
'use client'
import { useUser, SignInButton } from '@clerk/nextjs'

export function FeatureGate({ children, requiresAuth = false }) {
  const { isSignedIn, isLoaded } = useUser()

  // If feature doesn't require auth, show it
  if (!requiresAuth) {
    return children
  }

  if (!isLoaded) {
    return <Skeleton />
  }

  if (!isSignedIn) {
    return (
      <div className="p-4 border rounded">
        <p>Sign in to access this feature</p>
        <SignInButton mode="modal">
          <button className="btn">Sign In</button>
        </SignInButton>
      </div>
    )
  }

  return children
}

// Usage - only accrue MRU when user accesses premium features
function App() {
  return (
    <div>
      {/* Free features - no sign-in required */}
      <PublicContent />

      {/* Premium features - sign-in required */}
      <FeatureGate requiresAuth>
        <PremiumContent />
      </FeatureGate>
    </div>
  )
}
```

### Strategy 4: Reduce API Calls

```typescript
// lib/batched-clerk.ts
import { clerkClient } from '@clerk/nextjs/server'

// Batch user lookups to reduce API calls
export async function batchGetUsers(userIds: string[]) {
  if (userIds.length === 0) return []

  const client = await clerkClient()

  // Single API call instead of multiple getUser calls
  const { data: users } = await client.users.getUserList({
    userId: userIds,
    limit: 100
  })

  return users
}

// Cache organization data
const orgCache = new Map<string, any>()

export async function getOrganization(orgId: string) {
  if (orgCache.has(orgId)) {
    return orgCache.get(orgId)
  }

  const client = await clerkClient()
  const org = await client.organizations.getOrganization({ organizationId: orgId })

  orgCache.set(orgId, org)
  return org
}
```

### Strategy 5: Monitor and Alert

```typescript
// lib/cost-monitoring.ts
import { clerkClient } from '@clerk/nextjs/server'

export async function getMonthlyUsageEstimate() {
  const client = await clerkClient()

  // Get unique users this month
  const startOfMonth = new Date()
  startOfMonth.setDate(1)
  startOfMonth.setHours(0, 0, 0, 0)

  const { totalCount } = await client.users.getUserList({
    limit: 1,
    // Note: You may need to track this yourself
  })

  // Estimate cost
  const includedMRU = 50000 // Free (Hobby) and Pro tiers
  const extraUsers = Math.max(0, totalCount - includedMRU)
  const estimatedCost = 25 + (extraUsers * 0.02)

  return {
    totalUsers: totalCount,
    includedMRU,
    extraUsers,
    estimatedCost,
    percentageUsed: (totalCount / includedMRU) * 100
  }
}

// Alert when approaching limits
export async function checkUsageAlerts() {
  const usage = await getMonthlyUsageEstimate()

  if (usage.percentageUsed > 80) {
    await sendAlert(`Clerk usage at ${usage.percentageUsed}% of included MRU`)
  }
}
```

## Cost Reduction Checklist

- [ ] Review session lifetime settings (longer = fewer re-auths)
- [ ] Implement guest mode for non-essential features
- [ ] Defer authentication until necessary
- [ ] Batch API calls
- [ ] Cache user/org data aggressively
- [ ] Monitor MRU usage regularly
- [ ] Remove inactive users periodically
- [ ] Use webhooks instead of polling

## Pricing Calculator

```typescript
// Calculate monthly cost
function estimateMonthlyCost(
  tier: 'free' | 'pro' | 'enterprise',
  expectedMRU: number
): number {
  switch (tier) {
    case 'free':
      return expectedMRU <= 50000 ? 0 : Infinity // Upgrade required
    case 'pro':
      const includedMRU = 50000
      const basePrice = 25
      const extraUsers = Math.max(0, expectedMRU - includedMRU)
      return basePrice + (extraUsers * 0.02)
    case 'enterprise':
      return -1 // Contact sales
  }
}

// Examples
console.log(estimateMonthlyCost('free', 20000))  // $0
console.log(estimateMonthlyCost('pro', 60000))   // $225
console.log(estimateMonthlyCost('pro', 100000))  // $1025
```
