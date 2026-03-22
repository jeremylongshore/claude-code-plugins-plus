---
name: apify-hello-world
description: |
  Run your first Apify Actor and retrieve results via apify-client.
  Use when starting a new Apify integration, testing connectivity,
  or learning the Actor call/dataset retrieval pattern.
  Trigger: "apify hello world", "apify example", "run an apify actor",
  "apify quick start", "first apify scrape".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Hello World

## Overview

Run a public Actor from the Apify Store, wait for it to finish, and retrieve the scraped data. This demonstrates the fundamental call-wait-collect pattern used in every Apify integration.

## Prerequisites

- `npm install apify-client` completed
- `APIFY_TOKEN` environment variable set
- See `apify-install-auth` if not ready

## Core Pattern: Call Actor, Get Data

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

// 1. Run an Actor and wait for it to finish
const run = await client.actor('apify/website-content-crawler').call({
  startUrls: [{ url: 'https://docs.apify.com/academy' }],
  maxCrawlPages: 5,
});

// 2. Retrieve results from the default dataset
const { items } = await client.dataset(run.defaultDatasetId).listItems();

console.log(`Crawled ${items.length} pages:`);
items.forEach(item => {
  console.log(`  - ${item.url}: ${item.text?.substring(0, 80)}...`);
});
```

## Instructions

### Step 1: Create the Script

Create `hello-apify.ts` (or `.js`) with the code above.

### Step 2: Run It

```bash
# With tsx (recommended)
npx tsx hello-apify.ts

# Or with Node.js (plain JS)
node hello-apify.js
```

### Step 3: Understand the Output

The Actor runs on Apify's cloud infrastructure. When it finishes:
- `run.id` — unique run identifier
- `run.status` — `SUCCEEDED`, `FAILED`, `TIMED-OUT`, or `ABORTED`
- `run.defaultDatasetId` — ID of the dataset containing results
- `run.defaultKeyValueStoreId` — ID of the KV store with metadata

## Popular Starter Actors

| Actor ID | Purpose | Typical Input |
|----------|---------|---------------|
| `apify/website-content-crawler` | Crawl and extract text | `{ startUrls, maxCrawlPages }` |
| `apify/web-scraper` | General-purpose scraper | `{ startUrls, pageFunction }` |
| `apify/cheerio-scraper` | Fast HTML scraper | `{ startUrls, pageFunction }` |
| `apify/google-search-scraper` | Google SERP results | `{ queries, maxPagesPerQuery }` |

## Synchronous vs Asynchronous Runs

```typescript
// SYNCHRONOUS — .call() waits for the Actor to finish (simple, blocking)
const run = await client.actor('apify/web-scraper').call(input);

// ASYNCHRONOUS — .start() returns immediately, poll later
const run = await client.actor('apify/web-scraper').start(input);
// ... do other work ...
const finishedRun = await client.run(run.id).waitForFinish();
```

## Working with Results

```typescript
// Get all items (paginated internally)
const { items } = await client.dataset(run.defaultDatasetId).listItems();

// Get items with pagination control
const page1 = await client.dataset(run.defaultDatasetId).listItems({
  limit: 100,
  offset: 0,
});

// Download entire dataset as CSV/JSON/etc.
const buffer = await client.dataset(run.defaultDatasetId).downloadItems('csv');

// Get a named output from the key-value store
const screenshot = await client
  .keyValueStore(run.defaultKeyValueStoreId)
  .getRecord('screenshot');
```

## Run Configuration Options

```typescript
const run = await client.actor('apify/web-scraper').call(
  input,       // Actor-specific input object
  {
    memory: 1024,          // Memory in MB (128–32768, powers of 2)
    timeout: 300,          // Timeout in seconds (default: Actor's setting)
    build: 'latest',       // Which build to use
    waitSecs: 120,         // Max wait for .call() (0 = don't wait)
  }
);
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Actor not found` | Wrong Actor ID | Check ID at apify.com/store |
| `run.status === 'FAILED'` | Actor crashed | Check `run.statusMessage` for details |
| `run.status === 'TIMED-OUT'` | Exceeded timeout | Increase `timeout` or reduce workload |
| `Dataset is empty` | Actor produced no output | Verify input parameters; check Actor logs |
| `402 Payment Required` | Insufficient compute units | Top up at console.apify.com/billing |

## Complete Example: Scrape and Save

```typescript
import { ApifyClient } from 'apify-client';
import { writeFileSync } from 'fs';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

async function scrapeAndSave() {
  console.log('Starting Actor run...');

  const run = await client.actor('apify/website-content-crawler').call({
    startUrls: [{ url: 'https://example.com' }],
    maxCrawlPages: 10,
  });

  if (run.status !== 'SUCCEEDED') {
    throw new Error(`Actor run failed: ${run.status} — ${run.statusMessage}`);
  }

  const { items } = await client.dataset(run.defaultDatasetId).listItems();
  writeFileSync('results.json', JSON.stringify(items, null, 2));
  console.log(`Saved ${items.length} items to results.json`);
}

scrapeAndSave().catch(console.error);
```

## Resources

- [Apify Store — Browse Actors](https://apify.com/store)
- [Run Actor via API](https://docs.apify.com/academy/api/run-actor-and-retrieve-data-via-api)
- [JS Client Examples](https://docs.apify.com/api/client/js/docs/guides/examples)

## Next Steps

Proceed to `apify-local-dev-loop` for local Actor development.
