---
name: documenso-webhooks-events
description: |
  Implement Documenso webhook configuration and event handling.
  Use when setting up webhook endpoints, handling document events,
  or implementing real-time notifications for document signing.
  Trigger with phrases like "documenso webhook", "documenso events",
  "document completed webhook", "signing notification".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(ngrok:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, webhooks]

---
# Documenso Webhooks & Events

## Overview

Configure and handle Documenso webhooks for real-time document lifecycle notifications. Webhooks require a Teams plan or higher. The webhook secret is sent via the `X-Documenso-Secret` header (not HMAC-signed -- it is a shared secret comparison).

## Prerequisites

- Documenso team account (webhooks require teams)
- HTTPS endpoint for webhook reception
- Completed `documenso-install-auth` setup

## Supported Events

| Event | Trigger | Use Case |
|-------|---------|----------|
| `document.created` | New document created | Audit logging |
| `document.sent` | Document sent for signing | Start SLA timers |
| `document.opened` | Recipient opens the document | Track engagement |
| `document.signed` | One recipient completes signing | Progress tracking |
| `document.completed` | All recipients have signed | Trigger downstream workflows |
| `document.rejected` | Recipient rejects | Alert sender, escalate |
| `document.cancelled` | Sender cancels document | Cleanup, notify recipients |

## Instructions

### Step 1: Create Webhook via Dashboard

1. Log into Documenso, navigate to **Team Settings > Webhooks**.
2. Click **Create Webhook**.
3. Enter your **HTTPS endpoint URL**.
4. Select the events you want to receive.
5. (Optional) Enter a **webhook secret** -- this value will be sent as-is in the `X-Documenso-Secret` header on every request.
6. Save.

### Step 2: Webhook Handler (Express)

```typescript
// src/webhooks/documenso.ts
import express from "express";

const router = express.Router();
const WEBHOOK_SECRET = process.env.DOCUMENSO_WEBHOOK_SECRET!;

// Middleware: verify the shared secret
function verifySecret(req: express.Request, res: express.Response, next: express.NextFunction) {
  const secret = req.headers["x-documenso-secret"];
  if (!secret || secret !== WEBHOOK_SECRET) {
    console.warn("Webhook rejected: invalid secret");
    return res.status(401).json({ error: "Invalid webhook secret" });
  }
  next();
}

router.post("/webhooks/documenso", express.json(), verifySecret, async (req, res) => {
  const { event, payload } = req.body;
  console.log(`Received ${event} for document ${payload.id}`);

  // Acknowledge immediately -- process async
  res.status(200).json({ received: true });

  // Route to handler
  try {
    await handleEvent(event, payload);
  } catch (err) {
    console.error(`Failed to process ${event}:`, err);
  }
});

async function handleEvent(event: string, payload: any) {
  switch (event) {
    case "document.completed":
      // All recipients signed -- download final PDF, update CRM
      await onDocumentCompleted(payload);
      break;
    case "document.signed":
      // One recipient signed -- track progress
      await onRecipientSigned(payload);
      break;
    case "document.rejected":
      // Recipient rejected -- alert sender
      await onDocumentRejected(payload);
      break;
    case "document.opened":
      // Track engagement for SLA
      console.log(`Document ${payload.id} opened by recipient`);
      break;
    default:
      console.log(`Unhandled event: ${event}`);
  }
}

async function onDocumentCompleted(payload: any) {
  const { id, title, recipients } = payload;
  console.log(`Document "${title}" (${id}) completed by all ${recipients?.length} recipients`);
  // Download signed PDF, store in S3, update database, notify team
}

async function onRecipientSigned(payload: any) {
  console.log(`Recipient signed document ${payload.id}`);
  // Update progress tracker, send notification
}

async function onDocumentRejected(payload: any) {
  console.log(`Document ${payload.id} REJECTED`);
  // Alert sender, create follow-up task
}

export default router;
```

### Step 3: Verification in Python

```python
# webhooks/documenso.py
from flask import Flask, request, jsonify
import hmac

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["DOCUMENSO_WEBHOOK_SECRET"]

@app.route("/webhooks/documenso", methods=["POST"])
def handle_webhook():
    # Verify shared secret (constant-time comparison)
    secret = request.headers.get("X-Documenso-Secret", "")
    if not hmac.compare_digest(secret, WEBHOOK_SECRET):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    event = data["event"]
    payload = data["payload"]

    print(f"Event: {event}, Document: {payload['id']}")

    if event == "document.completed":
        # Trigger post-signing workflow
        pass
    elif event == "document.rejected":
        # Alert and escalate
        pass

    return jsonify({"received": True}), 200
```

### Step 4: Local Development with ngrok

```bash
# Start your webhook server
npm run dev  # listening on port 3000

# Expose via ngrok
ngrok http 3000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Add as webhook URL in Documenso dashboard:
# https://abc123.ngrok.io/webhooks/documenso
```

### Step 5: Test with curl

```bash
# Simulate a webhook delivery locally
curl -X POST http://localhost:3000/webhooks/documenso \
  -H "Content-Type: application/json" \
  -H "X-Documenso-Secret: $DOCUMENSO_WEBHOOK_SECRET" \
  -d '{
    "event": "document.completed",
    "payload": {
      "id": 42,
      "title": "Service Agreement",
      "status": "COMPLETED",
      "recipients": [
        { "email": "signer@example.com", "name": "Jane Doe", "role": "SIGNER" }
      ]
    }
  }'
```

### Step 6: Idempotency and Reliable Processing

```typescript
// Use a Set or database to deduplicate events
const processedEvents = new Set<string>();

async function handleEventIdempotent(event: string, payload: any) {
  const eventKey = `${event}:${payload.id}:${payload.updatedAt}`;
  if (processedEvents.has(eventKey)) {
    console.log(`Skipping duplicate: ${eventKey}`);
    return;
  }
  processedEvents.add(eventKey);
  await handleEvent(event, payload);
}
```

For production, store processed event IDs in Redis or a database table rather than in-memory.

## Webhook Payload Structure

```json
{
  "event": "document.completed",
  "payload": {
    "id": 42,
    "externalId": null,
    "userId": 1,
    "teamId": 5,
    "title": "Service Agreement",
    "status": "COMPLETED",
    "createdAt": "2026-03-22T10:00:00.000Z",
    "updatedAt": "2026-03-22T14:30:00.000Z",
    "completedAt": "2026-03-22T14:30:00.000Z",
    "recipients": [
      {
        "email": "signer@example.com",
        "name": "Jane Doe",
        "role": "SIGNER",
        "signingStatus": "SIGNED"
      }
    ]
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 401 on webhook | Secret mismatch | Verify `X-Documenso-Secret` matches your stored secret |
| No events received | URL not HTTPS | Use HTTPS endpoint (ngrok for local dev) |
| Duplicate processing | Retry delivery | Implement idempotency with event key deduplication |
| Handler timeout | Slow processing | Acknowledge 200 immediately, process async via queue |
| Events stop arriving | Webhook disabled | Check webhook status in Team Settings |

## Resources

- [Documenso Webhooks](https://docs.documenso.com/developers/webhooks)
- [Webhook Verification](https://docs.documenso.com/docs/developers/webhooks/verification)
- [ngrok Documentation](https://ngrok.com/docs)

## Next Steps

For performance optimization, see `documenso-performance-tuning`.
