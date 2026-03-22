---
name: hubspot-webhooks-events
description: |
  Implement HubSpot webhook subscriptions and CRM event handling.
  Use when setting up webhook endpoints for CRM events, implementing
  signature verification, or handling contact/deal/company change notifications.
  Trigger with phrases like "hubspot webhook", "hubspot events",
  "hubspot subscription", "handle hubspot notifications", "hubspot CRM events".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Webhooks & Events

## Overview

Set up HubSpot webhook subscriptions for CRM events (contact/company/deal creation, updates, deletions) with v3 signature verification and idempotent event handling.

## Prerequisites

- HubSpot public app (webhooks require a public app, not a private app)
- Client secret from your app settings (for signature verification)
- HTTPS endpoint accessible from the internet
- Optional: Redis or database for idempotency

## Instructions

### Step 1: Understand HubSpot Webhook Events

HubSpot sends webhook events as batches of CRM change notifications:

```json
[
  {
    "eventId": 100,
    "subscriptionId": 1234,
    "portalId": 12345678,
    "appId": 98765,
    "occurredAt": 1711234567890,
    "subscriptionType": "contact.propertyChange",
    "attemptNumber": 0,
    "objectId": 123,
    "propertyName": "lifecyclestage",
    "propertyValue": "marketingqualifiedlead",
    "changeSource": "CRM",
    "sourceId": "userId:12345"
  }
]
```

**Available subscription types:**
- `contact.creation`, `contact.deletion`, `contact.propertyChange`, `contact.privacyDeletion`
- `company.creation`, `company.deletion`, `company.propertyChange`
- `deal.creation`, `deal.deletion`, `deal.propertyChange`
- `ticket.creation`, `ticket.deletion`, `ticket.propertyChange`
- `contact.merge`, `company.merge`, `deal.merge`
- `contact.associationChange`, `company.associationChange`, `deal.associationChange`

### Step 2: Set Up Webhook Endpoint with Signature Verification

```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();

// IMPORTANT: Use raw body for signature verification
app.post('/webhooks/hubspot',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    // Verify signature (v3)
    const signature = req.headers['x-hubspot-signature-v3'] as string;
    const timestamp = req.headers['x-hubspot-request-timestamp'] as string;

    if (!signature || !timestamp) {
      // Fall back to v2 signature
      const sigV2 = req.headers['x-hubspot-signature'] as string;
      if (!verifySignatureV2(req.body.toString(), sigV2)) {
        return res.status(401).json({ error: 'Invalid signature' });
      }
    } else {
      const requestUri = `https://${req.headers.host}${req.originalUrl}`;
      if (!verifySignatureV3(req.body.toString(), signature, timestamp, requestUri)) {
        return res.status(401).json({ error: 'Invalid signature' });
      }
    }

    // HubSpot sends events as an array
    const events: HubSpotWebhookEvent[] = JSON.parse(req.body.toString());

    // Respond immediately (HubSpot expects < 5 second response)
    res.status(200).json({ received: true });

    // Process events asynchronously
    processEvents(events).catch(err =>
      console.error('Event processing failed:', err)
    );
  }
);
```

### Step 3: Signature Verification Functions

```typescript
const CLIENT_SECRET = process.env.HUBSPOT_CLIENT_SECRET!;

// v3 signature (preferred)
function verifySignatureV3(
  body: string, signature: string, timestamp: string, requestUri: string
): boolean {
  // Reject timestamps older than 5 minutes
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - parseInt(timestamp)) > 300) return false;

  const sourceString = `POST${requestUri}${body}${timestamp}`;
  const expected = crypto
    .createHmac('sha256', CLIENT_SECRET)
    .update(sourceString)
    .digest('base64');

  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

// v2 signature (fallback)
function verifySignatureV2(body: string, signature: string): boolean {
  const sourceString = CLIENT_SECRET + body;
  const expected = crypto
    .createHash('sha256')
    .update(sourceString)
    .digest('hex');

  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}
```

### Step 4: Event Handler with Idempotency

```typescript
interface HubSpotWebhookEvent {
  eventId: number;
  subscriptionId: number;
  portalId: number;
  appId: number;
  occurredAt: number;
  subscriptionType: string;
  attemptNumber: number;
  objectId: number;
  propertyName?: string;
  propertyValue?: string;
  changeSource?: string;
}

