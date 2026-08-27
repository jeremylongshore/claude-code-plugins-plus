---
name: apify-hello-world
description: |
  Run your first Apify Actor and retrieve results via apify-client.
  Use when starting a new Apify integration, testing connectivity,
  or learning the Actor call/dataset retrieval pattern.
  Trigger with "apify hello world", "apify example", "run an apify actor",
  "apify quick start", "first apify scrape".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(node:*)
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
# Apify Hello World

## Overview

Run a public Actor from the Apify Store, wait for it to finish, and retrieve the scraped data. This demonstrates the fundamental call-wait-collect pattern used in every Apify integration.

## Prerequisites

- `npm install apify-client` completed
- `APIFY_TOKEN` environment variable set
- See `apify-install-auth` if not ready

## Authentication

Every call authenticates with a personal API token passed to the client
constructor: `new ApifyClient({ token: process.env.APIFY_TOKEN })`. Keep the
token in the `APIFY_TOKEN` environment variable — never hard-code it in the
script. Full setup (where to generate the token, how to export it) lives in the
`apify-install-auth` skill.

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

This is the whole workflow at a high level: authenticate, `.call()` an Actor,
then read its default dataset. For sync-vs-async execution, pagination,
downloads, key-value store retrieval, run-configuration options, and a table of
popular starter Actors, see [run & retrieval patterns](references/patterns.md).

## Instructions

### Step 1: Create the Script

Use Write (or Edit an existing file) to create `hello-apify.ts` (or `.js`) with
the Core Pattern code above. Use Read to confirm the file contents before running.

### Step 2: Run It

```bash
# With tsx (recommended)
npx tsx hello-apify.ts

# Or with Node.js (plain JS)
node hello-apify.js
```

### Step 3: Understand the Output

The Actor runs on Apify's cloud infrastructure. See the Output section below for
the run-object fields returned when it finishes.

## Output

A successful run returns a run object plus a populated dataset. The fields you
read most:

| Field | Meaning |
|-------|---------|
| `run.id` | Unique run identifier |
| `run.status` | `SUCCEEDED`, `FAILED`, `TIMED-OUT`, or `ABORTED` |
| `run.defaultDatasetId` | ID of the dataset containing scrape results |
| `run.defaultKeyValueStoreId` | ID of the KV store with metadata/artifacts |
| `run.statusMessage` | Human-readable detail (essential when status is not `SUCCEEDED`) |

`client.dataset(run.defaultDatasetId).listItems()` returns `{ items }`, where
each item is one scraped record (shape depends on the Actor). Always branch on
`run.status` before reading the dataset — a `FAILED` run can leave an empty or
partial dataset. See [worked examples](references/examples.md) for the full
run-object breakdown.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Actor not found` | Wrong Actor ID | Check ID at apify.com/store |
| `run.status === 'FAILED'` | Actor crashed | Check `run.statusMessage` for details |
| `run.status === 'TIMED-OUT'` | Exceeded timeout | Increase `timeout` or reduce workload |
| `Dataset is empty` | Actor produced no output | Verify input parameters; check Actor logs |
| `402 Payment Required` | Insufficient compute units — Apify returns HTTP 402 when your account is out of prepaid units | Top up at console.apify.com/billing |

## Examples

Minimal happy-path collection — call an Actor and count the results:

```typescript
const run = await client.actor('apify/website-content-crawler').call({
  startUrls: [{ url: 'https://example.com' }],
  maxCrawlPages: 10,
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(`Scraped ${items.length} pages`);
```

For the complete status-guarded "scrape and save to JSON" script and a full
breakdown of the run object, see [worked examples](references/examples.md).

## Resources

- [Apify Store — Browse Actors](https://apify.com/store)
- [Run Actor via API](https://docs.apify.com/academy/api/run-actor-and-retrieve-data-via-api)
- [JS Client Examples](https://docs.apify.com/api/client/js/docs/guides/examples)
- [Run & retrieval patterns](references/patterns.md) — sync/async, pagination, run config, starter Actors
- [Worked examples](references/examples.md) — full scrape-and-save script

## Next Steps

Once your first Actor run succeeds, proceed to the `apify-local-dev-loop` skill
to build and iterate on your own Actor locally, then deploy it back to the Apify
platform. That skill covers the develop-run-debug cycle in depth.
