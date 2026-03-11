# Clerk Webhooks & Events - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Install Dependencies
```bash
npm install svix
```

### Step 2: Create Webhook Endpoint
```typescript
// app/api/webhooks/clerk/route.ts
import { Webhook } from 'svix'
import { headers } from 'next/headers'
import { WebhookEvent } from '@clerk/nextjs/server'

export async function POST(req: Request) {
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET

  if (!WEBHOOK_SECRET) {
    throw new Error('CLERK_WEBHOOK_SECRET not set')
  }

  // Get Svix headers
  const headerPayload = await headers()
  const svix_id = headerPayload.get('svix-id')
  const svix_timestamp = headerPayload.get('svix-timestamp')
  const svix_signature = headerPayload.get('svix-signature')

  if (!svix_id || !svix_timestamp || !svix_signature) {
    return Response.json({ error: 'Missing headers' }, { status: 400 })
  }

  // Get body
  const payload = await req.json()
  const body = JSON.stringify(payload)

  // Verify webhook
  const wh = new Webhook(WEBHOOK_SECRET)
  let evt: WebhookEvent

  try {
    evt = wh.verify(body, {
      'svix-id': svix_id,
      'svix-timestamp': svix_timestamp,
      'svix-signature': svix_signature,
    }) as WebhookEvent
  } catch (err) {
    console.error('Webhook verification failed:', err)
    return Response.json({ error: 'Invalid signature' }, { status: 400 })
  }

  // Handle event
  const eventType = evt.type
  console.log(`Received webhook: ${eventType}`)

  switch (eventType) {
    case 'user.created':
      await handleUserCreated(evt.data)
      break
    case 'user.updated':
      await handleUserUpdated(evt.data)
      break
    case 'user.deleted':
      await handleUserDeleted(evt.data)
      break
    case 'session.created':
      await handleSessionCreated(evt.data)
      break
    case 'organization.created':
      await handleOrgCreated(evt.data)
      break
    default:
      console.log(`Unhandled event type: ${eventType}`)
  }

  return Response.json({ success: true })
}
```

### Step 3: Implement Event Handlers
```typescript
// lib/webhook-handlers.ts
import { db } from './db'

interface ClerkUserData {
  id: string
  email_addresses: Array<{ email_address: string; id: string }>
  first_name: string | null
  last_name: string | null
  image_url: string
  created_at: number
  updated_at: number
}

export async function handleUserCreated(data: ClerkUserData) {
  const primaryEmail = data.email_addresses.find(
    e => e.id === data.primary_email_address_id
  )?.email_address

  await db.user.create({
    data: {
      clerkId: data.id,
      email: primaryEmail,
      firstName: data.first_name,
      lastName: data.last_name,
      imageUrl: data.image_url,
      createdAt: new Date(data.created_at)
    }
  })

  // Send welcome email
  await sendWelcomeEmail(primaryEmail)

  console.log(`User created: ${data.id}`)
}

export async function handleUserUpdated(data: ClerkUserData) {
  const primaryEmail = data.email_addresses.find(
    e => e.id === data.primary_email_address_id
  )?.email_address

  await db.user.update({
    where: { clerkId: data.id },
    data: {
      email: primaryEmail,
      firstName: data.first_name,
      lastName: data.last_name,
      imageUrl: data.image_url,
      updatedAt: new Date(data.updated_at)
    }
  })

  console.log(`User updated: ${data.id}`)
}

export async function handleUserDeleted(data: { id: string }) {
  await db.user.delete({
    where: { clerkId: data.id }
  })

  // Clean up user data
  await cleanupUserData(data.id)

  console.log(`User deleted: ${data.id}`)
}

export async function handleSessionCreated(data: any) {
  // Log session for analytics
  await db.sessionLog.create({
    data: {
      userId: data.user_id,
      sessionId: data.id,
      createdAt: new Date(data.created_at),
      userAgent: data.user_agent
    }
  })

  console.log(`Session created: ${data.id}`)
}

export async function handleOrgCreated(data: any) {
  await db.organization.create({
    data: {
      clerkOrgId: data.id,
      name: data.name,
      slug: data.slug,
      createdAt: new Date(data.created_at)
    }
  })

  console.log(`Organization created: ${data.id}`)
}
```

### Step 4: Idempotency and Error Handling
```typescript
// lib/webhook-idempotency.ts
import { Redis } from '@upstash/redis'

const redis = Redis.fromEnv()

export async function processWithIdempotency(
  eventId: string,
  handler: () => Promise<void>
) {
  const key = `webhook:${eventId}`

  // Check if already processed
  const processed = await redis.get(key)
  if (processed) {
    console.log(`Event ${eventId} already processed`)
    return { skipped: true }
  }

  try {
    await handler()

    // Mark as processed (expire after 24 hours)
    await redis.set(key, 'processed', { ex: 86400 })

    return { success: true }
  } catch (error) {
    // Log error but don't mark as processed
    console.error(`Failed to process ${eventId}:`, error)
    throw error
  }
}

// Usage in webhook handler
export async function POST(req: Request) {
  // ... verification code ...

  const svix_id = headerPayload.get('svix-id')!

  const result = await processWithIdempotency(svix_id, async () => {
    switch (evt.type) {
      case 'user.created':
        await handleUserCreated(evt.data)
        break
      // ... other handlers
    }
  })

  return Response.json(result)
}
```

### Step 5: Configure Webhook in Clerk Dashboard
1. Go to Clerk Dashboard > Webhooks
2. Add endpoint URL: `https://yourdomain.com/api/webhooks/clerk`
3. Select events:
   - `user.created`
   - `user.updated`
   - `user.deleted`
   - `session.created`
   - `session.ended`
   - `organization.*` (if using organizations)
4. Copy webhook secret to environment

## Available Events

| Event | Description |
|-------|-------------|
| `user.created` | New user signed up |
| `user.updated` | User profile changed |
| `user.deleted` | User account deleted |
| `session.created` | New session started |
| `session.ended` | Session terminated |
| `session.revoked` | Session manually revoked |
| `organization.created` | Org created |
| `organization.updated` | Org settings changed |
| `organization.deleted` | Org deleted |
| `organizationMembership.*` | Member added/removed |
| `email.created` | Email verification sent |

## Testing Webhooks Locally

```bash
# Use ngrok for local testing
npx ngrok http 3000

# Or use Clerk CLI
npx @clerk/cli dev

# Test with curl
curl -X POST http://localhost:3000/api/webhooks/clerk \
  -H "Content-Type: application/json" \
  -H "svix-id: test" \
  -H "svix-timestamp: $(date +%s)" \
  -H "svix-signature: v1,..." \
  -d '{"type":"user.created","data":{}}'
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret | Verify CLERK_WEBHOOK_SECRET |
| Missing headers | Request not from Clerk | Check sender is Clerk |
| Duplicate processing | Event sent twice | Implement idempotency |
| Timeout | Handler too slow | Use background jobs |
