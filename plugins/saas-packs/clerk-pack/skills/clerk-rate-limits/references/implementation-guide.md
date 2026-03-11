# Clerk Rate Limits - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Understand Rate Limits

#### Clerk API Rate Limits (as of 2024)
| Endpoint Category | Free Tier | Pro Tier | Enterprise |
|------------------|-----------|----------|------------|
| Authentication | 100/min | 500/min | Custom |
| User Management | 100/min | 500/min | Custom |
| Session Management | 200/min | 1000/min | Custom |
| Webhooks | Unlimited | Unlimited | Unlimited |

#### Client-Side Limits
- SDK requests are automatically throttled
- Browser session: 10 requests/second
- Token refresh: 1 per 50 seconds (automatic)

### Step 2: Implement Rate Limit Handling
```typescript
// lib/clerk-client.ts
import { clerkClient } from '@clerk/nextjs/server'

interface RateLimitConfig {
  maxRetries: number
  baseDelay: number
}

async function withRateLimitRetry<T>(
  operation: () => Promise<T>,
  config: RateLimitConfig = { maxRetries: 3, baseDelay: 1000 }
): Promise<T> {
  let lastError: Error | null = null

  for (let attempt = 0; attempt < config.maxRetries; attempt++) {
    try {
      return await operation()
    } catch (error: any) {
      lastError = error

      // Check for rate limit error
      if (error.status === 429 || error.code === 'rate_limit_exceeded') {
        const delay = config.baseDelay * Math.pow(2, attempt)
        console.warn(`Rate limited, retrying in ${delay}ms (attempt ${attempt + 1})`)
        await new Promise(resolve => setTimeout(resolve, delay))
        continue
      }

      // Non-rate-limit error, throw immediately
      throw error
    }
  }

  throw lastError
}

// Usage
export async function getUser(userId: string) {
  const client = await clerkClient()
  return withRateLimitRetry(() => client.users.getUser(userId))
}
```

### Step 3: Batch Operations
```typescript
// lib/clerk-batch.ts
import { clerkClient } from '@clerk/nextjs/server'

// Instead of multiple individual calls
async function getBatchedUsers(userIds: string[]) {
  const client = await clerkClient()

  // Use getUserList with userId filter (single API call)
  const { data: users } = await client.users.getUserList({
    userId: userIds,
    limit: 100
  })

  return users
}

// Paginated fetching with rate limit awareness
async function getAllUsers(batchSize = 100, delayMs = 100) {
  const client = await clerkClient()
  const allUsers = []
  let offset = 0

  while (true) {
    const { data: users, totalCount } = await client.users.getUserList({
      limit: batchSize,
      offset
    })

    allUsers.push(...users)
    offset += batchSize

    if (allUsers.length >= totalCount) break

    // Rate limit friendly delay
    await new Promise(resolve => setTimeout(resolve, delayMs))
  }

  return allUsers
}
```

### Step 4: Caching Strategy
```typescript
// lib/clerk-cache.ts
import { unstable_cache } from 'next/cache'
import { clerkClient } from '@clerk/nextjs/server'

// Cache user data to reduce API calls
export const getCachedUser = unstable_cache(
  async (userId: string) => {
    const client = await clerkClient()
    return client.users.getUser(userId)
  },
  ['clerk-user'],
  {
    revalidate: 60, // Cache for 60 seconds
    tags: ['clerk-users']
  }
)

// In-memory cache for high-frequency lookups
const userCache = new Map<string, { user: any; timestamp: number }>()
const CACHE_TTL = 30000 // 30 seconds

export async function getUserWithCache(userId: string) {
  const cached = userCache.get(userId)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.user
  }

  const client = await clerkClient()
  const user = await client.users.getUser(userId)

  userCache.set(userId, { user, timestamp: Date.now() })
  return user
}
```

### Step 5: Monitor Rate Limit Usage
```typescript
// lib/clerk-monitor.ts
interface RateLimitMetrics {
  endpoint: string
  remaining: number
  limit: number
  resetAt: Date
}

const metrics: RateLimitMetrics[] = []

export function trackRateLimit(response: Response) {
  const remaining = response.headers.get('x-ratelimit-remaining')
  const limit = response.headers.get('x-ratelimit-limit')
  const reset = response.headers.get('x-ratelimit-reset')

  if (remaining && limit) {
    metrics.push({
      endpoint: response.url,
      remaining: parseInt(remaining),
      limit: parseInt(limit),
      resetAt: reset ? new Date(parseInt(reset) * 1000) : new Date()
    })

    // Alert if approaching limit
    if (parseInt(remaining) < parseInt(limit) * 0.1) {
      console.warn('Approaching rate limit:', {
        remaining,
        limit,
        endpoint: response.url
      })
    }
  }
}

export function getRateLimitMetrics() {
  return metrics.slice(-100) // Last 100 entries
}
```

## Rate Limit Headers

```
x-ratelimit-limit: 100
x-ratelimit-remaining: 95
x-ratelimit-reset: 1704067200
```
