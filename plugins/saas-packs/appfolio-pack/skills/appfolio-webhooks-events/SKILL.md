---
name: appfolio-webhooks-events
description: 'Handle AppFolio webhook events for property management notifications.

  Trigger: "appfolio webhook".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio Webhooks & Events

## Overview

AppFolio Stack delivers real-time webhook notifications for property management lifecycle events including tenant onboarding, lease execution, rent payments, and maintenance workflows. Use these webhooks to sync AppFolio data with your CRM, accounting system, or custom property management dashboards without polling the API.

## Prerequisites

- Written confirmation in the current AppFolio partner contract that the target
  portfolio supports the event types, registration process, delivery semantics,
  and signature scheme. Do not infer webhook support from another integration.
- A bounded raw-body ingress route, managed webhook secret, durable event store,
  queue, idempotency table, and owner for downstream accounting/CRM effects.
- A sandbox endpoint and synthetic events for valid, malformed, duplicate, and
  delayed-delivery tests before production registration.

## Instructions

1. Register events only through the provider-issued process and contract-bound
   client after verifying the target URL, allowlist, and secret delivery path.
2. Verify bounded raw bytes and the signature before parsing; reject malformed
   or replayed events without logging tenant, payment, or lease content.
3. Persist the event ID, type, received time, and encrypted/minimized payload
   transactionally before acknowledging delivery, then process it asynchronously.
4. Enforce durable idempotency and reconcile unknown downstream outcomes before
   writing CRM, accounting, tenant, lease, or work-order state.

## Webhook Registration

```typescript
// Use this only if the signed provider contract explicitly supports this API.
const response = await createVerifiedAppFolioClient().post("/webhooks", {
    url: "https://yourapp.com/webhooks/appfolio",
    events: ["tenant.created", "work_order.updated", "payment.received", "lease.signed"],
    secret: process.env.APPFOLIO_WEBHOOK_SECRET,
});
```

## Signature Verification

```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyAppFolioSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-appfolio-signature"] as string;
  const expected = Buffer.from(crypto
    .createHmac("sha256", process.env.APPFOLIO_WEBHOOK_SECRET!)
    .update(req.body)
    .digest("hex"));
  const received = signature ? Buffer.from(signature) : Buffer.alloc(0);
  if (received.length !== expected.length || !crypto.timingSafeEqual(received, expected)) {
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
  // persistIncomingEvent performs a durable idempotency insert and queue write
  // in one transaction. A failed persist must receive a retryable response.
  persistIncomingEvent(event).then(() => {
    res.status(202).json({ received: true });
  }).catch(() => {
    res.status(503).json({ error: "Event persistence unavailable" });
  });
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
async function handleIdempotent(event: { id: string; type: string; data: any }) {
  if (await durableEventStore.hasSucceeded(event.id)) return;
  await routeEvent(event);
  await durableEventStore.markSucceeded(event.id);
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Signature mismatch | Wrong secret or parsed body | Use `express.raw()` for verification |
| Duplicate events | AppFolio retry on timeout | Track event IDs for idempotency |
| Missing `property_id` | Event from archived property | Check property status before processing |
| Durable store/queue unavailable | Cannot guarantee acknowledged event survives | Return retryable 503; do not acknowledge before persistence |

## Output

- A contract-gated webhook registration decision and a fail-closed raw-body
  signature verification result
- A durable receipt for each accepted event before acknowledgement, with
  minimized/encrypted content and durable idempotency state
- A controlled asynchronous processing outcome that can be retried or
  reconciled without duplicate tenant, lease, payment, or work-order effects

## Examples

For a synthetic work-order update, deliver a valid signed event, a malformed
signature, a duplicate ID, and a downstream timeout. Prove the valid event is
persisted before `202`, the malformed request is rejected without parsing, the
duplicate does not produce a second side effect, and the timeout remains queued
for reconciliation. If provider support, raw-body capture, signature secret,
durable store, or queue is unavailable, keep the endpoint disabled and use the
provider-approved polling/reconciliation path instead.

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)

## Next Steps

See `appfolio-security-basics`.
