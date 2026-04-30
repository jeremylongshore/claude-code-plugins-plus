---
name: navan-webhooks-events
description: 'Set up webhook listeners for real-time Navan event notifications.

  Use when you need to receive booking, expense, or travel disruption events from
  Navan.

  Trigger with "navan webhooks", "navan events", "navan webhook setup".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Webhooks & Events

## Overview
Navan supports asynchronous event delivery via callback URLs registered through the REST API. Since there is no public SDK, webhook handlers receive raw HTTP POST requests with JSON payloads. This skill covers endpoint setup, payload verification, event routing, and idempotent processing for the key event types: booking lifecycle, expense workflow, and travel disruptions.

## Prerequisites
- Active Navan account with API credentials (Admin > Travel admin > Settings > Integrations)
- OAuth 2.0 access token (see `navan-install-auth`)
- Publicly accessible HTTPS endpoint for callback URL (use ngrok for local development)
- Node.js 18+ with Express or equivalent HTTP framework

## Instructions

### Step 1: Register a Webhook Callback URL
```typescript
const response = await fetch('https://api.navan.com/v1/webhooks', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    url: 'https://your-domain.com/webhooks/navan',
    events: [
      'booking.created',
      'booking.updated',
      'booking.cancelled',
      'expense.submitted',
      'expense.approved',
      'expense.rejected',
      'trip.disrupted'
    ],
    secret: process.env.NAVAN_WEBHOOK_SECRET
  })
});
const webhook = await response.json();
console.log('Webhook registered:', webhook.id);
```

### Step 2: Verify Payload Signatures
```typescript
import crypto from 'node:crypto';

function verifySignature(payload: string, signature: string, secret: string): boolean {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}
```

### Step 3: Build the Webhook Handler
```typescript
import express from 'express';
const app = express();

// Track processed events for idempotency
const processedEvents = new Set<string>();

app.post('/webhooks/navan', express.raw({ type: 'application/json' }), async (req, res) => {
  const signature = req.headers['x-navan-signature'] as string;
  const rawBody = req.body.toString();

  // Verify authenticity
  if (!verifySignature(rawBody, signature, process.env.NAVAN_WEBHOOK_SECRET!)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Acknowledge immediately — process async
  res.status(200).json({ received: true });

  const event = JSON.parse(rawBody);

  // Idempotency check — Navan may retry on timeout
  if (processedEvents.has(event.id)) return;
  processedEvents.add(event.id);

  // Route by event type
  switch (event.type) {
    case 'booking.created':
      await handleNewBooking(event.data);
      break;
    case 'expense.submitted':
      await handleExpenseSubmission(event.data);
      break;
    case 'trip.disrupted':
      await handleDisruption(event.data);
      break;
    default:
      console.log('Unhandled event type:', event.type);
  }
});
```

### Step 4: Handle Key Event Types
```typescript
async function handleNewBooking(data: {
  booking_id: string;
  traveler_email: string;
  trip_type: 'flight' | 'hotel' | 'car';
  total_cost: number;
  currency: string;
}) {
  // Notify travel manager, update internal systems
  console.log(`New ${data.trip_type} booking: ${data.booking_id} — $${data.total_cost}`);
}

async function handleExpenseSubmission(data: {
  expense_id: string;
  submitter_email: string;
  amount: number;
  category: string;
}) {
  // Route to approval workflow
  console.log(`Expense submitted: ${data.expense_id} — $${data.amount} (${data.category})`);
}

async function handleDisruption(data: {
  trip_id: string;
  disruption_type: 'cancellation' | 'delay' | 'gate_change';
  severity: 'low' | 'medium' | 'high';
  affected_travelers: string[];
}) {
  // Trigger alerts for high-severity disruptions
  if (data.severity === 'high') {
    console.log(`ALERT: ${data.disruption_type} affecting ${data.affected_travelers.length} travelers`);
  }
}
```

## Output
A running webhook endpoint that receives real-time Navan events, verifies payload authenticity, deduplicates retries, and routes events to typed handler functions. The handler acknowledges receipt immediately (HTTP 200) and processes events asynchronously to avoid timeout-triggered retries.

## Error Handling
| Error | Code | Solution |
|-------|------|----------|
| Invalid signature | 401 | Verify `NAVAN_WEBHOOK_SECRET` matches the secret used during registration |
| Endpoint unreachable | N/A | Ensure HTTPS is valid and publicly accessible; check firewall rules |
| Duplicate events | N/A | Implement idempotency using event ID tracking (Set, Redis, or database) |
| Payload timeout | 408 | Respond with 200 before processing; handle work asynchronously |
| Webhook disabled | 410 | Re-register the callback URL; Navan disables after repeated failures |

## Examples

**List registered webhooks:**
```bash
curl -s -H "Authorization: Bearer $NAVAN_ACCESS_TOKEN" \
  https://api.navan.com/v1/webhooks | python3 -m json.tool
```

**Delete a webhook:**
```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $NAVAN_ACCESS_TOKEN" \
  https://api.navan.com/v1/webhooks/WEBHOOK_ID
```

**Test with ngrok for local development:**
```bash
ngrok http 3000
# Use the HTTPS URL as your callback URL when registering
```

## Resources
- [Navan Help Center](https://app.navan.com/app/helpcenter) — Official documentation and support
- [Navan Integrations](https://navan.com/integrations) — Available integration partners and setup guides
- [Navan Security](https://navan.com/security) — Compliance certifications and data handling policies

## Next Steps
After setting up webhooks, see `navan-rate-limits` to add throttling to your event processing pipeline, or `navan-security-basics` for credential rotation and SSO hardening.
