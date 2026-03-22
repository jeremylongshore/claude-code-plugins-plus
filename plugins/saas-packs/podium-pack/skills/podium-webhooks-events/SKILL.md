---
name: podium-webhooks-events
description: |
  Podium webhooks events — business messaging and communication platform integration.
  Use when working with Podium API for messaging, reviews, or payments.
  Trigger with phrases like "podium webhooks events", "podium-webhooks-events".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, podium, messaging, reviews, payments]
compatible-with: claude-code, codex, openclaw
---

# Podium Webhooks Events

## Overview
Handle Podium webhook events for messages, reviews, and payments with event routing and idempotent processing.

## Prerequisites
- Podium OAuth tokens configured
- HTTPS webhook endpoint

## Instructions

### Step 1: Webhook Event Types
| Event | Description |
|-------|-------------|
| `message.received` | Inbound customer message |
| `message.sent` | Outbound message delivered |
| `message.failed` | Message delivery failed |
| `review.created` | New review posted |
| `payment.completed` | Invoice payment received |

### Step 2: Event Handler
```typescript
import express from 'express';

const app = express();
app.post('/webhooks/podium', express.json(), async (req, res) => {
  const { type, data } = req.body;

  const handlers: Record<string, (data: any) => Promise<void>> = {
    'message.received': async (d) => {
      console.log(`Message from ${d.attributes['contact-phone']}: ${d.attributes.body}`);
    },
    'message.sent': async (d) => {
      console.log(`Message delivered: ${d.id}`);
    },
    'review.created': async (d) => {
      console.log(`New review: ${d.attributes.rating}/5`);
    },
    'payment.completed': async (d) => {
      console.log(`Payment received: $${d.attributes.amount / 100}`);
    },
  };

  const handler = handlers[type];
  if (handler) await handler(data);
  res.status(200).json({ received: true });
});
```

### Step 3: Register Webhook
```typescript
await podium.post('/webhooks', {
  data: {
    attributes: {
      url: 'https://your-app.com/webhooks/podium',
      events: ['message.received', 'message.sent', 'review.created', 'payment.completed'],
    },
  },
});
```

## Output
- Webhook endpoint handling all Podium event types
- Event routing to specific handlers
- Message, review, and payment events processed

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No events received | Wrong URL | Verify HTTPS URL in webhook config |
| Duplicate events | Retry delivery | Implement idempotency with event IDs |
| Handler timeout | Slow processing | Offload to background queue |

## Resources
- [Podium Webhooks](https://docs.podium.com/docs/webhooks)
- [Webhook Object](https://docs.podium.com/reference/the-webhook-object)

## Next Steps
For error diagnosis, see `podium-common-errors`.
