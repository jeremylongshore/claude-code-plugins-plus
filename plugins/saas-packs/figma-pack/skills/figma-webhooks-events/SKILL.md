---
name: figma-webhooks-events
description: |
  Implement Figma Webhooks V2 for real-time file, comment, and library events.
  Use when setting up webhook endpoints, handling FILE_UPDATE events,
  or building event-driven Figma automation.
  Trigger with phrases like "figma webhook", "figma events",
  "figma FILE_UPDATE", "figma notifications", "figma real-time".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Webhooks & Events

## Overview
Figma Webhooks V2 push real-time notifications when files change, comments are posted, or libraries are published. Webhooks can be scoped to teams, projects, or individual files. Authentication uses a passcode echoed back in each payload.

## Prerequisites
- HTTPS endpoint accessible from the internet
- `FIGMA_PAT` with `webhooks:write` scope
- Team ID (from Figma URL: `figma.com/files/team/<TEAM_ID>/...`)

## Instructions

### Step 1: Create a Webhook
```bash
# POST /v2/webhooks -- requires webhooks:write scope
curl -X POST https://api.figma.com/v2/webhooks \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "FILE_UPDATE",
    "team_id": "123456789",
    "endpoint": "https://yourapp.com/webhooks/figma",
    "passcode": "your-secret-passcode",
    "description": "Sync design tokens on file update"
  }'

# Response:
# { "id": "wh_abc123", "event_type": "FILE_UPDATE", "status": "ACTIVE", ... }
```

**Available event types:**

| Event Type | Trigger | Payload Contains |
|------------|---------|-----------------|
| `FILE_UPDATE` | File saved to version history | `file_key`, `file_name`, `timestamp` |
| `FILE_DELETE` | File deleted | `file_key`, `file_name` |
| `FILE_VERSION_UPDATE` | Named version created | `file_key`, `version_id`, `label` |
| `FILE_COMMENT` | Comment added | `file_key`, `comment`, `comment_id` |
| `LIBRARY_PUBLISH` | Library published | `file_key`, `description`, variables |

### Step 2: Handle Webhook Events
```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();
app.use(express.json());

// Figma webhook payload types
interface FigmaWebhookBase {
  event_type: string;
  passcode: string;
  timestamp: string;
  webhook_id: string;
}

interface FileUpdateEvent extends FigmaWebhookBase {
  event_type: 'FILE_UPDATE';
  file_key: string;
  file_name: string;
  triggered_by: { id: string; handle: string };
}

interface FileCommentEvent extends FigmaWebhookBase {
  event_type: 'FILE_COMMENT';
  file_key: string;
  file_name: string;
  comment: Array<{ text: string }>;
  comment_id: string;
  triggered_by: { id: string; handle: string };
}

interface LibraryPublishEvent extends FigmaWebhookBase {
  event_type: 'LIBRARY_PUBLISH';
  file_key: string;
  file_name: string;
  description: string;
  triggered_by: { id: string; handle: string };
}

type FigmaWebhookEvent = FileUpdateEvent | FileCommentEvent | LibraryPublishEvent;

app.post('/webhooks/figma', (req, res) => {
  const event: FigmaWebhookEvent = req.body;

  // 1. Verify passcode (timing-safe)
  const expected = process.env.FIGMA_WEBHOOK_PASSCODE!;
  if (event.passcode.length !== expected.length ||
      !crypto.timingSafeEqual(Buffer.from(event.passcode), Buffer.from(expected))) {
    return res.status(401).json({ error: 'Invalid passcode' });
  }

  // 2. Respond quickly (Figma expects 200 within seconds)
  res.status(200).json({ received: true });

  // 3. Process async
  processEvent(event).catch(err =>
    console.error(`Failed to process ${event.event_type}:`, err)
  );
});

async function processEvent(event: FigmaWebhookEvent) {
  switch (event.event_type) {
    case 'FILE_UPDATE':
      console.log(`File updated: ${event.file_name} by ${event.triggered_by.handle}`);
      // Re-extract design tokens, invalidate cache, notify Slack
      await syncDesignTokens(event.file_key);
      break;

    case 'FILE_COMMENT':
      console.log(`Comment on ${event.file_name}: ${event.comment[0]?.text}`);
      // Forward to Slack, create Jira ticket, etc.
      break;

    case 'LIBRARY_PUBLISH':
      console.log(`Library published: ${event.file_name}`);
      // Trigger downstream rebuilds
      await triggerTokenRebuild(event.file_key);
      break;
  }
}
```

### Step 3: Manage Webhooks
```typescript
const FIGMA_API = 'https://api.figma.com';

// List all webhooks for a team
async function listWebhooks(teamId: string) {
  const res = await fetch(`${FIGMA_API}/v2/webhooks?team_id=${teamId}`, {
    headers: { 'X-Figma-Token': process.env.FIGMA_PAT! },
  });
  return res.json(); // { webhooks: [...] }
}

// Delete a webhook
async function deleteWebhook(webhookId: string) {
  await fetch(`${FIGMA_API}/v2/webhooks/${webhookId}`, {
    method: 'DELETE',
    headers: { 'X-Figma-Token': process.env.FIGMA_PAT! },
  });
}

// Update a webhook (e.g., change endpoint)
async function updateWebhook(webhookId: string, updates: Record<string, any>) {
  const res = await fetch(`${FIGMA_API}/v2/webhooks/${webhookId}`, {
    method: 'PUT',
    headers: {
      'X-Figma-Token': process.env.FIGMA_PAT!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });
  return res.json();
}
```

### Step 4: Idempotency for Duplicate Events
```typescript
// Figma may deliver the same event multiple times
const processedEvents = new Set<string>();

function deduplicateEvent(event: FigmaWebhookEvent): boolean {
  const key = `${event.webhook_id}:${event.timestamp}`;
  if (processedEvents.has(key)) {
    console.log(`Duplicate event skipped: ${key}`);
    return false;
  }
  processedEvents.add(key);
  // Clean up old entries (keep last 1000)
  if (processedEvents.size > 1000) {
    const oldest = Array.from(processedEvents).slice(0, 500);
    oldest.forEach(k => processedEvents.delete(k));
  }
  return true;
}
```

## Output
- Webhook created and receiving Figma events
- Passcode verification on every incoming request
- Event handlers for FILE_UPDATE, FILE_COMMENT, LIBRARY_PUBLISH
- Idempotency preventing duplicate processing

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not firing | Endpoint not HTTPS | Figma requires TLS |
| Invalid passcode | Wrong secret configured | Verify passcode in webhook creation |
| Webhook status PAUSED | Too many delivery failures | Fix endpoint, then recreate webhook |
| Missing `triggered_by` | Older event format | Check webhook V2 vs V1 |

## Examples

### Test Webhook Locally
```bash
# Use ngrok to expose local server
ngrok http 3000

# Create webhook pointing to ngrok URL
curl -X POST https://api.figma.com/v2/webhooks \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "FILE_UPDATE",
    "team_id": "YOUR_TEAM_ID",
    "endpoint": "https://YOUR-NGROK.ngrok.io/webhooks/figma",
    "passcode": "test-passcode"
  }'
```

## Resources
- [Figma Webhooks V2](https://developers.figma.com/docs/rest-api/webhooks/)
- [Webhook Event Types](https://developers.figma.com/docs/rest-api/webhooks-types/)
- [Webhook Endpoints](https://developers.figma.com/docs/rest-api/webhooks-endpoints/)

## Next Steps
For performance optimization, see `figma-performance-tuning`.
