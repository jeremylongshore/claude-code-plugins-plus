---
name: apify-core-workflow-b
description: |
  Manage Apify datasets, key-value stores, and request queues programmatically,
  and orchestrate multi-Actor pipelines.

  Use when you need to read or write Apify datasets, export scraped data to
  CSV/JSON/XLSX, store config or binary artifacts in a key-value store, manage a
  resumable request queue, chain Actors into a scrape → transform → export
  pipeline, or monitor Actor run status and cost.

  Trigger with "apify dataset", "apify key-value store", "apify storage",
  "export apify data", "apify pipeline", "apify request queue".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
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
# Apify Core Workflow B — Storage & Pipelines

## Overview

Manage Apify's three storage types (datasets, key-value stores, request queues)
and orchestrate multi-Actor pipelines using the `apify-client` JS SDK. Covers
CRUD operations, data export, automatic pagination, and chaining Actors
together (scrape → transform → export).

This SKILL.md gives you the high-level workflow plus the essential first example
for each storage type. Drill into the reference files for the complete,
copy-ready code:

- **[Storage operations — full reference](references/storage-operations.md)** —
  every dataset, key-value store, and request queue operation with pagination,
  format export, and binary records.
- **[Pipelines & run monitoring — full reference](references/pipelines.md)** —
  the multi-Actor pipeline function and Actor-run status/cost/abort monitoring.

## Prerequisites

- Node.js with `apify-client` installed (`npm install apify-client`).
- An Apify account token exported as `APIFY_TOKEN` (see Authentication below).
- Familiarity with `apify-core-workflow-a` (Actor invocation and run lifecycle),
  since pipelines chain Actor runs and read their default storages.

## Authentication

All operations authenticate with an Apify API token. Never hard-code it —
read it from the environment and construct the client once:

```typescript
import { ApifyClient } from 'apify-client';
const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
```

Generate a token at Apify Console → Settings → Integrations, then export it
(`export APIFY_TOKEN=apify_api_...`) or load it from your secrets manager.

## Storage Types at a Glance

| Storage | Best For | Analogy | Retention |
|---------|----------|---------|-----------|
| Dataset | Lists of similar items (products, pages) | Append-only table | 7 days (unnamed) |
| Key-Value Store | Config, screenshots, summaries, any file | S3 bucket | 7 days (unnamed) |
| Request Queue | URLs to crawl (managed by Crawlee) | Job queue | 7 days (unnamed) |

Named storages persist indefinitely. Unnamed (default run) storages expire after 7 days.

## Instructions

Pick the storage type you need, use the skeleton below to get started, then open
the linked reference for the full operation set.

### Datasets — append-only item lists

`getOrCreate` a named dataset, push items, and list them (pagination is manual):

```typescript
const dataset = await client.datasets().getOrCreate('product-catalog');
const dsClient = client.dataset(dataset.id);
await dsClient.pushItems([{ sku: 'ABC123', name: 'Widget', price: 9.99 }]);
const { items, total } = await dsClient.listItems({ limit: 100, offset: 0 });
```

Full auto-pagination loop, CSV/JSON/XLSX export, and field filtering:
**[storage-operations.md, Step 1](references/storage-operations.md)**.

### Key-value stores — config, files, and Actor OUTPUT

Store JSON or binary records by key, then retrieve them:

```typescript
const store = await client.keyValueStores().getOrCreate('scraper-config');
const kvClient = client.keyValueStore(store.id);
await kvClient.setRecord({ key: 'settings', value: { maxRetries: 3 }, contentType: 'application/json' });
const record = await kvClient.getRecord('settings');
```

Binary records, key listing, and reading a run's default `OUTPUT`:
**[storage-operations.md, Step 2](references/storage-operations.md)**.

### Request queues — resumable crawl URLs

Create a named queue and add requests (deduplicated by `uniqueKey`):

```typescript
const queue = await client.requestQueues().getOrCreate('my-crawl-queue');
const rqClient = client.requestQueue(queue.id);
await rqClient.addRequest({ url: 'https://example.com/page1', uniqueKey: 'page1' });
```

Batch adds and queue stats:
**[storage-operations.md, Step 3](references/storage-operations.md)**.

### Multi-Actor pipelines & monitoring

Chain Actors (scrape → transform → export) and monitor run status and cost.
Full `runPipeline()` function and run-monitoring code:
**[pipelines.md](references/pipelines.md)**.

## Output

- **Datasets** return `{ items, total, count, offset, limit }` from `listItems()`;
  `downloadItems(format)` returns a `Buffer` in `csv` / `json` / `xlsx`.
- **Key-value stores** return `{ key, value, contentType }` from `getRecord()`
  and `{ items }` (each `{ key, size }`) from `listKeys()`.
- **Request queues** return `{ pendingRequestCount, handledRequestCount, ... }`
  from `get()`.
- **Pipelines** return the named export dataset id; run monitoring yields
  `{ status, statusMessage, stats, usage, usageTotalUsd }` per run.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Dataset not found` | Expired (unnamed, >7 days) | Use named datasets for persistence |
| `Record too large` | KV store 9MB record limit | Split into multiple records |
| `Push failed` | Dataset items >9MB batch | Push in smaller batches |
| `Request already exists` | Duplicate uniqueKey | Expected behavior, queue deduplicates |

## Examples

**Export a named dataset to CSV** — get the client, download the buffer, write it:

```typescript
const csvBuffer = await client.dataset('product-catalog').downloadItems('csv');
require('fs').writeFileSync('products.csv', csvBuffer);
```

**Read an Actor run's OUTPUT record** — after a run completes:

```typescript
const run = await client.actor('apify/web-scraper').call(input);
const output = await client.keyValueStore(run.defaultKeyValueStoreId).getRecord('OUTPUT');
```

Longer end-to-end examples — the full pagination loop, binary record storage,
and the three-stage `runPipeline()` — live in the reference files:
[storage-operations.md](references/storage-operations.md) and
[pipelines.md](references/pipelines.md).

## Resources

- [Dataset Documentation](https://docs.apify.com/platform/storage/dataset)
- [Key-Value Store Documentation](https://docs.apify.com/platform/storage/key-value-store)
- [Request Queue Documentation](https://docs.apify.com/platform/storage/request-queue)
- [JS Client API Reference](https://docs.apify.com/api/client/js/reference)

## Next Steps

For common errors and their fixes across the Apify pack, see the
`apify-common-errors` skill. For Actor invocation and run lifecycle basics that
pipelines build on, see `apify-core-workflow-a`.