// Track processed events to prevent duplicates
const processedEvents = new Set<number>();

async function processEvents(events: HubSpotWebhookEvent[]): Promise<void> {
  for (const event of events) {
    // Idempotency: skip already-processed events
    if (processedEvents.has(event.eventId)) {
      console.log(`Skipping duplicate event: ${event.eventId}`);
      continue;
    }

    try {
      await handleEvent(event);
      processedEvents.add(event.eventId);

      // Clean up old event IDs (keep last 10,000)
      if (processedEvents.size > 10000) {
        const oldest = [...processedEvents].slice(0, 5000);
        oldest.forEach(id => processedEvents.delete(id));
      }
    } catch (error) {
      console.error(`Failed to process event ${event.eventId}:`, error);
    }
  }
}

async function handleEvent(event: HubSpotWebhookEvent): Promise<void> {
  const { subscriptionType, objectId, propertyName, propertyValue } = event;

  switch (subscriptionType) {
    case 'contact.creation':
      console.log(`New contact created: ${objectId}`);
      // Sync to your database, send welcome email, etc.
      break;

    case 'contact.propertyChange':
      console.log(`Contact ${objectId}: ${propertyName} = ${propertyValue}`);
      if (propertyName === 'lifecyclestage' && propertyValue === 'customer') {
        // Trigger onboarding workflow
      }
      break;

    case 'deal.propertyChange':
      if (propertyName === 'dealstage') {
        console.log(`Deal ${objectId} moved to stage: ${propertyValue}`);
        // Notify sales team, update dashboard, etc.
      }
      break;

    case 'deal.creation':
      console.log(`New deal created: ${objectId}`);
      break;

    case 'contact.deletion':
    case 'contact.privacyDeletion':
      console.log(`Contact ${objectId} deleted`);
      // Remove from your systems (GDPR compliance)
      break;

    default:
      console.log(`Unhandled event: ${subscriptionType} for object ${objectId}`);
  }
}
```

### Step 5: Register Webhook Subscriptions

Subscriptions are configured in your HubSpot public app settings, or via API:

```typescript
// Create webhook subscription via API
async function createSubscription(
  appId: number,
  subscriptionType: string,
  propertyName?: string
) {
  const client = new hubspot.Client({
    accessToken: process.env.HUBSPOT_DEVELOPER_API_KEY!,
  });

  await client.apiRequest({
    method: 'POST',
    path: `/webhooks/v3/${appId}/subscriptions`,
    body: {
      eventType: subscriptionType,
      propertyName: propertyName || undefined,
      active: true,
    },
  });
}

// Example: Subscribe to lifecycle stage changes
await createSubscription(appId, 'contact.propertyChange', 'lifecyclestage');
await createSubscription(appId, 'deal.creation');
await createSubscription(appId, 'deal.propertyChange', 'dealstage');
```

## Output

- Webhook endpoint with v3 signature verification
- Event handler for contact, company, deal, and ticket events
- Idempotent processing preventing duplicate handling
- Replay protection via timestamp validation

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong client secret | Verify in App Settings > Auth |
| Duplicate events | HubSpot retries | Implement event ID tracking |
| Timeout (no 200 response) | Slow processing | Respond immediately, process async |
| Missing events | Subscription inactive | Check subscription status in app settings |
| `attemptNumber > 0` | Previous delivery failed | Normal retry behavior -- process normally |

## Examples

### Test Webhooks Locally

```bash
# Use ngrok to expose local server
ngrok http 3000

# Update webhook URL in HubSpot app settings:
# https://xxxx.ngrok.io/webhooks/hubspot

# Trigger a test: create a contact in HubSpot UI
# Watch your local logs for the webhook event
```

## Resources

- [HubSpot Webhooks API Guide](https://developers.hubspot.com/docs/guides/api/webhooks/overview)
- [Webhook Signature Verification](https://developers.hubspot.com/docs/guides/api/webhooks/validating-requests)
- [Webhook Subscription Types](https://developers.hubspot.com/changelog/new-subscription-types-for-webhooks)

## Next Steps

For performance optimization, see `hubspot-performance-tuning`.
