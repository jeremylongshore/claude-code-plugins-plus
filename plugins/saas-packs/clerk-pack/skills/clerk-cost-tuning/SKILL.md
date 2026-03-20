---
name: clerk-cost-tuning
description: |
  Optimize Clerk costs and understand pricing.
  Use when planning budget, reducing costs,
  or understanding Clerk pricing model.
  Trigger with phrases like "clerk cost", "clerk pricing",
  "reduce clerk cost", "clerk billing", "clerk budget".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Cost Tuning

## Overview
Understand Clerk pricing and optimize costs. Clerk charges by Monthly Active Users (MAU). Covers pricing tiers, MAU reduction strategies, caching to reduce API calls, and usage monitoring.

## Prerequisites
- Clerk account active
- Understanding of MAU (Monthly Active Users)
- Application usage patterns known

## Instructions

### Step 1: Understand Clerk Pricing Model

| Plan | Price | MAU Included | Extra MAU |
|------|-------|-------------|-----------|
| Free | $0/mo | 10,000 MAU | N/A |
| Pro | $25/mo | 10,000 MAU | $0.02/MAU |
| Enterprise | Custom | Custom | Custom |

Key pricing concepts:
- **MAU** = unique user who authenticates at least once per month
- Users who only visit public pages are not counted
- Bot/crawler sessions are not counted
- Test/development instances are free and unlimited

### Step 2: Reduce MAU Count
```typescript
// Strategy 1: Defer authentication — don't force sign-in until necessary
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const requiresAuth = createRouteMatcher([
  '/dashboard(.*)',
  '/settings(.*)',
  '/api/protected(.*)',
])

export default clerkMiddleware(async (auth, req) => {
  // Only require auth for specific routes (not entire site)
  if (requiresAuth(req)) {
    await auth.protect()
  }
})
```

```typescript
// Strategy 2: Use anonymous access for read-only features
// app/blog/[slug]/page.tsx
import { auth } from '@clerk/nextjs/server'

export default async function BlogPost({ params }: { params: { slug: string } }) {
  const { userId } = await auth() // Check but don't require
  const post = await db.post.findUnique({ where: { slug: params.slug } })

  return (
    <article>
      <h1>{post?.title}</h1>
      <div>{post?.content}</div>
      {userId ? <CommentForm /> : <p>Sign in to comment</p>}
    </article>
  )
}
```

### Step 3: Cache to Reduce API Calls
```typescript
// lib/user-cache.ts
import { cache } from 'react'
import { currentUser } from '@clerk/nextjs/server'

// Deduplicate within single request (free)
export const getUser = cache(async () => {
  return currentUser()
})

// Cross-request caching reduces Backend API calls
import { unstable_cache } from 'next/cache'
import { clerkClient } from '@clerk/nextjs/server'

export const getUserMetadata = unstable_cache(
  async (userId: string) => {
    const client = await clerkClient()
    const user = await client.users.getUser(userId)
    return user.publicMetadata
  },
  ['user-metadata'],
  { revalidate: 600 } // 10-minute cache
)
```

### Step 4: Monitor Usage
```typescript
// app/api/admin/clerk-usage/route.ts
import { auth, clerkClient } from '@clerk/nextjs/server'

export async function GET() {
  const { has } = await auth()
  if (!has({ role: 'org:admin' })) {
    return Response.json({ error: 'Admin only' }, { status: 403 })
  }

  const client = await clerkClient()
  const users = await client.users.getUserList({ limit: 1 })

  return Response.json({
    totalUsers: users.totalCount,
    // Estimate MAU based on recent sign-ins
    estimatedMAU: 'Check Clerk Dashboard > Billing for actual MAU',
    dashboardUrl: 'https://dashboard.clerk.com/last-active?after=30d',
  })
}
```

### Step 5: Clean Up Inactive Users
```typescript
// scripts/cleanup-inactive-users.ts
import { createClerkClient } from '@clerk/backend'

const clerk = createClerkClient({ secretKey: process.env.CLERK_SECRET_KEY! })

async function findInactiveUsers(daysInactive = 90) {
  const cutoff = Date.now() - daysInactive * 24 * 60 * 60 * 1000
  const allUsers = await clerk.users.getUserList({ limit: 500 })

  const inactive = allUsers.data.filter(
    (user) => (user.lastSignInAt || 0) < cutoff
  )

  console.log(`Found ${inactive.length} users inactive for ${daysInactive}+ days`)
  console.log('Consider: notification campaign, data export, or account cleanup')

  return inactive
}

findInactiveUsers()
```

## Output
- Pricing model understood with MAU thresholds
- Route-level auth to minimize unnecessary MAU counts
- Request-level and cross-request caching reducing API calls
- Usage monitoring endpoint for admins
- Inactive user identification script

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected bill increase | MAU spike from bot traffic | Add bot detection, restrict auth to needed routes |
| Feature limitations | Free tier limits (no SSO, etc.) | Upgrade to Pro ($25/mo) |
| High API call volume | No caching | Add React `cache()` + `unstable_cache()` |
| MAU count mismatch | Counting test users | Use separate dev instance (free, unlimited) |

## Examples

### Cost Estimation Script
```typescript
function estimateMonthlyCost(mau: number): string {
  if (mau <= 10_000) return 'Free tier ($0/mo)'
  const overage = mau - 10_000
  const cost = 25 + overage * 0.02
  return `Pro tier: $${cost.toFixed(2)}/mo (${overage.toLocaleString()} extra MAU at $0.02 each)`
}

console.log(estimateMonthlyCost(15_000))  // "Pro tier: $125.00/mo (5,000 extra MAU at $0.02 each)"
console.log(estimateMonthlyCost(50_000))  // "Pro tier: $825.00/mo (40,000 extra MAU at $0.02 each)"
```

## Resources
- [Clerk Pricing](https://clerk.com/pricing)
- [Clerk Usage Dashboard](https://dashboard.clerk.com)
- [Clerk Fair Use Policy](https://clerk.com/legal/fair-use-policy)

## Next Steps
Proceed to `clerk-reference-architecture` for architecture patterns.
