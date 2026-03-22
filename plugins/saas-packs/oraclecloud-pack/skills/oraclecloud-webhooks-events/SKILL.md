---
name: oraclecloud-webhooks-events
description: |
  Webhooks Events for Oracle Cloud.
  Trigger: "oraclecloud webhooks events".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Webhooks & Events

## Webhook Handler
```typescript
app.post('/webhooks/oraclecloud', (req, res) => {
  // Verify signature
  const event = req.body;
  console.log(`Event: ${event.type}`);
  res.status(200).send('OK');
});
```

## Resources
- [Oracle Cloud Webhooks](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-performance-tuning`.
