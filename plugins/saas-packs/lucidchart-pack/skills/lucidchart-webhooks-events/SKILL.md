---
name: lucidchart-webhooks-events
description: 'Webhooks Events for Lucidchart.

  Trigger: "lucidchart webhooks events".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lucidchart
- diagramming
compatibility: Designed for Claude Code
---
# Lucidchart Webhooks & Events

## Overview

Lucidchart delivers real-time webhook notifications when documents, shapes, and collaboration states change across your organization's diagramming workspace. These events power integrations such as auto-archiving diagrams to Confluence when finalized, notifying Slack channels when collaborators join a shared document, triggering CI pipelines when architecture diagrams are updated, and maintaining audit logs of all document access. Payloads are signed JSON delivered over HTTPS using a webhook signing secret.

## Prerequisites

- A Lucid developer account with an OAuth2 app registered at `developer.lucid.co`
- Webhook endpoint URL accessible over HTTPS (TLS 1.2+)
- Webhook signing secret from the Lucid app settings (`LUCID_WEBHOOK_SECRET`)
- Express.js with raw body parsing for signature verification

## Webhook Registration

```typescript
import axios from "axios";

const res = await axios.post(
  "https://api.lucid.co/v1/webhooks",
  {
    callbackUrl: "https://your-app.com/webhooks/lucidchart",
    events: ["document.created", "document.updated", "document.shared",
             "shape.added", "collaborator.joined"],
    scope: "account",
  },
  { headers: { Authorization: `Bearer ${process.env.LUCID_ACCESS_TOKEN}`,
               "Lucid-Api-Version": "1" } }
);
console.log("Webhook ID:", res.data.webhookId);
```

## Signature Verification

```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyLucidSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-lucid-signature"] as string;
  const requestId = req.headers["x-lucid-request-id"] as string;
  if (!signature || !requestId) return res.status(401).send("Missing signature");

  const expected = crypto
    .createHmac("sha256", process.env.LUCID_WEBHOOK_SECRET!)
    .update((req as any).rawBody)
    .digest("base64");

  if (!crypto.timingSafeEqual(Buffer.from(signature, "base64"), Buffer.from(expected, "base64"))) {
    return res.status(403).send("Invalid signature");
  }
  next();
}
```

## Event Handler

```typescript
app.post("/webhooks/lucidchart", verifyLucidSignature, (req, res) => {
  const { eventType, data, timestamp } = req.body;

  switch (eventType) {
    case "document.created":
      console.log(`New doc: "${data.title}" by ${data.creatorId} in ${data.folderId}`);
      break;
    case "document.updated":
      console.log(`Doc updated: ${data.documentId}, pages: ${data.pageCount}`);
      break;
    case "document.shared":
      console.log(`Doc shared: ${data.documentId} → ${data.recipientEmail} (${data.permission})`);
      break;
    case "shape.added":
      console.log(`Shape: ${data.shapeType} on page ${data.pageId} of doc ${data.documentId}`);
      break;
    case "collaborator.joined":
      console.log(`${data.userId} joined doc ${data.documentId} as ${data.role}`);
      break;
    default:
      console.warn(`Unhandled event: ${eventType}`);
  }
  res.status(200).json({ ok: true });
});
```

## Event Types

| Event | Payload Fields | Use Case |
|---|---|---|
| `document.created` | `documentId`, `title`, `creatorId`, `folderId`, `templateId` | Index new diagrams in search or notify team channels |
| `document.updated` | `documentId`, `pageCount`, `lastEditedBy`, `editSummary` | Trigger CI when architecture diagrams change |
| `document.shared` | `documentId`, `recipientEmail`, `permission`, `sharedBy` | Audit external sharing for compliance |
| `shape.added` | `documentId`, `pageId`, `shapeType`, `shapeId`, `position` | Track diagram complexity metrics |
| `collaborator.joined` | `documentId`, `userId`, `role`, `joinedAt` | Post Slack notifications for live collaboration |
| `document.deleted` | `documentId`, `deletedBy`, `deletedAt` | Remove stale references from linked systems |

## Retry & Idempotency

```typescript
const seen = new Set<string>();

function ensureIdempotent(req: Request, res: Response, next: NextFunction) {
  const requestId = req.headers["x-lucid-request-id"] as string;
  if (seen.has(requestId)) {
    return res.status(200).json({ duplicate: true });
  }
  seen.add(requestId);
  next();
}
// Lucid retries failed deliveries 3 times with exponential backoff (1 min, 5 min, 30 min).
// After 3 consecutive failures the webhook is marked inactive and must be re-enabled via API.
```

## Error Handling

| Issue | Cause | Fix |
|---|---|---|
| 403 on signature check | Signing secret regenerated in Lucid dashboard | Update `LUCID_WEBHOOK_SECRET` and redeploy |
| Events arrive for wrong account | Webhook scope set to `user` instead of `account` | Re-register with `"scope": "account"` |
| `shape.added` floods endpoint | Busy diagram with many rapid edits | Debounce by `documentId` with a 5-second window |
| Webhook marked inactive | Endpoint returned errors for 3 retries | Fix endpoint, then PATCH webhook status to `active` |
| Missing `Lucid-Api-Version` header | API version not pinned | Always include `"Lucid-Api-Version": "1"` in registration |

## Resources

- [Lucid Developer Reference](https://developer.lucid.co/reference/overview)

## Next Steps

See `lucidchart-security-basics`.
