# Major Migration: Apify SDK v2 to v3 (Crawlee Split)

This is the most common migration. In v3, crawling code moved to `crawlee`.

## Import Changes

```typescript
// ---- BEFORE (SDK v2) ----
import Apify from 'apify';
const { CheerioCrawler, PlaywrightCrawler, log } = Apify;

// ---- AFTER (SDK v3 + Crawlee) ----
import { Actor } from 'apify';
import { CheerioCrawler, PlaywrightCrawler, log } from 'crawlee';
```

## Initialization Changes

```typescript
// ---- BEFORE (v2) ----
Apify.main(async () => {
  const input = await Apify.getInput();
  const dataset = await Apify.openDataset();
  await Apify.pushData({ url: 'https://example.com' });
  await Apify.setValue('OUTPUT', { done: true });
});

// ---- AFTER (v3) ----
await Actor.main(async () => {
  const input = await Actor.getInput();
  const dataset = await Actor.openDataset();
  await Actor.pushData({ url: 'https://example.com' });
  await Actor.setValue('OUTPUT', { done: true });
});
```

## Crawler Configuration Changes

```typescript
// ---- BEFORE (v2) ----
const crawler = new Apify.CheerioCrawler({
  handlePageFunction: async ({ request, $ }) => {
    // ...
  },
  handleFailedRequestFunction: async ({ request }) => {
    // ...
  },
});

// ---- AFTER (v3 / Crawlee) ----
const crawler = new CheerioCrawler({
  requestHandler: async ({ request, $ }) => {
    // renamed from handlePageFunction
  },
  failedRequestHandler: async ({ request }, error) => {
    // renamed from handleFailedRequestFunction
    // error is now second argument
  },
});
```

## Proxy Configuration Changes

```typescript
// ---- BEFORE (v2) ----
const proxyConfiguration = await Apify.createProxyConfiguration({
  groups: ['RESIDENTIAL'],
});

// ---- AFTER (v3) ----
const proxyConfiguration = await Actor.createProxyConfiguration({
  groups: ['RESIDENTIAL'],
});
```

## Request Queue Changes

```typescript
// ---- BEFORE (v2) ----
const requestQueue = await Apify.openRequestQueue();
await requestQueue.addRequest({ url: 'https://example.com' });

// ---- AFTER (v3) ----
// Option A: Use enqueueLinks in crawler (preferred)
await enqueueLinks({ strategy: 'same-domain' });

// Option B: Open queue directly
const requestQueue = await Actor.openRequestQueue();
await requestQueue.addRequest({ url: 'https://example.com' });
```

## Router Pattern (New in v3)

```typescript
// v3 introduced explicit routers (replaces label-based if/else)
import { createCheerioRouter } from 'crawlee';

const router = createCheerioRouter();

router.addDefaultHandler(async ({ request, $, enqueueLinks }) => {
  // Handle listing pages
  await enqueueLinks({ selector: 'a.detail', label: 'DETAIL' });
});

router.addHandler('DETAIL', async ({ request, $ }) => {
  // Handle detail pages
  await Actor.pushData({ url: request.url, title: $('h1').text() });
});

const crawler = new CheerioCrawler({ requestHandler: router });
```

## apify-client Upgrade Notes

The `apify-client` package has been more stable. Key changes across versions:

```typescript
// v1.x → v2.x: Constructor changed
// Before
const { ApifyClient } = require('apify-client');
const client = new ApifyClient({ userId: 'xxx', token: 'yyy' });

// After (v2+): userId removed, just token
const client = new ApifyClient({ token: 'yyy' });

// Method chaining style (consistent since v2)
const run = await client.actor('username/actor').call(input);
const { items } = await client.dataset(run.defaultDatasetId).listItems();
```
