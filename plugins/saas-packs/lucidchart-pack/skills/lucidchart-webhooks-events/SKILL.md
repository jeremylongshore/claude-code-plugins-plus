---
name: lucidchart-webhooks-events
description: |
  Webhooks Events for Lucidchart.
  Trigger: "lucidchart webhooks events".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Webhooks & Events

## Webhook Handler
```typescript
app.post('/webhooks/lucidchart', (req, res) => {
  // Verify signature
  const event = req.body;
  console.log(`Event: ${event.type}`);
  res.status(200).send('OK');
});
```

## Resources
- [Lucidchart Webhooks](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-performance-tuning`.
