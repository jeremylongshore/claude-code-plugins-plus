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

## Overview

Linktree emits real-time webhook events whenever links, profiles, or analytics milestones change. These events enable automations such as syncing new bio links to a CMS, triggering social media posts when a profile is updated, alerting marketing teams when traffic milestones are hit, and auditing link lifecycle changes for compliance dashboards. All payloads are JSON over HTTPS with HMAC-SHA256 signature verification to guarantee authenticity.

## Prerequisites

- A registered Linktree developer app with webhook permissions enabled
- Webhook endpoint URL accessible over HTTPS (TLS 1.2+)
- Signing secret from the Linktree developer dashboard (`LINKTREE_WEBHOOK_SECRET`)
- Express.js with `raw` body parsing enabled for signature verification

## Webhook Registration

```typescript
import axios from "axios";

const res = await axios.post(
  "https://api.linktr.ee/v1/webhooks",
  {
    url: "https://your-app.com/webhooks/linktree",
    events: ["link.created", "link.updated", "link.deleted",
             "profile.updated", "analytics.milestone"],
  },
  { headers: { Authorization: `Bearer ${process.env.LINKTREE_API_TOKEN}` } }
);
console.log("Subscription ID:", res.data.id);
```

## Signature Verification

```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyLinktreeSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-linktree-signature"] as string;
  const timestamp = req.headers["x-linktree-timestamp"] as string;
  if (!signature || !timestamp) return res.status(401).send("Missing signature");

  const payload = `${timestamp}.${(req as any).rawBody}`;
  const expected = crypto
    .createHmac("sha256", process.env.LINKTREE_WEBHOOK_SECRET!)
    .update(payload)
    .digest("hex");

  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return res.status(403).send("Invalid signature");
  }
  next();
}
```

## Event Handler

```typescript
app.post("/webhooks/linktree", verifyLinktreeSignature, (req, res) => {
  const { type, data, timestamp } = req.body;

  switch (type) {
    case "link.created":
      console.log(`New link: ${data.title} → ${data.url}`);
      break;
    case "link.updated":
      console.log(`Link edited: ${data.link_id}, position: ${data.position}`);
      break;
    case "link.deleted":
      console.log(`Link removed: ${data.link_id}`);
      break;
    case "profile.updated":
      console.log(`Profile changed: bio=${data.bio}, avatar=${data.avatar_url}`);
      break;
    case "analytics.milestone":
      console.log(`Milestone: ${data.metric} hit ${data.threshold} on ${data.link_id}`);
      break;
    default:
      console.warn(`Unhandled event: ${type}`);
  }
  res.status(200).json({ received: true });
});
```

## Event Types

| Event | Payload Fields | Use Case |
|---|---|---|
| `link.created` | `link_id`, `title`, `url`, `position` | Sync new links to CMS or dashboard |
| `link.updated` | `link_id`, `title`, `url`, `position`, `thumbnail_url` | Detect reordering or URL changes |
| `link.deleted` | `link_id`, `deleted_at` | Clean up external references |
| `profile.updated` | `username`, `bio`, `avatar_url`, `theme` | Mirror profile changes to marketing sites |
| `analytics.milestone` | `link_id`, `metric`, `value`, `threshold` | Alert when a link hits click milestones |

## Retry & Idempotency

```typescript
const processed = new Set<string>();

function ensureIdempotent(req: Request, res: Response, next: NextFunction) {
  const deliveryId = req.headers["x-linktree-delivery-id"] as string;
  if (processed.has(deliveryId)) {
    return res.status(200).json({ duplicate: true });
  }
  processed.add(deliveryId);
  next();
}
// Linktree retries up to 5 times with exponential backoff (10s, 30s, 90s, 270s, 810s).
// Webhooks are disabled after 72 hours of consecutive failures.
```

## Error Handling

| Issue | Cause | Fix |
|---|---|---|
| 401 on every delivery | Signing secret rotated in dashboard | Re-copy secret and redeploy |
| Duplicate events processed | Retry after timeout | Implement idempotency check on `x-linktree-delivery-id` |
| Missing `analytics.milestone` events | Milestone thresholds not configured | Set thresholds in Linktree dashboard under Analytics |
| Payload body is empty | Body parser consuming raw body | Use `express.raw({ type: "application/json" })` before route |
| Webhook auto-disabled | Endpoint returned 5xx for 72 hours | Fix endpoint, then re-enable subscription via API |

## Resources

- [Linktree Developer Platform](https://linktr.ee/marketplace/developer)

## Next Steps

See `linktree-security-basics`.
