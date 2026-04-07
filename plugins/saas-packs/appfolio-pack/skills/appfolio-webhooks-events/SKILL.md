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

# AppFolio Webhooks & Events

## Overview
AppFolio Stack delivers real-time webhook notifications for property management lifecycle events including tenant onboarding, lease execution, rent payments, and maintenance workflows. Use these webhooks to sync AppFolio data with your CRM, accounting system, or custom property management dashboards without polling the API.

## Webhook Registration
```typescript
const response = await fetch("https://api.appfolio.com/v1/webhooks", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.APPFOLIO_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    url: "https://yourapp.com/webhooks/appfolio",
    events: ["tenant.created", "work_order.updated", "payment.received", "lease.signed"],
    secret: process.env.APPFOLIO_WEBHOOK_SECRET,
  }),
});
```

## Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyAppFolioSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-appfolio-signature"] as string;
  const expected = crypto
    .createHmac("sha256", process.env.APPFOLIO_WEBHOOK_SECRET!)
    .update(req.body)
    .digest("hex");
  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return res.status(401).json({ error: "Invalid signature" });
  }
  next();
}
```

## Event Handler
```typescript
import express from "express";
const app = express();

app.post("/webhooks/appfolio", express.raw({ type: "application/json" }), verifyAppFolioSignature, (req, res) => {
  const event = JSON.parse(req.body.toString());
  res.status(200).json({ received: true });

  switch (event.type) {
    case "tenant.created":
      syncTenantToCRM(event.data.tenant_id, event.data.property_id); break;
    case "work_order.updated":
      notifyMaintenanceTeam(event.data.work_order_id, event.data.status); break;
    case "payment.received":
      recordPayment(event.data.lease_id, event.data.amount_cents); break;
    case "lease.signed":
      activateLease(event.data.lease_id, event.data.move_in_date); break;
  }
});
```

## Event Types
| Event | Payload Fields | Use Case |
|-------|---------------|----------|
| `tenant.created` | `tenant_id`, `property_id`, `email` | Sync new tenant to CRM |
| `work_order.updated` | `work_order_id`, `status`, `assigned_vendor` | Dispatch or escalate maintenance |
| `payment.received` | `lease_id`, `amount_cents`, `payment_method` | Update accounting ledger |
| `lease.signed` | `lease_id`, `move_in_date`, `term_months` | Activate unit and send welcome |
| `lease.expired` | `lease_id`, `unit_id`, `vacate_date` | Trigger renewal or re-listing |

## Retry & Idempotency
```typescript
const processed = new Set<string>();

async function handleIdempotent(event: { id: string; type: string; data: any }) {
  if (processed.has(event.id)) return;
  await routeEvent(event);
  processed.add(event.id);
  if (processed.size > 10_000) {
    const entries = Array.from(processed);
    entries.slice(0, entries.length - 10_000).forEach((id) => processed.delete(id));
  }
}
```

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| Signature mismatch | Wrong secret or parsed body | Use `express.raw()` for verification |
| Duplicate events | AppFolio retry on timeout | Track event IDs for idempotency |
| Missing `property_id` | Event from archived property | Check property status before processing |
| 5xx from handler | Downstream service unavailable | Return 200 immediately, process async |

## Resources
- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)

## Next Steps
See `appfolio-security-basics`.
