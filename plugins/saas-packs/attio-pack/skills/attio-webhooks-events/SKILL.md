---
name: attio-webhooks-events
description: 'Implement Attio v2 webhooks -- subscribe to record/list/note/task events,

  verify signatures, filter by object or attribute, and handle idempotently.

  Trigger: "attio webhook", "attio events", "attio webhook signature",

  "handle attio events", "attio notifications", "attio real-time".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- crm
- attio
compatibility: Designed for Claude Code
---
# Attio Webhooks & Events

## Overview
Attio v2 webhooks deliver real-time CRM event notifications to your HTTPS endpoint. Subscribe to record, list-entry, note, and task events with optional object or attribute filters to reduce volume. Webhooks are managed via `POST /v2/webhooks` and verified with HMAC-SHA256 signatures using a timestamp-prefixed payload.

## Webhook Registration
```typescript
const webhook = await fetch("https://api.attio.com/v2/webhooks", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.ATTIO_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    target_url: "https://yourapp.com/webhooks/attio",
    subscriptions: [
      { event_type: "record.created" },
      { event_type: "record.updated", filter: { object: { $eq: "deals" } } },
      { event_type: "note.created" },
      { event_type: "task.completed" },
    ],
  }),
});
```

## Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyAttioSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-attio-signature"] as string;
  const timestamp = req.headers["x-attio-timestamp"] as string;
  const age = Date.now() - parseInt(timestamp) * 1000;
  if (age > 300_000) return res.status(401).json({ error: "Timestamp too old" });
  const payload = `${timestamp}.${req.body.toString()}`;
  const expected = crypto.createHmac("sha256", process.env.ATTIO_WEBHOOK_SECRET!)
    .update(payload).digest("hex");
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

app.post("/webhooks/attio", express.raw({ type: "application/json" }), verifyAttioSignature, (req, res) => {
  const event = JSON.parse(req.body.toString());
  res.status(200).json({ received: true });

  switch (event.event_type) {
    case "record.created":
      syncRecordToCRM(event.object?.api_slug, event.record?.id?.record_id); break;
    case "record.updated":
      reindexRecord(event.object?.api_slug, event.record?.id?.record_id); break;
    case "note.created":
      forwardToNotionSync(event.id.event_id); break;
    case "task.completed":
      closeProjectTask(event.id.event_id); break;
  }
});
```

## Event Types
| Event | Payload Fields | Use Case |
|-------|---------------|----------|
| `record.created` | `object.api_slug`, `record.record_id`, `actor` | Sync new contacts/deals to external CRM |
| `record.updated` | `object.api_slug`, `record.record_id`, `attribute` | Re-index changed records |
| `note.created` | `event_id`, `actor`, `record` | Forward meeting notes to Notion |
| `task.completed` | `event_id`, `actor`, `record` | Close linked project management tasks |
| `list-entry.created` | `list.api_slug`, `entry.entry_id` | Trigger pipeline stage automation |

## Retry & Idempotency
```typescript
const processed = new Set<string>();

async function handleIdempotent(event: { id: { event_id: string }; event_type: string }) {
  const eventId = event.id.event_id;
  if (processed.has(eventId)) return;
  await routeEvent(event);
  processed.add(eventId);
  if (processed.size > 10_000) {
    const entries = Array.from(processed);
    entries.slice(0, entries.length - 10_000).forEach((id) => processed.delete(id));
  }
}
```

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| Signature mismatch | Body parsed before raw verification | Use `express.raw()`, verify raw body |
| Duplicate events | Attio retry on timeout | Track `event_id` in Redis or DB |
| Missed events | Handler returns non-200 | Return 200 immediately, process async |
| Too many events | No subscription filtering | Add `filter` clauses to subscriptions |

## Resources
- [Attio Webhooks Guide](https://docs.attio.com/rest-api/guides/webhooks)
- [Attio Webhook Events Reference](https://docs.attio.com/rest-api/webhook-reference/record-events/recordcreated)

## Next Steps
See `attio-security-basics`.
