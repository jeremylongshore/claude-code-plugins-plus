---
name: mindtickle-webhooks-events
description: |
  Webhooks Events for MindTickle.
  Trigger: "mindtickle webhooks events".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Webhooks & Events

## Webhook Handler
```typescript
app.post('/webhooks/mindtickle', (req, res) => {
  // Verify signature
  const event = req.body;
  console.log(`Event: ${event.type}`);
  res.status(200).send('OK');
});
```

## Resources
- [MindTickle Webhooks](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-performance-tuning`.
