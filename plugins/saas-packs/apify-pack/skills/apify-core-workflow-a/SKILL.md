---
name: apify-core-workflow-a
description: 'Build a complete web scraping Actor with Crawlee and deploy to Apify.

  Use when you need end-to-end web scraping on Apify: defining an input schema,
  building a router-based Crawlee crawler, extracting structured data, storing
  results in a dataset, testing locally, and deploying the Actor to the platform.

  Trigger with "apify scrape website", "build apify actor", "crawlee scraper",
  "apify main workflow".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(apify:*), Grep
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
# Apify Core Workflow A — Build & Deploy a Scraper

## Overview

End-to-end workflow: define input schema, build a Crawlee-based Actor, extract structured data, store results in datasets, test locally, and deploy to Apify platform. This is the primary money-path workflow for Apify.

## Prerequisites

- `npm install apify crawlee` in your project
- `npm install -g apify-cli` and `apify login` completed
- For programmatic retrieval (Step 6), an API token in `APIFY_TOKEN` — read it from
  the environment (`process.env.APIFY_TOKEN`), never hard-code it
- Familiarity with `apify-sdk-patterns`

## Instructions

### Step 1: Define Input Schema

Create `.actor/INPUT_SCHEMA.json`:

```json
{
  "title": "E-Commerce Scraper",
  "type": "object",
  "schemaVersion": 1,
  "properties": {
    "startUrls": {
      "title": "Start URLs",
      "type": "array",
      "description": "Product listing page URLs to scrape",
      "editor": "requestListSources",
      "prefill": [{ "url": "https://example-store.com/products" }]
    },
    "maxItems": {
      "title": "Max items",
      "type": "integer",
      "description": "Maximum number of products to scrape",
      "default": 100,
      "minimum": 1,
      "maximum": 10000
    },
    "proxyConfig": {
      "title": "Proxy configuration",
      "type": "object",
      "description": "Select proxy to use",
      "editor": "proxy",
      "default": { "useApifyProxy": true }
    }
  },
  "required": ["startUrls"]
}
```

### Step 2: Build the Actor with Router Pattern

Use a Crawlee router that splits handling by page type: the default handler
enqueues product links + pagination from listing pages, and a `PRODUCT`-labeled
handler extracts structured fields from detail pages. The entry point wires proxy
config, concurrency, a failed-request handler, and a run summary into the key-value
store. Skeleton:

```typescript
// src/main.ts
import { Actor } from 'apify';
import { CheerioCrawler, createCheerioRouter, Dataset, log } from 'crawlee';

const router = createCheerioRouter();
router.addDefaultHandler(async ({ enqueueLinks }) => {
  await enqueueLinks({ selector: 'a.product-card', label: 'PRODUCT' });
  await enqueueLinks({ selector: 'a.next-page', label: 'LISTING' });
});
router.addHandler('PRODUCT', async ({ request, $ }) => {
  await Actor.pushData({ url: request.url, name: $('h1.product-title').text().trim() });
});

await Actor.main(async () => {
  const input = await Actor.getInput();
  const crawler = new CheerioCrawler({ requestHandler: router, maxRequestsPerCrawl: input?.maxItems ?? 100 });
  await crawler.run(input.startUrls.map(s => s.url));
});
```

The full typed Actor — `Product`/`ProductInput` interfaces, proxy configuration,
`failedRequestHandler`, and the `SUMMARY` key-value write — is in
[implementation.md, Step 2](references/implementation.md).

### Step 3: Configure Dockerfile

Use the `apify/actor-node:20` base with a two-stage build (compile TypeScript in a
`builder` stage, ship only `dist/` + production deps). Full Dockerfile:
[implementation.md, Step 3](references/implementation.md).

### Step 4: Test Locally

```bash
# Create test input
mkdir -p storage/key_value_stores/default
echo '{"startUrls":[{"url":"https://example.com"}],"maxItems":5}' \
  > storage/key_value_stores/default/INPUT.json

# Run locally
apify run

# Check results
ls storage/datasets/default/
cat storage/key_value_stores/default/SUMMARY.json
```

### Step 5: Deploy to Apify Platform

```bash
# Push to Apify (creates Actor if it doesn't exist)
apify push

# Or push to a specific Actor
apify push username/my-actor

# Run on platform
apify actors call username/my-actor
```

### Step 6: Retrieve Results Programmatically

From any client, use the `apify-client` SDK to call the deployed Actor, list its
dataset items, and download results (JSON/CSV). The token comes from
`process.env.APIFY_TOKEN` — never hard-code it. Full retrieval code:
[implementation.md, Step 6](references/implementation.md).

## Output

- Deployable Actor with typed input schema
- Router-based crawler handling listing + detail pages
- Structured product data in default dataset
- Run summary in default key-value store
- Failed requests tracked with error messages

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Actor build failed` | Dockerfile/deps issue | Check build logs on platform |
| Selector returns empty | Page structure changed | Update CSS selectors |
| `maxRequestsPerCrawl` hit | Too many pages enqueued | Increase limit or filter URLs |
| Proxy errors | Anti-bot blocking | Switch to residential proxy |
| `TIMED-OUT` status | Actor exceeded timeout | Increase timeout or reduce scope |

## Examples

A quick example — seed a local input, run the Actor, and check results:

```bash
mkdir -p storage/key_value_stores/default
echo '{"startUrls":[{"url":"https://example-store.com/products"}],"maxItems":5}' \
  > storage/key_value_stores/default/INPUT.json
apify run
cat storage/key_value_stores/default/SUMMARY.json
```

Three fuller worked scenarios live in [examples.md](references/examples.md):

- **Scrape a catalog locally, then deploy** — the full seed → `apify run` →
  inspect → `apify push` loop, with the expected `SUMMARY.json` output.
- **Run the deployed Actor and export CSV** — call the Actor via `apify-client`
  and download the dataset as CSV.
- **Route through residential proxy** — pass a `proxyConfig` group at run time to
  get past anti-bot blocking.

## Resources

- [Crawlee Quick Start](https://crawlee.dev/js/docs/quick-start)
- [Actor Deployment](https://docs.apify.com/platform/actors/development/deployment)
- [Input Schema Spec](https://docs.apify.com/platform/actors/development/actor-definition/input-schema)
- [Full implementation walkthrough](references/implementation.md) — complete Actor source, Dockerfile, and retrieval code
- [Worked examples](references/examples.md) — three end-to-end run scenarios

## Next Steps

Once your Actor is deployed and producing data, move on to dataset and key-value
store management — pagination over large datasets, deduplication, exporting to
external stores, and scheduling recurring runs — covered in `apify-core-workflow-b`.
