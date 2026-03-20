---
name: clerk-webhooks-events
description: |
  Configure Clerk webhooks and handle authentication events.
  Use when setting up user sync, handling auth events,
  or integrating Clerk with external systems.
  Trigger with phrases like "clerk webhooks", "clerk events",
  "clerk user sync", "clerk notifications", "clerk event handling".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Webhooks & Events

## Overview
Configure and handle Clerk webhooks for user lifecycle events and data synchronization. Clerk uses Svix for webhook delivery with signature verification.

## Prerequisites
- Clerk account with webhook access
- HTTPS endpoint for webhooks (use `ngrok` for local dev)
- `svix` package for signature verification

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
    throw new Error('Missing CLERK_WEBHOOK_SECRET env variable')
  }

  const headerPayload = await headers()
  const svix_id = headerPayload.get('svix-id')
  const svix_timestamp = headerPayload.get('svix-timestamp')
  const svix_signature = headerPayload.get('svix-signature')

  if (!svix_id || !svix_timestamp || !svix_signature) {
    return new Response('Missing svix headers', { status: 400 })
  }

  const payload = await req.json()
  const body = JSON.stringify(payload)

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
    return new Response('Invalid signature', { status: 400 })
  }

  return handleWebhookEvent(evt)
}
```

### Step 3: Implement Event Handlers
```typescript
// app/api/webhooks/clerk/route.ts (continued)
async function handleWebhookEvent(evt: WebhookEvent) {
  const eventType = evt.type

  switch (eventType) {
    case 'user.created': {
      const { id, email_addresses, first_name, last_name, image_url } = evt.data
      const email = email_addresses[0]?.email_address
      await db.user.create({
        data: { clerkId: id, email, firstName: first_name, lastName: last_name, avatarUrl: image_url },
      })
      break
    }

    case 'user.updated': {
      const { id, email_addresses, first_name, last_name } = evt.data
      await db.user.update({
        where: { clerkId: id },
        data: { email: email_addresses[0]?.email_address, firstName: first_name, lastName: last_name },
      })
      break
    }

    case 'user.deleted': {
      const { id } = evt.data
      await db.user.delete({ where: { clerkId: id! } })
      break
    }

    case 'organization.created': {
      const { id, name, slug } = evt.data
      await db.organization.create({ data: { clerkOrgId: id, name, slug } })
      break
    }

    case 'session.created': {
      console.log(`New session for user: ${evt.data.user_id}`)
      break
    }

    default:
      console.log(`Unhandled webhook event: ${eventType}`)
  }

  return new Response('OK', { status: 200 })
}
```

### Step 4: Implement Idempotency
```typescript
// lib/webhook-idempotency.ts
const processedEvents = new Map<string, number>()

export async function isEventProcessed(svixId: string): Promise<boolean> {
  // In production, use Redis or your database
  if (processedEvents.has(svixId)) return true

  // Check database for persistent idempotency
  const existing = await db.webhookEvent.findUnique({
    where: { svixId },
  })
  return !!existing
}

export async function markEventProcessed(svixId: string, eventType: string): Promise<void> {
  processedEvents.set(svixId, Date.now())
  await db.webhookEvent.create({
    data: { svixId, eventType, processedAt: new Date() },
  })
}
```

### Step 5: Configure Webhook in Clerk Dashboard
1. Go to **Clerk Dashboard > Webhooks > Add Endpoint**
2. Set endpoint URL: `https://yourdomain.com/api/webhooks/clerk`
3. Select events: `user.created`, `user.updated`, `user.deleted`, `organization.created`
4. Copy the **Signing Secret** to your `.env`:
```bash
# .env.local
CLERK_WEBHOOK_SECRET=whsec_...
```

## Output
- Webhook endpoint verifying Svix signatures
- Event handlers syncing users, orgs, and sessions to your database
- Idempotency protection against duplicate events
- Environment variable configured with webhook secret

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong `CLERK_WEBHOOK_SECRET` | Re-copy secret from Clerk Dashboard |
| Missing svix headers | Request not from Clerk | Verify sender; check endpoint URL |
| Duplicate processing | Clerk retried delivery | Implement idempotency with svix-id |
| Handler timeout | Slow DB operations | Offload to background job queue |

## Examples

### Express.js Webhook Endpoint
```typescript
import express from 'express'
import { Webhook } from 'svix'

const app = express()

app.post('/api/webhooks/clerk', express.raw({ type: 'application/json' }), (req, res) => {
  const wh = new Webhook(process.env.CLERK_WEBHOOK_SECRET!)
  try {
    const evt = wh.verify(req.body, {
      'svix-id': req.headers['svix-id'] as string,
      'svix-timestamp': req.headers['svix-timestamp'] as string,
      'svix-signature': req.headers['svix-signature'] as string,
    })
    console.log('Webhook event:', evt)
    res.status(200).json({ received: true })
  } catch (err) {
    res.status(400).json({ error: 'Invalid signature' })
  }
})
```

## Resources
- [Clerk Webhooks Guide](https://clerk.com/docs/integrations/webhooks/overview)
- [Svix Verification Docs](https://docs.svix.com/receiving/verifying-payloads/how)
- [Webhook Event Types](https://clerk.com/docs/integrations/webhooks/sync-data)

## Next Steps
Proceed to `clerk-performance-tuning` for optimization strategies.
