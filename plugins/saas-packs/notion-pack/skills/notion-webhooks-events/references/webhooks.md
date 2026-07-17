# Native Webhooks (API 2025-02+)

Notion's native webhooks deliver HTTP POST notifications when pages, databases, comments, or data sources change. They notify you that something changed — you then call the API to fetch the actual data.

## Register and Verify a Webhook Endpoint

```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();
app.use(express.json());

// Step A: Handle the verification challenge during webhook registration
// Notion sends { type: "url_verification", challenge: "..." }
app.post('/webhooks/notion', (req, res) => {
  if (req.body.type === 'url_verification') {
    console.log('Webhook verification received');
    return res.status(200).json({ challenge: req.body.challenge });
  }

  // Step B: Process real events
  handleWebhookEvent(req.body);
  // Always respond 200 quickly — do heavy processing async
  res.status(200).json({ ok: true });
});

app.listen(3000, () => console.log('Webhook receiver on :3000'));
```

## Handle Webhook Events

```typescript
interface NotionWebhookEvent {
  type: string;
  data: {
    id: string;
    object: 'page' | 'database' | 'data_source' | 'comment';
    parent?: { type: string; page_id?: string; database_id?: string };
  };
  integration_id: string;
  authors: Array<{ id: string; type: 'person' | 'bot' }>;
  attempt_number: number;
  timestamp: string;
}

// Supported event types:
//   page.created, page.deleted, page.moved, page.undeleted
//   page.content_updated, page.properties_updated
//   page.locked, page.unlocked
//   database.created, database.deleted, database.moved
//   database.schema_updated, database.content_updated
//   comment.created, comment.updated, comment.deleted
//   data_source.schema_updated

async function handleWebhookEvent(event: NotionWebhookEvent) {
  console.log(`[webhook] ${event.type} → ${event.data.object} ${event.data.id}`);

  switch (event.type) {
    case 'page.content_updated':
    case 'page.properties_updated':
      // Fetch the page to see what actually changed
      const page = await notion.pages.retrieve({ page_id: event.data.id });
      await processPageUpdate(page, event.type);
      break;

    case 'page.created':
      const newPage = await notion.pages.retrieve({ page_id: event.data.id });
      await processNewPage(newPage);
      break;

    case 'page.deleted':
      await handlePageDeletion(event.data.id);
      break;

    case 'database.schema_updated':
      const db = await notion.databases.retrieve({ database_id: event.data.id });
      console.log('Schema changed. Properties:', Object.keys(db.properties));
      break;

    case 'comment.created':
      await handleNewComment(event.data.id);
      break;

    default:
      console.log(`Unhandled event type: ${event.type}`);
  }
}
```

## Debouncing and Deduplication

Notion may deliver events more than once (retries on non-200 responses). Rapid edits can also produce a burst of events for the same resource. Handle both:

```typescript
// Deduplication: skip events we have already processed
const processedEvents = new Map<string, number>(); // key → timestamp

function isDuplicate(event: NotionWebhookEvent): boolean {
  const key = `${event.type}:${event.data.id}:${event.timestamp}`;
  if (processedEvents.has(key)) return true;

  processedEvents.set(key, Date.now());
  // Prune entries older than 10 minutes
  const cutoff = Date.now() - 10 * 60 * 1000;
  for (const [k, ts] of processedEvents) {
    if (ts < cutoff) processedEvents.delete(k);
  }
  return false;
}

// Debouncing: collapse rapid edits into one processing call
const pendingDebounce = new Map<string, NodeJS.Timeout>();
const DEBOUNCE_MS = 2000;

function debounceEvent(
  event: NotionWebhookEvent,
  handler: (event: NotionWebhookEvent) => Promise<void>
) {
  const resourceKey = `${event.data.object}:${event.data.id}`;

  const existing = pendingDebounce.get(resourceKey);
  if (existing) clearTimeout(existing);

  pendingDebounce.set(
    resourceKey,
    setTimeout(async () => {
      pendingDebounce.delete(resourceKey);
      await handler(event);
    }, DEBOUNCE_MS)
  );
}

// Combined entry point
async function onWebhookReceived(event: NotionWebhookEvent) {
  if (isDuplicate(event)) {
    console.log(`Skipping duplicate: ${event.type} ${event.data.id}`);
    return;
  }
  debounceEvent(event, handleWebhookEvent);
}
```
