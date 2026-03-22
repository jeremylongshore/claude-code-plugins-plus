---
name: navan-webhooks-events
description: |
  Webhooks Events for Navan.
  Trigger: "navan webhooks events".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Webhooks & Events

## Webhook Handler
```typescript
app.post('/webhooks/navan', (req, res) => {
  // Verify signature
  const event = req.body;
  console.log(`Event: ${event.type}`);
  res.status(200).send('OK');
});
```

## Resources
- [Navan Webhooks](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-performance-tuning`.
