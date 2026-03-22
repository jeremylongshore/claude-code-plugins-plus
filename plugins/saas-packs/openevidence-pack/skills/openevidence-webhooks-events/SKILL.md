---
name: openevidence-webhooks-events
description: |
  Webhooks Events for OpenEvidence.
  Trigger: "openevidence webhooks events".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Webhooks & Events

## Webhook Handler
```typescript
app.post('/webhooks/openevidence', (req, res) => {
  // Verify signature
  const event = req.body;
  console.log(`Event: ${event.type}`);
  res.status(200).send('OK');
});
```

## Resources
- [OpenEvidence Webhooks](https://www.openevidence.com)

## Next Steps
See `openevidence-performance-tuning`.
