---
name: podium-core-workflow-a
description: |
  Podium core workflow a — business messaging and communication platform integration.
  Use when working with Podium API for messaging, reviews, or payments.
  Trigger with phrases like "podium core workflow a", "podium-core-workflow-a".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, podium, messaging, reviews, payments]
compatible-with: claude-code, codex, openclaw
---

# Podium Core Workflow A

## Overview
Build a complete messaging workflow with Podium: send messages, receive inbound messages via webhooks, and manage conversation threads.

## Prerequisites
- Completed `podium-install-auth` with OAuth tokens
- Webhook endpoint accessible via HTTPS

## Instructions

### Step 1: Set Up Webhook for Inbound Messages
```typescript
import express from 'express';
const app = express();

app.post('/webhooks/podium', express.json(), async (req, res) => {
  const event = req.body;
  if (event.type === 'message.received') {
    const msg = event.data;
    console.log(`From: ${msg.attributes['contact-phone']}`);
    console.log(`Body: ${msg.attributes.body}`);
    // Auto-reply or route to agent
    await sendReply(msg.attributes['location-uid'], msg.attributes['contact-phone'], 'Thanks for reaching out!');
  }
  res.status(200).json({ received: true });
});
```

### Step 2: Register Webhook with Podium
```typescript
const { data } = await podium.post('/webhooks', {
  data: {
    attributes: {
      url: 'https://your-app.com/webhooks/podium',
      events: ['message.received', 'message.sent', 'message.failed'],
    },
  },
});
console.log(`Webhook registered: ${data.data.id}`);
```

### Step 3: Send Reply Messages
```typescript
async function sendReply(locationId: string, phone: string, body: string) {
  const { data } = await podium.post(`/locations/${locationId}/messages`, {
    data: { attributes: { body, 'contact-phone': phone } },
  });
  return data.data.id;
}
```

## Output
- Webhook receiving inbound messages
- Auto-reply capability
- Two-way messaging via Podium

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Webhook not firing | URL not HTTPS | Use HTTPS endpoint |
| Message failed | Invalid phone | Verify E.164 format |
| No events received | Wrong event types | Check webhook configuration |

## Resources
- [Sync Messages](https://docs.podium.com/docs/sync-messages-from-podium-conversations)
- [Webhooks Guide](https://docs.podium.com/docs/webhooks)

## Next Steps
Reviews and payments: `podium-core-workflow-b`
