---
name: framer-webhooks-events
description: |
  Implement Framer webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Framer event notifications securely.
  Trigger with phrases like "framer webhook", "framer events",
  "framer webhook signature", "handle framer events", "framer notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Webhooks & Events

## Overview

Framer's Server API uses a WebSocket channel for real-time communication, not traditional REST webhooks. For event-driven integrations, you subscribe to changes via the WebSocket connection or set up your own webhook endpoints that trigger Framer sync via the Server API.

## Instructions

### Step 1: Subscribe to CMS Changes via Server API

```typescript
import { framer } from 'framer-api';

async function watchChanges() {
  const client = await framer.connect({
    apiKey: process.env.FRAMER_API_KEY!,
    siteId: process.env.FRAMER_SITE_ID!,
  });

  // Subscribe to collection changes
  const collections = await client.getCollections();
  for (const col of collections) {
    col.subscribe((items) => {
      console.log(`Collection "${col.name}" updated: ${items.length} items`);
    });
  }
}
```

### Step 2: External Webhook → Framer Sync

```typescript
// Receive webhook from your CMS, sync to Framer
import express from 'express';
import { framer } from 'framer-api';

const app = express();
app.use(express.json());

app.post('/webhooks/cms-update', async (req, res) => {
  const { event, data } = req.body;

  // Validate webhook source
  const signature = req.headers['x-webhook-signature'];
  if (!verifySignature(req.body, signature as string)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  if (event === 'content.updated') {
    const client = await framer.connect({
      apiKey: process.env.FRAMER_API_KEY!,
      siteId: process.env.FRAMER_SITE_ID!,
    });

    const col = (await client.getCollections()).find(c => c.name === data.collection);
    if (col) {
      await col.setItems(data.items.map(i => ({ fieldData: i })));
      await client.publish();
      console.log(`Synced ${data.items.length} items and published`);
    }
  }

  res.json({ received: true });
});
```

### Step 3: Plugin Event Subscriptions

```tsx
// Inside a Framer plugin — subscribe to canvas changes
import { framer } from 'framer-plugin';

// Watch for selection changes
framer.subscribeToSelection((selection) => {
  console.log('Selection changed:', selection.length, 'layers');
});

// Watch for code file changes
framer.subscribeToCodeFiles((codeFiles) => {
  console.log('Code files updated:', codeFiles.map(f => f.name));
});
```

## Output

- WebSocket-based real-time CMS subscriptions
- External webhook handler triggering Framer sync
- Plugin event subscriptions for canvas changes

## Resources

- [Framer Server API](https://www.framer.com/developers/server-api-introduction)
- [Plugin Subscriptions](https://www.framer.com/developers/reference)

## Next Steps

For performance, see `framer-performance-tuning`.
