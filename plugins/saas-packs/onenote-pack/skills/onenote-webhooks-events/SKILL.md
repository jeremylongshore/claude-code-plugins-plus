---
name: onenote-webhooks-events
description: |
  Webhooks Events for OneNote.
  Trigger: "onenote webhooks events".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote Webhooks & Events

## Webhook Handler
```typescript
app.post('/webhooks/onenote', (req, res) => {
  // Verify signature
  const event = req.body;
  console.log(`Event: ${event.type}`);
  res.status(200).send('OK');
});
```

## Resources
- [OneNote Webhooks](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-performance-tuning`.
