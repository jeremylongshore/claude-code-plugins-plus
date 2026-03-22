---
name: notion-webhooks-events
description: |
  Implement Notion webhook receivers for real-time page and database change events.
  Use when setting up webhook endpoints, handling Notion event notifications,
  or building real-time sync with Notion workspaces.
  Trigger with phrases like "notion webhook", "notion events",
  "notion real-time", "handle notion changes", "notion notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Webhooks & Events

## Overview
Set up webhook receivers for Notion's real-time event system. Notion delivers HTTP POST events when pages, databases, data sources, or comments change in your workspace.

## Prerequisites
- Notion integration with webhook capability
- HTTPS endpoint accessible from the internet
- Integration configured at https://www.notion.so/my-integrations
- Understanding of Notion's webhook event types

## Instructions

### Step 1: Configure Webhook in Integration Dashboard
1. Go to https://www.notion.so/my-integrations
2. Select your integration
3. Under **Webhooks**, click **Add webhook**
4. Enter your HTTPS endpoint URL
5. Notion sends a verification request to your endpoint

### Step 2: Handle Webhook Verification
```typescript
import express from 'express';

const app = express();
app.use(express.json());

app.post('/webhooks/notion', (req, res) => {
  // Notion sends a verification challenge during setup
  if (req.body.type === 'url_verification') {
    console.log('Webhook verification received');
    return res.status(200).json({ challenge: req.body.challenge });
  }

  // Handle real events (see Step 3)
  handleEvent(req.body);
  res.status(200).json({ ok: true });
});
```

### Step 3: Handle Webhook Events
Notion sends events for pages, databases, data sources, and comments:

```typescript
interface NotionWebhookEvent {
  type: string;
  data: {
    id: string;
    object: 'page' | 'database' | 'data_source' | 'comment';
    parent?: { type: string; page_id?: string; database_id?: string };
    [key: string]: any;
  };
  integration_id: string;
  authors: Array<{ id: string; type: 'person' | 'bot' }>;
  attempt_number: number;
  timestamp: string;
}

// Event types:
// page.created, page.deleted, page.moved
// page.content_updated, page.properties_updated, page.undeleted
// page.locked, page.unlocked
// database.created, database.deleted, database.moved
// database.schema_updated, database.content_updated
// data_source.schema_updated (API 2025-09-03)
// comment.created, comment.updated, comment.deleted

async function handleEvent(event: NotionWebhookEvent) {
  console.log(`Event: ${event.type} for ${event.data.object} ${event.data.id}`);

  switch (event.type) {
    case 'page.created':
      await onPageCreated(event.data.id);
      break;

    case 'page.properties_updated':
      await onPagePropertiesUpdated(event.data.id);
      break;

    case 'page.content_updated':
      await onPageContentUpdated(event.data.id);
      break;

    case 'page.deleted':
      await onPageDeleted(event.data.id);
      break;

    case 'database.schema_updated':
      await onSchemaChanged(event.data.id);
      break;

    case 'comment.created':
      await onCommentCreated(event.data.id);
      break;

    default:
      console.log(`Unhandled event: ${event.type}`);
  }
}
```

### Step 4: React to Events with the API
```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function onPageCreated(pageId: string) {
  // Fetch the full page to see what was created
  const page = await notion.pages.retrieve({ page_id: pageId });

  if ('properties' in page) {
    const title = page.properties.Name?.type === 'title'
      ? page.properties.Name.title.map(t => t.plain_text).join('')
      : 'Untitled';

    console.log(`New page: "${title}" created at ${page.created_time}`);

    // Example: Add a welcome comment
    await notion.comments.create({
      parent: { page_id: pageId },
      rich_text: [{ text: { content: 'Tracked by integration.' } }],
    });
  }
}

async function onPagePropertiesUpdated(pageId: string) {
  const page = await notion.pages.retrieve({ page_id: pageId });

  if ('properties' in page) {
    const status = page.properties.Status;
    if (status?.type === 'select' && status.select?.name === 'Done') {
      console.log(`Page ${pageId} marked as Done — triggering downstream action`);
      // Trigger external systems, send notifications, etc.
    }
  }
}

async function onPageContentUpdated(pageId: string) {
  // Fetch updated content
  const { results: blocks } = await notion.blocks.children.list({
    block_id: pageId,
  });
  console.log(`Page ${pageId} content updated: ${blocks.length} top-level blocks`);
}

async function onPageDeleted(pageId: string) {
  console.log(`Page ${pageId} was deleted (archived)`);
  // Clean up references, remove from cache, etc.
}

async function onSchemaChanged(dbId: string) {
  // Re-fetch database schema to update your integration
  const db = await notion.databases.retrieve({ database_id: dbId });
  console.log('Schema updated. Properties:', Object.keys(db.properties));
}

async function onCommentCreated(commentId: string) {
  const comment = await notion.comments.retrieve({ comment_id: commentId });
  const text = comment.rich_text.map(t => t.plain_text).join('');
  console.log(`New comment: "${text}"`);
}
```

### Step 5: Idempotent Event Processing
```typescript
// Notion may deliver events more than once — use idempotency
const processedEvents = new Set<string>();

async function handleEventIdempotent(event: NotionWebhookEvent) {
  const eventKey = `${event.type}:${event.data.id}:${event.timestamp}`;

  if (processedEvents.has(eventKey)) {
    console.log(`Skipping duplicate event: ${eventKey}`);
    return;
  }

  processedEvents.add(eventKey);
  await handleEvent(event);

  // Clean up old entries (keep last 1000)
  if (processedEvents.size > 1000) {
    const entries = Array.from(processedEvents);
    entries.slice(0, entries.length - 1000).forEach(e => processedEvents.delete(e));
  }
}
```

### Step 6: Webhook Actions (Database Automations)
Notion also supports webhook actions from database automations and buttons:

```typescript
// Webhook action payloads have a different structure
app.post('/webhooks/notion-action', express.json(), (req, res) => {
  // Webhook action sends the page data directly
  const { data } = req.body;
  console.log('Action triggered for page:', data.id);
  console.log('Properties:', data.properties);

  res.status(200).json({ ok: true });
});
```

Configure in Notion: Database `...` menu -> Automations -> Add action -> Send webhook.

## Output
- Webhook endpoint receiving real-time Notion events
- Verification handshake passing
- Event handlers for page, database, and comment changes
- Idempotent processing preventing duplicates

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Verification fails | Endpoint not returning challenge | Return `{ challenge }` for `url_verification` |
| Events not received | Webhook URL not HTTPS | Use HTTPS endpoint |
| Duplicate events | Network retry | Implement idempotency check |
| Event processing timeout | Slow handler | Respond 200 immediately, process async |
| Missing event types | Integration lacks capabilities | Enable required capabilities in dashboard |

## Examples

### Local Development with ngrok
```bash
# Expose local server for webhook testing
ngrok http 3000

# Use the ngrok URL in your integration's webhook settings
# https://xxxx.ngrok-free.app/webhooks/notion
```

## Resources
- [Notion Webhooks Reference](https://developers.notion.com/reference/webhooks)
- [Webhook Actions Help](https://www.notion.com/help/webhook-actions)
- [Working with Comments](https://developers.notion.com/docs/working-with-comments)

## Next Steps
For performance optimization, see `notion-performance-tuning`.
