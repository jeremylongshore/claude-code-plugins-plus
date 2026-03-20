---
name: lokalise-webhooks-events
description: |
  Implement Lokalise webhook handling and event processing.
  Use when setting up webhook endpoints, handling translation events,
  or building automation based on Lokalise notifications.
  Trigger with phrases like "lokalise webhook", "lokalise events",
  "lokalise notifications", "handle lokalise events", "lokalise automation".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Webhooks Events

## Overview

Lokalise webhooks push real-time notifications to your endpoint when translation events occur — keys created, translations updated, files uploaded, contributors added. This skill covers creating webhooks via the API, handling each event type, verifying webhook secrets, and routing events to appropriate handlers.

## Prerequisites

- Lokalise project with admin or manager role (required for webhook creation)
- HTTPS endpoint accessible from the internet (Lokalise rejects HTTP URLs)
- Express.js or equivalent HTTP framework
- Webhook secret for payload verification (generated during webhook creation)

## Instructions

### 1. Create a Webhook via the API

Register your endpoint with Lokalise using `POST /projects/{project_id}/webhooks`:

```bash
curl -X POST "https://api.lokalise.com/api2/projects/${PROJECT_ID}/webhooks" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.example.com/webhooks/lokalise",
    "branch": "main",
    "events": [
      "project.key.added",
      "project.key.modified",
      "project.translation.updated",
      "project.translation.proofread",
      "project.imported",
      "project.exported",
      "project.contributor.added",
      "project.contributor.deleted"
    ],
    "event_lang_map": [
      {"event": "project.translation.updated", "lang_iso_codes": ["en", "fr", "de"]}
    ]
  }'
```

The response includes a `secret` field — store this securely. You need it to verify incoming payloads.

To scope webhooks to specific languages, use `event_lang_map`. This prevents noise from languages you do not manage.

### 2. Know the Event Types

| Event | Fires When | Key Payload Fields |
|-------|-----------|-------------------|
| `project.key.added` | New key created | `key.key_id`, `key.key_name`, `key.platforms` |
| `project.key.modified` | Key name, tags, or metadata changed | `key.key_id`, `key.key_name`, `key.modifications` |
| `project.key.deleted` | Key removed | `key.key_id`, `key.key_name` |
| `project.key.comment.added` | Comment added to a key | `key.key_id`, `comment.comment` |
| `project.translation.updated` | Translation value changed | `translation.translation_id`, `translation.value`, `language.lang_iso` |
| `project.translation.proofread` | Translation marked as reviewed | `translation.translation_id`, `language.lang_iso` |
| `project.imported` | File uploaded to project | `import.filename`, `import.format` |
| `project.exported` | File downloaded/exported | `export.filename` |
| `project.contributor.added` | New team member added | `contributor.email`, `contributor.role` |
| `project.contributor.deleted` | Team member removed | `contributor.email` |

### 3. Understand the Webhook Payload Structure

Every webhook POST delivers this structure:

```json
{
  "event": "project.translation.updated",
  "project": {
    "id": "123456789.abcdefgh",
    "name": "My Project"
  },
  "user": {
    "email": "translator@example.com",
    "full_name": "Jane Translator"
  },
  "language": {
    "lang_id": 640,
    "lang_iso": "fr",
    "lang_name": "French"
  },
  "translation": {
    "translation_id": 98765,
    "key_id": 11223,
    "value": "Bonjour le monde",
    "is_reviewed": false,
    "modified_at": "2026-03-19T10:30:00Z"
  },
  "created_at": "2026-03-19T10:30:01Z"
}
```

The top-level `event` field determines which nested objects are present. Always check `event` first before accessing nested fields.

### 4. Build an Express Handler with Secret Verification

Lokalise signs webhook payloads with the secret from step 1. Verify it using the `x-secret` header:

```typescript
import express from "express";
import type { Request, Response, NextFunction } from "express";

const app = express();
const WEBHOOK_SECRET = process.env.LOKALISE_WEBHOOK_SECRET!;

// Parse raw body for signature verification
app.use("/webhooks/lokalise", express.json());

// Verify webhook secret
function verifyLokaliseSecret(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const secret = req.headers["x-secret"] as string;

  if (!secret || secret !== WEBHOOK_SECRET) {
    console.error("Webhook signature verification failed");
    res.status(401).json({ error: "Invalid webhook secret" });
    return;
  }
  next();
}

app.post(
  "/webhooks/lokalise",
  verifyLokaliseSecret,
  async (req: Request, res: Response) => {
    // Respond immediately — Lokalise times out after 8 seconds
    res.status(200).json({ received: true });

    // Process asynchronously
    try {
      await routeEvent(req.body);
    } catch (error) {
      console.error("Webhook processing failed:", error);
    }
  }
);
```

