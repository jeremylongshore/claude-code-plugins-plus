# Apify Deploy & Integration — Full Implementation

Deep, copy-paste implementations for every integration pattern the skill covers.
Read `SKILL.md` first for the high-level workflow; drill in here for complete code.

## Authentication

Every integration authenticates with an Apify API token. Generate one at
**Apify Console → Settings → Integrations** and expose it to your app as the
`APIFY_TOKEN` environment variable (never hard-code it):

```bash
export APIFY_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

```typescript
import { ApifyClient } from 'apify-client';

// The client reads the token you pass; keep it in env, not source.
const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
```

For platform CLI operations (`apify push`, `apify pull`) run `apify login` once —
the CLI stores its own credentials separately from `APIFY_TOKEN`.

## Web Application Integration Service

The most common pattern: trigger an Actor from your app and consume results.
This service module exposes synchronous (blocking) and asynchronous (start + poll)
entry points.

```typescript
// src/services/apify.ts
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

interface ScrapeResult {
  url: string;
  title: string;
  price: number;
  inStock: boolean;
}

/**
 * Run a scraping Actor and return typed results.
 * Blocks until the Actor finishes (synchronous pattern).
 */
export async function scrapeProducts(urls: string[]): Promise<ScrapeResult[]> {
  const run = await client.actor('username/product-scraper').call({
    startUrls: urls.map(url => ({ url })),
    maxItems: 500,
  }, {
    memory: 2048,
    timeout: 600,  // 10 minutes
  });

  if (run.status !== 'SUCCEEDED') {
    throw new Error(`Scrape failed: ${run.status} — ${run.statusMessage}`);
  }

  const { items } = await client.dataset(run.defaultDatasetId).listItems();
  return items as ScrapeResult[];
}

/**
 * Start a scraping Actor without waiting (async pattern).
 * Returns run ID for later polling.
 */
export async function startScrape(urls: string[]): Promise<string> {
  const run = await client.actor('username/product-scraper').start({
    startUrls: urls.map(url => ({ url })),
  });
  return run.id;
}

/**
 * Check if a run has finished and get results.
 */
export async function getScrapeResults(runId: string): Promise<{
  status: string;
  items?: ScrapeResult[];
}> {
  const run = await client.run(runId).get();

  if (run.status === 'RUNNING' || run.status === 'READY') {
    return { status: run.status };
  }

  if (run.status === 'SUCCEEDED') {
    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    return { status: 'SUCCEEDED', items: items as ScrapeResult[] };
  }

  return { status: run.status };
}
```

## Next.js API Route Integration

Wire the async pattern into a Next.js App Router: one route starts the run, a
second route polls by run ID.

```typescript
// app/api/scrape/route.ts (Next.js App Router)
import { NextResponse } from 'next/server';
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

export async function POST(request: Request) {
  const { urls } = await request.json();

  if (!urls?.length) {
    return NextResponse.json({ error: 'urls required' }, { status: 400 });
  }

  try {
    // Start Actor (non-blocking)
    const run = await client.actor('username/product-scraper').start({
      startUrls: urls.map((url: string) => ({ url })),
      maxItems: 100,
    });

    return NextResponse.json({
      runId: run.id,
      status: run.status,
      statusUrl: `/api/scrape/${run.id}`,
    });
  } catch (error) {
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 500 },
    );
  }
}

// app/api/scrape/[runId]/route.ts
export async function GET(
  _req: Request,
  { params }: { params: { runId: string } },
) {
  const run = await client.run(params.runId).get();

  if (run.status === 'SUCCEEDED') {
    const { items } = await client
      .dataset(run.defaultDatasetId)
      .listItems({ limit: 100 });
    return NextResponse.json({ status: 'SUCCEEDED', items });
  }

  return NextResponse.json({
    status: run.status,
    statusMessage: run.statusMessage,
  });
}
```

## Express.js Webhook Receiver

Instead of polling, register an Apify webhook that POSTs to your server when a run
completes. This receiver dispatches on event type.

```typescript
// Receive notifications when an Actor run completes
import express from 'express';
import { ApifyClient } from 'apify-client';

const app = express();
const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

app.use(express.json());

app.post('/webhooks/apify', async (req, res) => {
  const { eventType, eventData } = req.body;

  // Verify the webhook (check run exists)
  const { actorRunId } = eventData;
  const run = await client.run(actorRunId).get();

  if (!run) {
    return res.status(400).json({ error: 'Invalid run ID' });
  }

  switch (eventType) {
    case 'ACTOR.RUN.SUCCEEDED': {
      const { items } = await client
        .dataset(run.defaultDatasetId)
        .listItems();
      console.log(`Run succeeded with ${items.length} items`);
      // Process items: save to DB, send notifications, etc.
      await processScrapedData(items);
      break;
    }

    case 'ACTOR.RUN.FAILED':
    case 'ACTOR.RUN.TIMED_OUT':
      console.error(`Run ${eventType}: ${run.statusMessage}`);
      // Alert team via Slack, PagerDuty, etc.
      await sendAlert(`Apify run ${eventType}: ${run.statusMessage}`);
      break;
  }

  res.json({ received: true });
});
```

## Scheduled Pipeline with Data Export

Run an Actor on a cron or Apify Schedule, export to CSV, and archive into a named
dataset for historical access.

```typescript
// Run daily via cron, schedule, or Apify Schedule
import { ApifyClient } from 'apify-client';
import { writeFileSync } from 'fs';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

async function dailyScrapeAndExport() {
  // Run Actor
  const run = await client.actor('username/product-scraper').call({
    startUrls: [{ url: 'https://target-store.com/products' }],
    maxItems: 5000,
  });

  if (run.status !== 'SUCCEEDED') {
    throw new Error(`Run failed: ${run.status}`);
  }

  // Export as CSV
  const csvBuffer = await client
    .dataset(run.defaultDatasetId)
    .downloadItems('csv');
  writeFileSync(`exports/products-${Date.now()}.csv`, csvBuffer);

  // Also store in a named dataset for historical access
  const archive = await client.datasets().getOrCreate('product-archive');
  const { items } = await client.dataset(run.defaultDatasetId).listItems();
  await client.dataset(archive.id).pushItems(
    items.map(item => ({ ...item, scrapedDate: new Date().toISOString() })),
  );

  console.log(`Exported ${items.length} products`);
}
```

## Docker Deployment (Self-Hosted Integration)

Package an app that calls Apify into a container and ship it anywhere — plain
Docker or Cloud Run with the token injected as a secret.

```dockerfile
# Dockerfile for an app that calls Apify
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY . .
CMD ["node", "dist/index.js"]
```

```bash
# Build and deploy
docker build -t apify-integration .
docker run -e APIFY_TOKEN=apify_api_xxx apify-integration

# Or deploy to Cloud Run
gcloud run deploy apify-service \
  --source . \
  --set-secrets=APIFY_TOKEN=apify-token:latest \
  --region us-central1
```

## Integration Architecture

```
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│  Your App      │────▶│  Apify API   │────▶│  Actor Run     │
│  (apify-client)│     │              │     │  (on Apify     │
│                │◀────│              │◀────│   platform)    │
└────────────────┘     └──────────────┘     └────────────────┘
       │                                           │
       │  Poll or Webhook                          │
       ▼                                           ▼
┌────────────────┐                        ┌────────────────┐
│  Your DB       │                        │  Dataset       │
│  (processed)   │                        │  (raw results) │
└────────────────┘                        └────────────────┘
```

Choose polling for request/response UX (a user waits on a result) and webhooks for
fire-and-forget pipelines (scheduled scrapes, background enrichment).
