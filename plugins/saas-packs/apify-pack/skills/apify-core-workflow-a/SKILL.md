---
name: apify-core-workflow-a
description: |
  Build a complete web scraping Actor with Crawlee and deploy to Apify.
  Use when implementing end-to-end scraping: input schema, crawler,
  data extraction, dataset output, and platform deployment.
  Trigger: "apify scrape website", "build apify actor",
  "crawlee scraper", "apify main workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(apify:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Core Workflow A — Build & Deploy a Scraper

## Overview

End-to-end workflow: define input schema, build a Crawlee-based Actor, extract structured data, store results in datasets, test locally, and deploy to Apify platform. This is the primary money-path workflow for Apify.

## Prerequisites

- `npm install apify crawlee` in your project
- `npm install -g apify-cli` and `apify login` completed
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

```typescript
// src/main.ts
import { Actor } from 'apify';
import { CheerioCrawler, createCheerioRouter, Dataset, log } from 'crawlee';

interface ProductInput {
  startUrls: { url: string }[];
  maxItems?: number;
  proxyConfig?: { useApifyProxy: boolean; groups?: string[] };
}

interface Product {
  url: string;
  name: string;
  price: number | null;
  currency: string;
  description: string;
  imageUrl: string | null;
  inStock: boolean;
  scrapedAt: string;
}

const router = createCheerioRouter();

// LISTING pages — extract product links
router.addDefaultHandler(async ({ request, $, enqueueLinks, log }) => {
  log.info(`Listing page: ${request.url}`);

  await enqueueLinks({
    selector: 'a.product-card',
    label: 'PRODUCT',
  });

  // Handle pagination
  await enqueueLinks({
    selector: 'a.next-page',
    label: 'LISTING',
  });
});

// PRODUCT detail pages — extract structured data
router.addHandler('PRODUCT', async ({ request, $, log }) => {
  log.info(`Product page: ${request.url}`);

  const product: Product = {
    url: request.url,
    name: $('h1.product-title').text().trim(),
    price: parseFloat($('.price').text().replace(/[^0-9.]/g, '')) || null,
    currency: $('.currency').text().trim() || 'USD',
    description: $('div.description').text().trim(),
    imageUrl: $('img.product-image').attr('src') || null,
    inStock: !$('.out-of-stock').length,
    scrapedAt: new Date().toISOString(),
  };

  await Actor.pushData(product);
});

// Entry point
await Actor.main(async () => {
  const input = await Actor.getInput<ProductInput>();
  if (!input?.startUrls?.length) throw new Error('startUrls required');

  const proxyConfiguration = input.proxyConfig?.useApifyProxy
    ? await Actor.createProxyConfiguration({
        groups: input.proxyConfig.groups,
      })
    : undefined;

  const crawler = new CheerioCrawler({
    requestHandler: router,
    proxyConfiguration,
    maxRequestsPerCrawl: input.maxItems ?? 100,
    maxConcurrency: 10,
    requestHandlerTimeoutSecs: 60,

    async failedRequestHandler({ request }, error) {
      log.error(`Failed: ${request.url} — ${error.message}`);
      await Actor.pushData({
        url: request.url,
        error: error.message,
        '#isFailed': true,
      });
    },
  });

  await crawler.run(input.startUrls.map(s => s.url));

  // Save run summary to key-value store
  const dataset = await Dataset.open();
  const info = await dataset.getInfo();
  await Actor.setValue('SUMMARY', {
    itemCount: info?.itemCount ?? 0,
    finishedAt: new Date().toISOString(),
    startUrls: input.startUrls.map(s => s.url),
  });

  log.info(`Done. Scraped ${info?.itemCount ?? 0} products.`);
});
```

### Step 3: Configure Dockerfile

```dockerfile
# .actor/Dockerfile
FROM apify/actor-node:20 AS builder
COPY package*.json ./
RUN npm ci --include=dev --audit=false
COPY . .
RUN npm run build

FROM apify/actor-node:20
COPY package*.json ./
RUN npm ci --omit=dev --audit=false
COPY --from=builder /usr/src/app/dist ./dist
COPY .actor .actor
CMD ["npm", "start"]
```

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

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

// Run the deployed Actor
const run = await client.actor('username/my-actor').call({
  startUrls: [{ url: 'https://target-store.com/products' }],
  maxItems: 500,
});

// Get results
const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(`Scraped ${items.length} products`);

// Download as CSV
const csv = await client.dataset(run.defaultDatasetId).downloadItems('csv');
```

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

## Resources

- [Crawlee Quick Start](https://crawlee.dev/js/docs/quick-start)
- [Actor Deployment](https://docs.apify.com/platform/actors/development/deployment)
- [Input Schema Spec](https://docs.apify.com/platform/actors/development/actor-definition/input-schema)

## Next Steps

For dataset/KV store management, see `apify-core-workflow-b`.