Responding with 200 before processing is critical. Lokalise retries on timeout (8s) and treats non-2xx as failure. Process the event asynchronously to avoid timeouts.

### 5. Route Events by Type

```typescript
interface LokaliseWebhookPayload {
  event: string;
  project: { id: string; name: string };
  user: { email: string; full_name: string };
  language?: { lang_iso: string; lang_name: string };
  key?: { key_id: number; key_name: string; platforms: string[] };
  translation?: {
    translation_id: number;
    value: string;
    is_reviewed: boolean;
  };
  import?: { filename: string; format: string };
  contributor?: { email: string; role: string };
  created_at: string;
}

type EventHandler = (payload: LokaliseWebhookPayload) => Promise<void>;

const eventHandlers: Record<string, EventHandler> = {
  "project.key.added": async (payload) => {
    console.log(`New key: ${payload.key!.key_name}`);
    // Notify translators, update local cache, trigger CI
  },

  "project.translation.updated": async (payload) => {
    const { translation, language } = payload;
    console.log(
      `Translation updated [${language!.lang_iso}]: ${translation!.value}`
    );
    // Trigger rebuild, invalidate CDN cache, update OTA bundle
  },

  "project.imported": async (payload) => {
    console.log(`File imported: ${payload.import!.filename}`);
    // Kick off translation memory update, notify reviewers
  },

  "project.contributor.added": async (payload) => {
    console.log(`New contributor: ${payload.contributor!.email}`);
    // Send onboarding info, assign default language pairs
  },
};

async function routeEvent(payload: LokaliseWebhookPayload): Promise<void> {
  const handler = eventHandlers[payload.event];
  if (handler) {
    await handler(payload);
  } else {
    console.log(`Unhandled event type: ${payload.event}`);
  }
}
```

### 6. Implement Idempotency

Lokalise may retry webhooks on network failure, sending duplicates. Track processed events:

```typescript
const processedEvents = new Set<string>();

async function routeEventIdempotent(
  payload: LokaliseWebhookPayload
): Promise<void> {
  // Create a unique key from event + timestamp + relevant IDs
  const eventKey = `${payload.event}:${payload.created_at}:` +
    `${payload.translation?.translation_id ?? payload.key?.key_id ?? ""}`;

  if (processedEvents.has(eventKey)) {
    console.log(`Duplicate event skipped: ${eventKey}`);
    return;
  }

  processedEvents.add(eventKey);
  // For production: use Redis SET with TTL instead of in-memory Set
  // await redis.set(`webhook:${eventKey}`, "1", "EX", 86400);

  await routeEvent(payload);
}
```

## Output

- Webhook registered in Lokalise project with selected event subscriptions
- Express endpoint verifying `x-secret` header on every request
- Event router dispatching to type-specific handlers
- Idempotency guard preventing duplicate processing
- Immediate 200 response with async background processing

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong secret or secret rotated | Re-check `LOKALISE_WEBHOOK_SECRET` against Lokalise project settings |
| Timeout (8 seconds) | Synchronous processing too slow | Respond 200 immediately, process in background |
| Duplicate events | Lokalise retried after network issue | Implement idempotency with event key deduplication |
| Missing events | Event type not subscribed | Update webhook via `PUT /projects/{id}/webhooks/{webhook_id}` |
| Webhook disabled | Too many consecutive failures | Check Lokalise dashboard; webhook auto-disables after repeated errors |

## Examples

### List Existing Webhooks

```bash
curl -X GET "https://api.lokalise.com/api2/projects/${PROJECT_ID}/webhooks" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}"
```

### Update Webhook Events

```bash
curl -X PUT "https://api.lokalise.com/api2/projects/${PROJECT_ID}/webhooks/${WEBHOOK_ID}" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      "project.translation.updated",
      "project.translation.proofread",
      "project.imported"
    ]
  }'
```

### Delete a Webhook

```bash
curl -X DELETE "https://api.lokalise.com/api2/projects/${PROJECT_ID}/webhooks/${WEBHOOK_ID}" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}"
```

### Test Webhook Locally with ngrok

```bash
# Terminal 1: Start your server
npm run dev  # Express on port 3000

# Terminal 2: Expose via ngrok
ngrok http 3000

# Use the ngrok HTTPS URL when creating the webhook:
# https://abc123.ngrok-free.app/webhooks/lokalise
```

## Resources

- [Lokalise Webhooks Guide](https://developers.lokalise.com/docs/webhooks-guide)
- [Webhook Events Reference](https://developers.lokalise.com/docs/webhook-events)
- [Webhooks API — Create](https://developers.lokalise.com/reference/create-a-webhook)
- [Webhooks API — List](https://developers.lokalise.com/reference/list-project-webhooks)

## Next Steps

For handling errors returned by webhook API calls, see `lokalise-common-errors`.
