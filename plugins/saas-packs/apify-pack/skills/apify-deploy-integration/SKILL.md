---
name: apify-deploy-integration
description: 'Deploy Apify Actors and integrate scraping into external applications.

  Use when deploying an Actor to the platform, integrating Actor results into a web
  app (Next.js, Express), wiring webhooks, or scheduling scraping pipelines.

  Trigger with "deploy apify actor", "apify Vercel integration",
  "apify production deploy", "integrate apify results", "apify API endpoint".

  '
allowed-tools: Read, Write, Edit, Bash(apify:*), Bash(npm:*), Bash(vercel:*), Bash(gcloud:*)
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify Deploy Integration

## Overview

Deploy Actors to the Apify platform and integrate their results into external
applications. Covers `apify push` deployment, API-triggered runs from web apps
(synchronous and async patterns), webhook receivers, scheduled scraping pipelines,
and container deployment.

SKILL.md gives you the workflow and the core skeleton. Complete, copy-paste code
for every pattern lives in [references/implementation.md](references/implementation.md);
end-to-end worked scenarios are in [references/examples.md](references/examples.md).

## Prerequisites

- Actor tested locally (`apify run`)
- `apify login` completed (stores CLI credentials)
- Target application ready for integration

## Authentication

Apps authenticate with an Apify API token. Generate one in **Apify Console →
Settings → Integrations** and expose it as the `APIFY_TOKEN` environment variable —
never hard-code it. The `apify` CLI uses its own credentials from `apify login`,
separate from `APIFY_TOKEN`. Full auth notes: [references/implementation.md](references/implementation.md).

## Instructions

### Step 1: Deploy the Actor to the platform

```bash
# Push Actor code to Apify
apify push

# Push to a specific Actor (creates if it doesn't exist)
apify push username/my-scraper

# Pull an existing Actor to modify
apify pull username/existing-actor
```

### Step 2: Trigger the Actor from your app

Instantiate `ApifyClient` with your token, then either `call()` (blocks until the
run finishes) or `start()` (returns immediately for polling). Here is the core
synchronous skeleton:

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

const run = await client.actor('username/product-scraper').call({
  startUrls: [{ url: 'https://store.example.com' }],
  maxItems: 500,
});
if (run.status !== 'SUCCEEDED') throw new Error(run.statusMessage);

const { items } = await client.dataset(run.defaultDatasetId).listItems();
```

The full typed service — `scrapeProducts` (blocking), `startScrape` +
`getScrapeResults` (async poll) — is in
[references/implementation.md](references/implementation.md).

### Step 3: Choose an integration pattern

Pick the pattern that matches your app, then copy the full handler from the
reference:

- **Next.js API route** — start a run in a `POST`, poll by run ID in a `GET`. Avoids
  serverless timeouts. See [implementation.md](references/implementation.md).
- **Express webhook receiver** — register an Apify webhook and react on
  `ACTOR.RUN.SUCCEEDED` / `FAILED` / `TIMED_OUT`. See [implementation.md](references/implementation.md).
- **Scheduled pipeline** — run on cron/Apify Schedule, export CSV, archive to a
  named dataset. See [implementation.md](references/implementation.md).
- **Docker / Cloud Run** — containerize an app that calls Apify, inject the token
  as a secret. See [implementation.md](references/implementation.md).

**Rule of thumb:** poll for request/response UX (a user waits on a result); use
webhooks for fire-and-forget pipelines (scheduled scrapes, background enrichment).

## Output

- A deployed Actor on the Apify platform (`apify push` build succeeds)
- An integration module (`src/services/apify.ts`) exposing blocking + async calls
- API routes / webhook receivers wired into your app's framework
- Structured results read from the Actor's default dataset (JSON or CSV export)
- Optional date-stamped archive in a named dataset for historical access

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `apify push` fails | Auth or build error | Check `apify login` and Dockerfile |
| Webhook not received | URL unreachable from internet | Use ngrok for dev; verify HTTPS in prod |
| Timeout in API route | Actor takes too long | Use async pattern (start + poll) |
| Memory error on platform | Actor needs more RAM | Increase `memory` option |
| Large dataset download | >100MB results | Use pagination or streaming |

## Examples

Three end-to-end scenarios — synchronous script call, non-blocking Next.js API,
and a scheduled CSV-export pipeline — are worked through in
[references/examples.md](references/examples.md). Minimal blocking call:

```typescript
import { scrapeProducts } from './services/apify';
const products = await scrapeProducts(['https://store.example.com/p/1']);
console.log(`Got ${products.length} products`);
```

## Resources

- [Actor Deployment](https://docs.apify.com/platform/actors/development/deployment)
- [API Integration Guide](https://docs.apify.com/platform/integrations/api)
- [Webhook Documentation](https://docs.apify.com/platform/integrations/webhooks)

## Next Steps

For webhook event handling in depth, see the `apify-webhooks-events` skill. For the
full integration code referenced above, see
[references/implementation.md](references/implementation.md).
