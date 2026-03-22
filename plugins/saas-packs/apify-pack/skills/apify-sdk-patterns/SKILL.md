---
name: apify-sdk-patterns
description: |
  Production-ready patterns for Apify SDK and apify-client in TypeScript.
  Use when building Actors with Crawlee, managing datasets/KV stores,
  or implementing robust client wrappers with retry and validation.
  Trigger: "apify SDK patterns", "apify best practices",
  "apify client wrapper", "crawlee patterns", "idiomatic apify".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify SDK Patterns

## Overview

Production patterns for both the `apify` SDK (building Actors) and `apify-client` (calling Actors remotely). Covers Crawlee crawler selection, data storage, proxy configuration, and typed client wrappers.

## Prerequisites

- `apify-client` and/or `apify` + `crawlee` installed
- `APIFY_TOKEN` configured
- TypeScript recommended

## Pattern 1: Typed Client Singleton

```typescript
// src/apify/client.ts
import { ApifyClient } from 'apify-client';

let instance: ApifyClient | null = null;

export function getApifyClient(): ApifyClient {
  if (!instance) {
    const token = process.env.APIFY_TOKEN;
    if (!token) throw new Error('APIFY_TOKEN is required');
    instance = new ApifyClient({ token });
  }
  return instance;
}

// Reset for testing
export function resetClient(): void {
  instance = null;
}
```

## Pattern 2: Crawlee Crawler Selection

Choose the right crawler for the job:

```typescript
import { CheerioCrawler, PlaywrightCrawler, PuppeteerCrawler } from 'crawlee';

// CHEERIO — Fast, lightweight, no JavaScript rendering
// Use for: static HTML, server-rendered pages, APIs
const cheerioCrawler = new CheerioCrawler({
  async requestHandler({ request, $, enqueueLinks }) {
    const title = $('title').text();
    await Actor.pushData({ url: request.url, title });
    await enqueueLinks({ strategy: 'same-domain' });
  },
});

// PLAYWRIGHT — Full browser, all engines, modern API
// Use for: SPAs, JavaScript-heavy pages, complex interactions
const playwrightCrawler = new PlaywrightCrawler({
  launchContext: { launchOptions: { headless: true } },
  async requestHandler({ page, request, enqueueLinks }) {
    await page.waitForSelector('h1');
    const title = await page.title();
    const content = await page.$eval('main', el => el.textContent);
    await Actor.pushData({ url: request.url, title, content });
    await enqueueLinks({ strategy: 'same-domain' });
  },
});

// PUPPETEER — Chromium-only browser automation
// Use for: when you need Chromium specifically or legacy Puppeteer code
const puppeteerCrawler = new PuppeteerCrawler({
  async requestHandler({ page, request }) {
    const title = await page.title();
    await Actor.pushData({ url: request.url, title });
  },
});
```

## Pattern 3: Actor Lifecycle with Error Handling

```typescript
import { Actor } from 'apify';
import { CheerioCrawler, log } from 'crawlee';

// Actor.main() wraps init + exit + error handling
await Actor.main(async () => {
  const input = await Actor.getInput<{
    startUrls: { url: string }[];
    maxPages?: number;
    proxyConfig?: { useApifyProxy: boolean; groups?: string[] };
  }>();

  if (!input?.startUrls?.length) {
    throw new Error('Input must include at least one startUrl');
  }

  // Configure proxy if requested
  const proxyConfiguration = input.proxyConfig?.useApifyProxy
    ? await Actor.createProxyConfiguration({
        groups: input.proxyConfig.groups,
      })
    : undefined;

  const crawler = new CheerioCrawler({
    proxyConfiguration,
    maxRequestsPerCrawl: input.maxPages ?? 50,
    maxConcurrency: 10,

    async requestHandler({ request, $, enqueueLinks }) {
      log.info(`Processing ${request.url}`);

      await Actor.pushData({
        url: request.url,
        title: $('title').text().trim(),
        h1: $('h1').first().text().trim(),
        paragraphs: $('p').map((_, el) => $(el).text().trim()).get(),
      });

      await enqueueLinks({ strategy: 'same-domain' });
    },

    async failedRequestHandler({ request }, error) {
      log.error(`Request failed: ${request.url}`, { error: error.message });
      await Actor.pushData({
        url: request.url,
        error: error.message,
        '#isFailed': true,
      });
    },
  });

  await crawler.run(input.startUrls.map(s => s.url));
  log.info(`Crawler finished. ${crawler.stats.state.requestsFinished} pages processed.`);
});
```

## Pattern 4: Dataset Operations

