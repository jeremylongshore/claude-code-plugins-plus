---
name: appfolio-webhooks-events
description: |
  Handle AppFolio webhook events for property management notifications.
  Trigger: "appfolio webhook".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio webhooks events | sed 's/\b\(.\)/\u\1/g'

## Overview
AppFolio Stack supports webhooks for lease, payment, and maintenance events.

## Webhook Handler
```typescript
import express from "express";
import crypto from "crypto";

const router = express.Router();

router.post("/webhooks/appfolio", express.raw({ type: "application/json" }), (req, res) => {
  const signature = req.headers["x-appfolio-signature"] as string;
  const expected = crypto.createHmac("sha256", process.env.APPFOLIO_WEBHOOK_SECRET!)
    .update(req.body).digest("hex");

  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return res.status(401).json({ error: "Invalid signature" });
  }

  const event = JSON.parse(req.body.toString());
  console.log(\`Event: \${event.type} — \${JSON.stringify(event.data)}\`);
  res.status(200).json({ received: true });
});
```

## Event Types
| Event | Trigger | Use Case |
|-------|---------|----------|
| `lease.created` | New lease signed | Update CRM |
| `lease.expired` | Lease ended | Trigger renewal workflow |
| `payment.received` | Rent paid | Update accounting |
| `maintenance.created` | Work order filed | Dispatch vendor |

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
