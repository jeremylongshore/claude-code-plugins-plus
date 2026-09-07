# Apify Core Workflow A — Full Implementation Walkthrough

This reference holds the complete, copy-ready code for each step of the
build-and-deploy workflow. `SKILL.md` carries the lean skeleton and the
high-level sequence; drill in here for the full Actor source, the Dockerfile,
and the programmatic result-retrieval code.

## Step 2: Build the Actor with Router Pattern

The router pattern separates listing-page handling (enqueue product links +
pagination) from product-detail handling (extract structured fields). This keeps
each handler small and testable, and lets Crawlee route requests by `label`.

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

## Step 3: Configure Dockerfile

A two-stage build compiles TypeScript in the `builder` stage, then copies only
the built `dist/` into a lean runtime image with production-only dependencies.

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

## Step 6: Retrieve Results Programmatically

After deployment, call the Actor and pull its dataset from any client using the
`apify-client` SDK. The token comes from `process.env.APIFY_TOKEN` (never
hard-code it).

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