```typescript
import { Actor } from 'apify';
import { ApifyClient } from 'apify-client';

// --- Inside an Actor (apify SDK) ---

// Push single item
await Actor.pushData({ url: 'https://example.com', title: 'Example' });

// Push batch
await Actor.pushData([
  { url: 'https://a.com', price: 10 },
  { url: 'https://b.com', price: 20 },
]);

// Store named output in key-value store
await Actor.setValue('SUMMARY', {
  totalItems: 100,
  avgPrice: 15.50,
  crawledAt: new Date().toISOString(),
});

// Get value back
const summary = await Actor.getValue('SUMMARY');

// --- From external app (apify-client) ---
const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

// List dataset items with pagination
const { items, total } = await client
  .dataset('DATASET_ID')
  .listItems({ limit: 1000, offset: 0 });

// Push items to a named dataset
const dataset = await client.datasets().getOrCreate('my-results');
await client.dataset(dataset.id).pushItems([
  { url: 'https://example.com', data: 'scraped content' },
]);

// Download entire dataset
const csv = await client.dataset(dataset.id).downloadItems('csv');
const json = await client.dataset(dataset.id).downloadItems('json');
```

## Pattern 5: Key-Value Store Operations

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

// Create or get a named store
const store = await client.keyValueStores().getOrCreate('my-config');
const storeClient = client.keyValueStore(store.id);

// Set a record (any content type)
await storeClient.setRecord({
  key: 'CONFIG',
  value: { retries: 3, timeout: 30000 },
  contentType: 'application/json',
});

// Get a record
const record = await storeClient.getRecord('CONFIG');
console.log(record?.value); // { retries: 3, timeout: 30000 }

// Store binary data (screenshots, PDFs)
await storeClient.setRecord({
  key: 'screenshot.png',
  value: screenshotBuffer,
  contentType: 'image/png',
});

// List all keys
const { items: keys } = await storeClient.listKeys();
```

## Pattern 6: Proxy Configuration

```typescript
import { Actor } from 'apify';

// Datacenter proxy (included in subscription, fast)
const dcProxy = await Actor.createProxyConfiguration({
  groups: ['BUYPROXIES94952'],
});

// Residential proxy (pay per GB, high success rate)
const resProxy = await Actor.createProxyConfiguration({
  groups: ['RESIDENTIAL'],
  countryCode: 'US',
});

// Google SERP proxy (specialized for Google)
const serpProxy = await Actor.createProxyConfiguration({
  groups: ['GOOGLE_SERP'],
});

// Use with any crawler
const crawler = new CheerioCrawler({
  proxyConfiguration: dcProxy,
  // ...
});
```

## Pattern 7: Router for Multi-Page Actors

```typescript
import { Actor } from 'apify';
import { CheerioCrawler, createCheerioRouter } from 'crawlee';

const router = createCheerioRouter();

// Default route — listing pages
router.addDefaultHandler(async ({ request, $, enqueueLinks }) => {
  // Extract links to detail pages
  const detailLinks = $('a.product-link')
    .map((_, el) => $(el).attr('href'))
    .get();

  await enqueueLinks({
    urls: detailLinks,
    label: 'DETAIL',
  });
});

// Detail route — individual item pages
router.addHandler('DETAIL', async ({ request, $ }) => {
  await Actor.pushData({
    url: request.url,
    name: $('h1.product-name').text().trim(),
    price: parseFloat($('.price').text().replace('$', '')),
    description: $('div.description').text().trim(),
  });
});

await Actor.main(async () => {
  const crawler = new CheerioCrawler({
    requestHandler: router,
  });
  await crawler.run(['https://example-store.com/products']);
});
```

## Pattern 8: Safe Result Wrapper

```typescript
type Result<T> = { data: T; error: null } | { data: null; error: Error };

async function safeActorCall<T>(
  client: ApifyClient,
  actorId: string,
  input: Record<string, unknown>,
): Promise<Result<T[]>> {
  try {
    const run = await client.actor(actorId).call(input, { timeout: 300 });

    if (run.status !== 'SUCCEEDED') {
      return { data: null, error: new Error(`Run ${run.status}: ${run.statusMessage}`) };
    }

    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    return { data: items as T[], error: null };
  } catch (err) {
    return { data: null, error: err as Error };
  }
}

// Usage
const result = await safeActorCall<{ url: string; title: string }>(
  client, 'apify/web-scraper', { startUrls: [{ url: 'https://example.com' }] }
);

if (result.error) {
  console.error('Actor call failed:', result.error.message);
} else {
  console.log(`Got ${result.data.length} items`);
}
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `Actor.main()` | Actor entry point | Auto init/exit + error reporting |
| `failedRequestHandler` | Per-request failures | Log failures without stopping crawl |
| Safe wrapper | External calls | Prevents uncaught exceptions |
| Router | Multi-page scrapes | Clean separation of page types |
| Proxy rotation | Anti-bot sites | Higher success rate |

## Resources

- [Apify SDK Reference](https://docs.apify.com/sdk/js/reference)
- [Crawlee Documentation](https://crawlee.dev/js/docs/quick-start)
- [Apify JS Client Reference](https://docs.apify.com/api/client/js/reference)
- [Proxy Management Guide](https://docs.apify.com/sdk/js/docs/guides/proxy-management)

## Next Steps

Apply patterns in `apify-core-workflow-a` for a complete web scraping workflow.
