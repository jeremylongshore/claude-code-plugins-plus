---
name: linktree-webhooks-events
description: |
  Webhooks Events for Linktree.
  Trigger: "linktree webhooks events".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Webhooks & Events

## Webhook Handler
```typescript
app.post('/webhooks/linktree', (req, res) => {
  // Verify signature
  const event = req.body;
  console.log(`Event: ${event.type}`);
  res.status(200).send('OK');
});
```

## Resources
- [Linktree Webhooks](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-performance-tuning`.
