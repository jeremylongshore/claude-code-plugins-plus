---
name: apify-deploy-integration
description: |
  Deploy Apify Actors and integrate scraping into external applications.
  Use when deploying Actors to the platform, integrating Actor results
  into web apps, or connecting Apify with external services.
  Trigger: "deploy apify actor", "apify Vercel integration",
  "apify production deploy", "integrate apify results", "apify API endpoint".
allowed-tools: Read, Write, Edit, Bash(apify:*), Bash(npm:*), Bash(vercel:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Deploy Integration

## Overview

Deploy Actors to the Apify platform and integrate their results into external applications. Covers `apify push` deployment, API-triggered runs from web apps, scheduled scraping with data pipelines, and platform-specific integration patterns.

## Prerequisites

- Actor tested locally (`apify run`)
- `apify login` completed
- Target application ready for integration

## Instructions

### Step 1: Deploy Actor to Platform

```bash
# Push Actor code to Apify
apify push

# Push to a specific Actor (creates if doesn't exist)
apify push username/my-scraper

# Pull an existing Actor to modify
apify pull username/existing-actor
```

### Step 2: Integrate with a Web Application

The most common pattern: trigger an Actor from your app and consume results.

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

### Step 3: Next.js API Route Integration

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

### Step 4: Express.js Webhook Receiver

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

### Step 5: Scheduled Pipeline with Data Export

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

### Step 6: Docker Deployment (Self-Hosted Integration)

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

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `apify push` fails | Auth or build error | Check `apify login` and Dockerfile |
| Webhook not received | URL unreachable from internet | Use ngrok for dev; verify HTTPS in prod |
| Timeout in API route | Actor takes too long | Use async pattern (start + poll) |
| Memory error on platform | Actor needs more RAM | Increase `memory` option |
| Large dataset download | >100MB results | Use pagination or streaming |

## Resources

- [Actor Deployment](https://docs.apify.com/platform/actors/development/deployment)
- [API Integration Guide](https://docs.apify.com/platform/integrations/api)
- [Webhook Documentation](https://docs.apify.com/platform/integrations/webhooks)

## Next Steps

For webhook handling, see `apify-webhooks-events`.
