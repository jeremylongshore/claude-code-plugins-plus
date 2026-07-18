# Apify Storage Operations — Full Reference

Complete, copy-ready code for Apify's three storage types: datasets, key-value
stores, and request queues. Each section is the deep companion to the lean
skeleton in `SKILL.md`.

## Step 1: Dataset Operations

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

## Step 2: Key-Value Store Operations

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

## Step 3: Request Queue Management

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

## Data Flow Diagram

```
Actor Run
  ├── Default Dataset      ← Actor.pushData() writes here
  ├── Default KV Store     ← Actor.setValue() writes here
  │     ├── INPUT          ← Input passed at run start
  │     └── OUTPUT         ← Convention for main output
  └── Default Request Queue ← Crawlee manages this
```
