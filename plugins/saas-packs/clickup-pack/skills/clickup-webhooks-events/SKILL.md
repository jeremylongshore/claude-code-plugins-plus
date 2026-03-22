---
name: clickup-webhooks-events
description: |
  Create and manage ClickUp webhooks for real-time event notifications.
  Use when setting up webhook listeners for task/list/space events,
  implementing two-way sync, or handling ClickUp event payloads.
  Trigger: "clickup webhook", "clickup events", "clickup notifications",
  "clickup real-time", "clickup event listener", "clickup webhook create".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Webhooks & Events

## Overview

ClickUp webhooks send HTTP POST notifications when resources change. Register webhooks via API, subscribe to specific events, and receive payloads with `history_items` showing what changed.

## Webhook Endpoints

```
POST   /api/v2/team/{team_id}/webhook    Create webhook
GET    /api/v2/team/{team_id}/webhook    Get webhooks
PUT    /api/v2/webhook/{webhook_id}      Update webhook
DELETE /api/v2/webhook/{webhook_id}      Delete webhook
```

## Create a Webhook

```typescript
async function createWebhook(teamId: string, endpoint: string, events: string[]) {
  return clickupRequest(`/team/${teamId}/webhook`, {
    method: 'POST',
    body: JSON.stringify({
      endpoint,        // Your HTTPS URL
      events,          // Array of event names
      space_id: null,  // Optional: limit to specific space
      folder_id: null, // Optional: limit to specific folder
      list_id: null,   // Optional: limit to specific list
      task_id: null,   // Optional: limit to specific task
    }),
  });
}

// Subscribe to task and list events
const webhook = await createWebhook('1234567', 'https://myapp.com/webhooks/clickup', [
  'taskCreated',
  'taskUpdated',
  'taskDeleted',
  'taskStatusUpdated',
  'taskAssigneeUpdated',
  'taskDueDateUpdated',
  'taskCommentPosted',
  'taskTimeTrackedUpdated',
  'listCreated',
  'listUpdated',
  'listDeleted',
]);

// Response:
// { "id": "wh_abc123", "webhook": { "id": "...", "endpoint": "...", "events": [...] } }
```

## Available Events

| Category | Events |
|----------|--------|
| **Task** | `taskCreated`, `taskUpdated`, `taskDeleted`, `taskStatusUpdated`, `taskAssigneeUpdated`, `taskDueDateUpdated`, `taskTagUpdated`, `taskMoved`, `taskCommentPosted`, `taskCommentUpdated`, `taskTimeTrackedUpdated`, `taskTimeEstimateUpdated`, `taskPriorityUpdated` |
| **List** | `listCreated`, `listUpdated`, `listDeleted` |
| **Folder** | `folderCreated`, `folderUpdated`, `folderDeleted` |
| **Space** | `spaceCreated`, `spaceUpdated`, `spaceDeleted` |
| **Goal** | `goalCreated`, `goalUpdated`, `goalDeleted`, `keyResultCreated`, `keyResultUpdated`, `keyResultDeleted` |

## Webhook Payload Format

```json
{
  "event": "taskUpdated",
  "webhook_id": "wh_abc123",
  "task_id": "abc123",
  "history_items": [
    {
      "id": "hist_001",
      "type": 1,
      "date": "1695000000000",
      "field": "status",
      "parent_id": "abc123",
      "data": {},
      "source": null,
      "user": { "id": 183, "username": "john", "email": "john@example.com" },
      "before": { "status": "to do", "color": "#d3d3d3", "type": "open" },
      "after": { "status": "in progress", "color": "#4194f6", "type": "custom" }
    }
  ]
}
```

## Webhook Handler (Express)

```typescript
import express from 'express';

const app = express();
app.use(express.json());

app.post('/webhooks/clickup', async (req, res) => {
  const { event, webhook_id, task_id, history_items } = req.body;

  // Immediately acknowledge (ClickUp expects 200 within 30s)
  res.status(200).json({ received: true });

  // Process asynchronously
  try {
    await processClickUpEvent(event, task_id, history_items);
  } catch (err) {
    console.error(`Failed to process ${event} for task ${task_id}:`, err);
  }
});

async function processClickUpEvent(
  event: string,
  taskId: string,
  historyItems: any[]
) {
  switch (event) {
    case 'taskCreated':
      console.log(`New task: ${taskId}`);
      break;
    case 'taskStatusUpdated': {
      const change = historyItems[0];
      console.log(`Task ${taskId}: ${change.before.status} -> ${change.after.status}`);
      // Trigger downstream actions (e.g., notify Slack, update external system)
      break;
    }
    case 'taskCommentPosted':
      console.log(`New comment on task ${taskId}`);
      break;
    case 'taskTimeTrackedUpdated':
      console.log(`Time tracked updated on task ${taskId}`);
      break;
    default:
      console.log(`Unhandled event: ${event}`);
  }
}
```

## Idempotency (Prevent Duplicate Processing)

```typescript
const processedEvents = new Map<string, number>();

function isDuplicate(webhookId: string, historyItemId: string): boolean {
  const key = `${webhookId}:${historyItemId}`;
  if (processedEvents.has(key)) return true;
  processedEvents.set(key, Date.now());

  // Clean old entries every 1000 events
  if (processedEvents.size > 10000) {
    const cutoff = Date.now() - 3600000; // 1 hour
    for (const [k, v] of processedEvents) {
      if (v < cutoff) processedEvents.delete(k);
    }
  }
  return false;
}
```

## List and Manage Webhooks

```bash
# List all webhooks for a workspace
TEAM_ID="1234567"
curl -s "https://api.clickup.com/api/v2/team/${TEAM_ID}/webhook" \
  -H "Authorization: $CLICKUP_API_TOKEN" | jq '.webhooks[] | {id, endpoint, events}'

# Delete a webhook
curl -s -X DELETE "https://api.clickup.com/api/v2/webhook/WH_ID" \
  -H "Authorization: $CLICKUP_API_TOKEN"
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not firing | Endpoint not HTTPS | Webhooks require HTTPS URLs |
| Duplicate events | No idempotency | Track history_item IDs |
| Timeout (no 200) | Slow processing | Respond 200 immediately, process async |
| Webhook auto-disabled | Repeated failures | ClickUp disables after many 5xx responses |

## Resources

- [ClickUp Webhooks Guide](https://developer.clickup.com/docs/webhooks)
- [Task Webhook Payloads](https://developer.clickup.com/docs/webhooktaskpayloads)
- [List Webhook Payloads](https://developer.clickup.com/docs/webhooklistpayloads)
- [Create Webhook API](https://clickup.com/api/clickupreference/operation/CreateWebhook/)

## Next Steps

For performance optimization, see `clickup-performance-tuning`.
