---
name: apify-core-workflow-b
description: |
  Manage Apify datasets, key-value stores, and request queues programmatically.
  Use when reading/writing datasets, exporting data, managing Actor storage,
  or orchestrating multi-Actor pipelines.
  Trigger: "apify dataset", "apify key-value store", "apify storage",
  "export apify data", "apify pipeline", "apify request queue".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Core Workflow B — Storage & Pipelines

## Overview

Manage Apify's three storage types (datasets, key-value stores, request queues) and orchestrate multi-Actor pipelines. Covers CRUD operations, data export, pagination, and chaining Actors together.

## Prerequisites

- `apify-client` installed and authenticated
- Familiarity with `apify-core-workflow-a`

## Storage Types at a Glance

| Storage | Best For | Analogy | Retention |
|---------|----------|---------|-----------|
| Dataset | Lists of similar items (products, pages) | Append-only table | 7 days (unnamed) |
| Key-Value Store | Config, screenshots, summaries, any file | S3 bucket | 7 days (unnamed) |
| Request Queue | URLs to crawl (managed by Crawlee) | Job queue | 7 days (unnamed) |

Named storages persist indefinitely. Unnamed (default run) storages expire after 7 days.

## Instructions

### Step 1: Dataset Operations

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

// Create a named dataset (persists indefinitely)
const dataset = await client.datasets().getOrCreate('product-catalog');
const dsClient = client.dataset(dataset.id);

// Push items (single or batch)
await dsClient.pushItems([
  { sku: 'ABC123', name: 'Widget', price: 9.99 },
  { sku: 'DEF456', name: 'Gadget', price: 19.99 },
]);

// List items with pagination
const page1 = await dsClient.listItems({ limit: 100, offset: 0 });
console.log(`Total items: ${page1.total}, this page: ${page1.items.length}`);

// Iterate all items (handles pagination automatically)
let offset = 0;
const limit = 1000;
const allItems = [];
while (true) {
  const { items } = await dsClient.listItems({ limit, offset });
  if (items.length === 0) break;
  allItems.push(...items);
  offset += items.length;
}

// Download in various formats
const csvBuffer = await dsClient.downloadItems('csv');
const jsonBuffer = await dsClient.downloadItems('json');
const xlsxBuffer = await dsClient.downloadItems('xlsx');

// Download filtered/transformed
const filtered = await dsClient.downloadItems('json', {
  fields: ['sku', 'name', 'price'],   // Only these fields
  unwind: 'variants',                  // Flatten nested arrays
  desc: true,                          // Reverse order
});

// Get dataset info (item count, size)
const info = await dsClient.get();
console.log(`${info.itemCount} items, ${info.actSize} bytes`);
```

### Step 2: Key-Value Store Operations

```typescript
// Create a named store
const store = await client.keyValueStores().getOrCreate('scraper-config');
const kvClient = client.keyValueStore(store.id);

// Store JSON config
await kvClient.setRecord({
  key: 'settings',
  value: { maxRetries: 3, proxy: 'residential', country: 'US' },
  contentType: 'application/json',
});

// Store binary data (screenshot, PDF)
import { readFileSync } from 'fs';
await kvClient.setRecord({
  key: 'report.pdf',
  value: readFileSync('report.pdf'),
  contentType: 'application/pdf',
});

// Retrieve a record
const record = await kvClient.getRecord('settings');
console.log(record.value); // { maxRetries: 3, proxy: 'residential', ... }

// List all keys in the store
const { items: keys } = await kvClient.listKeys();
keys.forEach(k => console.log(`${k.key} (${k.size} bytes)`));

// Delete a record
await kvClient.deleteRecord('old-config');

// Access an Actor run's default stores
const run = await client.actor('apify/web-scraper').call(input);
const runKv = client.keyValueStore(run.defaultKeyValueStoreId);
const output = await runKv.getRecord('OUTPUT');
```

### Step 3: Request Queue Management

```typescript
// Create a named request queue (useful for resumable crawls)
const queue = await client.requestQueues().getOrCreate('my-crawl-queue');
const rqClient = client.requestQueue(queue.id);

