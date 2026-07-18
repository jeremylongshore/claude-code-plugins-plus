# Apify Webhooks — Full Implementation

Deep walkthrough for the webhook handler, idempotency, event-driven pipelines,
and lifecycle management. The lean skeletons live in `SKILL.md`; this file
carries the complete, production-ready code.

## Build the Webhook Handler

```typescript
import express from 'express';
import { ApifyClient } from 'apify-client';

const app = express();
const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

app.use(express.json());

// Webhook endpoint
app.post('/api/webhooks/apify', async (req, res) => {
  // Respond immediately (Apify expects 2xx within 30 seconds)
  res.status(200).json({ received: true });

  // Process asynchronously
  try {
    await processWebhook(req.body);
  } catch (error) {
    console.error('Webhook processing failed:', error);
  }
});

async function processWebhook(payload: {
  eventType: string;
  actorRunId: string;
  defaultDatasetId?: string;
  status: string;
  statusMessage?: string;
}) {
  const { eventType, actorRunId, defaultDatasetId } = payload;

  switch (eventType) {
    case 'ACTOR.RUN.SUCCEEDED': {
      if (!defaultDatasetId) return;

      // Fetch results from the dataset
      const { items } = await client
        .dataset(defaultDatasetId)
        .listItems({ limit: 10000 });

      console.log(`Run ${actorRunId} succeeded with ${items.length} items`);

      // Process results: save to DB, trigger downstream jobs, etc.
      await saveToDatabase(items);
      await notifyTeam(`Scrape completed: ${items.length} items`);
      break;
    }

    case 'ACTOR.RUN.FAILED':
    case 'ACTOR.RUN.TIMED_OUT': {
      console.error(`Run ${actorRunId} ${eventType}: ${payload.statusMessage}`);

      // Get full run log for debugging
      const log = await client.run(actorRunId).log().get();
      await alertOncall({
        subject: `Apify run ${eventType}`,
        runId: actorRunId,
        message: payload.statusMessage,
        logTail: log?.slice(-1000),
      });
      break;
    }

    case 'ACTOR.RUN.ABORTED':
      console.warn(`Run ${actorRunId} was aborted`);
      break;

    default:
      console.log(`Unhandled event: ${eventType}`);
  }
}
```

## Idempotent Processing

Webhooks may be delivered more than once. Guard against duplicates:

```typescript
// Using a Set for in-memory dedup (use Redis/DB in production)
const processedRuns = new Set<string>();

async function processWebhookIdempotent(payload: {
  actorRunId: string;
  eventType: string;
}) {
  const dedupeKey = `${payload.actorRunId}:${payload.eventType}`;

  if (processedRuns.has(dedupeKey)) {
    console.log(`Skipping duplicate: ${dedupeKey}`);
    return;
  }

  processedRuns.add(dedupeKey);

  // Process the webhook...
  await processWebhook(payload);

  // Cleanup old entries (keep last 10000)
  if (processedRuns.size > 10000) {
    const entries = Array.from(processedRuns);
    entries.slice(0, entries.length - 10000).forEach(e => processedRuns.delete(e));
  }
}
```

## Event-Driven Pipeline

Chain Actors together using webhooks:

```typescript
// Actor A finishes → webhook triggers → start Actor B

app.post('/api/webhooks/pipeline', async (req, res) => {
  res.status(200).json({ received: true });

  const { eventType, actorRunId, defaultDatasetId } = req.body;

  if (eventType !== 'ACTOR.RUN.SUCCEEDED') return;

  // Stage 1 completed, start Stage 2
  console.log(`Pipeline Stage 1 done (run ${actorRunId}). Starting Stage 2...`);

  const stage2Run = await client.actor('username/data-processor').start(
    {
      sourceDatasetId: defaultDatasetId,
      outputFormat: 'json',
    },
    {
      webhooks: [{
        eventTypes: ['ACTOR.RUN.SUCCEEDED', 'ACTOR.RUN.FAILED'],
        requestUrl: 'https://your-app.com/api/webhooks/pipeline-stage3',
      }],
    },
  );

  console.log(`Stage 2 started: ${stage2Run.id}`);
});
```

## Manage Webhooks

```typescript
// List all webhooks
const { items: webhooks } = await client.webhooks().list();
webhooks.forEach(wh => {
  console.log(`${wh.id} | ${wh.eventTypes.join(',')} | ${wh.requestUrl}`);
});

// Update a webhook
await client.webhook('WEBHOOK_ID').update({
  requestUrl: 'https://new-url.com/webhook',
  isEnabled: true,
});

// Delete a webhook
await client.webhook('WEBHOOK_ID').delete();

// Get webhook dispatch history (see delivery attempts)
const { items: dispatches } = await client
  .webhook('WEBHOOK_ID')
  .dispatches()
  .list();
dispatches.forEach(d => {
  console.log(`${d.status} | ${d.createdAt} | HTTP ${d.responseStatus}`);
});
```
