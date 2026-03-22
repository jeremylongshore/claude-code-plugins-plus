---
name: juicebox-webhooks-events
description: |
  Handle Juicebox webhooks and events.
  Trigger: "juicebox webhooks", "juicebox events".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Webhooks & Events

## Webhook Setup
Configure at app.juicebox.ai > Settings > Webhooks.

## Event Handling
```typescript
app.post('/webhooks/juicebox', (req, res) => {
  const sig = req.headers['x-juicebox-signature'];
  if (!verifySignature(req.body, sig, WEBHOOK_SECRET)) return res.status(401).end();
  switch (req.body.type) {
    case 'outreach.replied': handleReply(req.body.data); break;
    case 'enrichment.complete': handleEnrichment(req.body.data); break;
  }
  res.status(200).send('OK');
});
```

## Events
| Event | Use |
|-------|-----|
| `outreach.replied` | Alert recruiter |
| `enrichment.complete` | Update record |
| `search.alert` | New candidate matches |

## Resources
- [Webhooks](https://docs.juicebox.work/webhooks)

## Next Steps
See `juicebox-performance-tuning`.