// Add requests
await rqClient.addRequest({ url: 'https://example.com/page1', uniqueKey: 'page1' });

// Batch add (up to 25 per call)
await rqClient.batchAddRequests([
  { url: 'https://example.com/page2', uniqueKey: 'page2' },
  { url: 'https://example.com/page3', uniqueKey: 'page3' },
]);

// Get queue info
const queueInfo = await rqClient.get();
console.log(`Pending: ${queueInfo.pendingRequestCount}, Handled: ${queueInfo.handledRequestCount}`);
```

### Step 4: Multi-Actor Pipeline

```typescript
// Pipeline: Scrape -> Transform -> Export
async function runPipeline(urls: string[]) {
  const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

  // Stage 1: Scrape raw data
  console.log('Stage 1: Scraping...');
  const scrapeRun = await client.actor('username/product-scraper').call({
    startUrls: urls.map(url => ({ url })),
    maxItems: 1000,
  });
  const { items: rawData } = await client
    .dataset(scrapeRun.defaultDatasetId)
    .listItems();
  console.log(`Scraped ${rawData.length} items`);

  // Stage 2: Transform (using a data-processing Actor)
  console.log('Stage 2: Transforming...');
  const transformRun = await client.actor('username/data-transformer').call({
    datasetId: scrapeRun.defaultDatasetId,
    transformations: {
      dedup: { field: 'sku' },
      filter: { field: 'price', operator: 'gt', value: 0 },
    },
  });

  // Stage 3: Export to named dataset for long-term storage
  console.log('Stage 3: Exporting...');
  const { items: cleanData } = await client
    .dataset(transformRun.defaultDatasetId)
    .listItems();

  const exportDs = await client.datasets().getOrCreate('product-catalog-clean');
  await client.dataset(exportDs.id).pushItems(cleanData);

  console.log(`Pipeline complete. ${cleanData.length} clean items stored.`);
  return exportDs.id;
}
```

### Step 5: Monitor Actor Runs

```typescript
// List recent runs for an Actor
const { items: runs } = await client.actor('username/my-actor').runs().list({
  limit: 10,
  desc: true,
});

runs.forEach(run => {
  console.log(`${run.id} | ${run.status} | ${run.startedAt} | ${run.usageTotalUsd?.toFixed(4)} USD`);
});

// Get detailed run info
const runDetail = await client.run('RUN_ID').get();
console.log({
  status: runDetail.status,
  statusMessage: runDetail.statusMessage,
  datasetItems: runDetail.stats?.datasetItemCount,
  computeUnits: runDetail.usage?.ACTOR_COMPUTE_UNITS,
  durationSecs: runDetail.stats?.runTimeSecs,
});

// Abort a running Actor
await client.run('RUN_ID').abort();
```

## Data Flow Diagram

```
Actor Run
  ├── Default Dataset      ← Actor.pushData() writes here
  ├── Default KV Store     ← Actor.setValue() writes here
  │     ├── INPUT          ← Input passed at run start
  │     └── OUTPUT         ← Convention for main output
  └── Default Request Queue ← Crawlee manages this
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Dataset not found` | Expired (unnamed, >7 days) | Use named datasets for persistence |
| `Record too large` | KV store 9MB record limit | Split into multiple records |
| `Push failed` | Dataset items >9MB batch | Push in smaller batches |
| `Request already exists` | Duplicate uniqueKey | Expected behavior, queue deduplicates |

## Resources

- [Dataset Documentation](https://docs.apify.com/platform/storage/dataset)
- [Key-Value Store Documentation](https://docs.apify.com/platform/storage/key-value-store)
- [Request Queue Documentation](https://docs.apify.com/platform/storage/request-queue)
- [JS Client API Reference](https://docs.apify.com/api/client/js/reference)

## Next Steps

For common errors, see `apify-common-errors`.
