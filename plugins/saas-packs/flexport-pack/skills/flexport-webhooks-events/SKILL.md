---
name: flexport-webhooks-events
description: |
  Implement Flexport webhook event handling for shipment milestones, booking updates,
  purchase order events, and invoice notifications.
  Trigger: "flexport webhooks", "flexport events", "flexport milestones",
  "flexport shipment tracking webhook".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Webhooks & Events

## Overview

Flexport sends webhook notifications for shipment milestones, booking confirmations, PO updates, invoice events, and document availability. Webhooks are configured in Portal > Settings with a secret token for HMAC-SHA256 signature verification via the `X-Hub-Signature` header.

## Webhook Event Types

| Category | Events | Use Case |
|----------|--------|----------|
| Milestones | `cargo_ready`, `departed`, `arrived`, `customs_cleared`, `delivered` | Shipment tracking |
| Transit | `estimated_departure`, `estimated_arrival`, `actual_departure` | ETA updates |
| Bookings | `booking_confirmed`, `booking_amended` | Booking lifecycle |
| Purchase Orders | `po_created`, `po_updated`, `po_archived` | PO management |
| Invoices | `invoice_created`, `freight_invoice_ready` | Billing |
| Documents | `document_uploaded`, `bill_of_lading_ready` | Document management |
| Container | `container_loaded`, `container_unloaded` | Container tracking |

## Instructions

### Step 1: Create Webhook Endpoint in Flexport

Navigate to Portal > Settings > Webhooks > Add Endpoint:
- URL: `https://your-app.com/webhooks/flexport`
- Secret: Generate a strong random string
- Events: Select event types to subscribe to

### Step 2: Implement Webhook Handler

```typescript
import crypto from 'crypto';
import express from 'express';

const app = express();

// IMPORTANT: Use raw body for signature verification
app.post('/webhooks/flexport', express.raw({ type: '*/*' }), async (req, res) => {
  // Step 1: Verify signature
  const signature = req.headers['x-hub-signature'] as string;
  const expected = 'sha256=' + crypto
    .createHmac('sha256', process.env.FLEXPORT_WEBHOOK_SECRET!)
    .update(req.body)
    .digest('hex');

  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    console.error('Invalid webhook signature');
    return res.status(401).send('Invalid signature');
  }

  // Step 2: Parse and route event
  const event = JSON.parse(req.body.toString());
  console.log(`Webhook: ${event.type} | ID: ${event.data?.id}`);

  try {
    await routeEvent(event);
    res.status(200).send('OK');
  } catch (err) {
    console.error('Webhook processing failed:', err);
    res.status(500).send('Processing error');
    // Dead letter: store for retry
  }
});

// Step 3: Route events to handlers
async function routeEvent(event: { type: string; data: any }) {
  switch (event.type) {
    case 'shipment.milestone':
      await handleMilestone(event.data);
      break;
    case 'shipment.eta_updated':
      await handleETAUpdate(event.data);
      break;
    case 'booking.confirmed':
      await handleBookingConfirmed(event.data);
      break;
    case 'invoice.created':
      await handleInvoice(event.data);
      break;
    case 'document.uploaded':
      await handleDocument(event.data);
      break;
    default:
      console.log(`Unhandled event type: ${event.type}`);
  }
}
```

### Step 3: Handle Shipment Milestones

```typescript
async function handleMilestone(data: {
  shipment_id: string;
  milestone: string;
  occurred_at: string;
  location?: { name: string; country: string };
}) {
  console.log(`Milestone: ${data.milestone} for ${data.shipment_id}`);
  console.log(`  At: ${data.occurred_at} | Location: ${data.location?.name}`);

  // Update your database
  await db.shipments.update({
    where: { flexportId: data.shipment_id },
    data: {
      status: data.milestone,
      lastMilestoneAt: new Date(data.occurred_at),
      currentLocation: data.location?.name,
    },
  });

  // Notify stakeholders for key milestones
  if (['departed', 'arrived', 'delivered'].includes(data.milestone)) {
    await notifyStakeholders(data.shipment_id, data.milestone);
  }
}
```

### Step 4: Idempotent Processing

```typescript
// Flexport may retry webhooks — ensure idempotent handling
async function processWebhookIdempotently(event: any) {
  const eventId = event.id || crypto.createHash('sha256')
    .update(JSON.stringify(event)).digest('hex');

  // Check if already processed
  const exists = await db.webhookLog.findUnique({ where: { eventId } });
  if (exists) {
    console.log(`Duplicate webhook ${eventId}, skipping`);
    return;
  }

  await db.$transaction([
    db.webhookLog.create({ data: { eventId, type: event.type, processedAt: new Date() } }),
    routeEvent(event),
  ]);
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 401 signature mismatch | Wrong secret or body parsing | Use `express.raw()`, verify secret matches Portal |
| Duplicate events | Flexport retries on timeout | Implement idempotency with event ID dedup |
| Missing events | Endpoint unreachable | Monitor uptime, use dead letter queue |
| Slow processing | Complex handler logic | Acknowledge fast (200), process async |

## Resources

- [Flexport Webhook API](https://apidocs.flexport.com/v2/tag/Webhook-Endpoints/)
- [Flexport Developer Portal](https://developers.flexport.com/)

## Next Steps

For performance optimization, see `flexport-performance-tuning`.
