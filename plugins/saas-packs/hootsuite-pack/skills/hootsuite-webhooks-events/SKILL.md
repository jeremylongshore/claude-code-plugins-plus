---
name: hootsuite-webhooks-events
description: |
  Implement Hootsuite webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Hootsuite event notifications securely.
  Trigger with phrases like "hootsuite webhook", "hootsuite events",
  "hootsuite webhook signature", "handle hootsuite events", "hootsuite notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite Webhooks & Events

## Overview

Hootsuite provides webhook notifications for social stream events when building Hootsuite App Directory integrations. For API-only integrations, you poll for message state changes or implement your own scheduling system with callbacks.

## Instructions

### Step 1: Poll for Message Status Changes

```typescript
// Since Hootsuite REST API doesn't push webhooks for message status,
// poll for changes to scheduled messages
async function pollMessageStatus(messageId: string, intervalMs = 30000) {
  const check = async () => {
    const response = await fetch(`https://platform.hootsuite.com/v1/messages/${messageId}`, {
      headers: { 'Authorization': `Bearer ${await getStoredToken()}` },
    });
    const { data } = await response.json();

    if (data.state === 'SENT') {
      console.log(`Message ${messageId} sent at ${data.sentAt}`);
      return data;
    } else if (data.state === 'FAILED' || data.state === 'REJECTED') {
      console.error(`Message ${messageId} failed: ${data.state}`);
      return data;
    }

    console.log(`Message ${messageId}: ${data.state}, checking again...`);
    await new Promise(r => setTimeout(r, intervalMs));
    return check();
  };

  return check();
}
```

### Step 2: Build Custom Scheduling Webhook

```typescript
// Your own webhook system to track scheduled post status
import express from 'express';

const app = express();
app.use(express.json());

// Cron job checks scheduled posts and fires webhooks
async function checkScheduledPosts() {
  const response = await fetch('https://platform.hootsuite.com/v1/messages?state=SENT&limit=50', {
    headers: { 'Authorization': `Bearer ${await getStoredToken()}` },
  });
  const { data } = await response.json();

  for (const msg of data) {
    // Notify your systems about sent posts
    await fetch(process.env.INTERNAL_WEBHOOK_URL!, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event: 'post.sent', messageId: msg.id, sentAt: msg.sentAt, text: msg.text }),
    });
  }
}
```

### Step 3: Hootsuite App Directory Webhooks

For apps listed in the Hootsuite App Directory, you receive stream events:

```typescript
// Webhook handler for Hootsuite App Directory integration
app.post('/webhooks/hootsuite', async (req, res) => {
  const { type, data } = req.body;
  switch (type) {
    case 'message.sent': console.log('Post sent:', data); break;
    case 'message.failed': console.error('Post failed:', data); break;
    case 'stream.message': console.log('New social message:', data); break;
  }
  res.status(200).json({ received: true });
});
```

## Resources

- [Hootsuite Developer Platform](https://developer.hootsuite.com/docs/the-hootsuite-platform)
- [API Guides](https://developer.hootsuite.com/docs/api-guides)

## Next Steps

For performance, see `hootsuite-performance-tuning`.
