# Apify Run & Retrieval Patterns

Deeper reference for the call-wait-collect workflow: sync vs async execution,
dataset/key-value retrieval, and run configuration. Read this after the
`## Core Pattern` in SKILL.md when you need more than the happy path.

## Synchronous vs Asynchronous Runs

```typescript
// SYNCHRONOUS — .call() waits for the Actor to finish (simple, blocking)
const run = await client.actor('apify/web-scraper').call(input);

// ASYNCHRONOUS — .start() returns immediately, poll later
const run = await client.actor('apify/web-scraper').start(input);
// ... do other work ...
const finishedRun = await client.run(run.id).waitForFinish();
```

Use `.call()` for short scrapes and scripts where blocking is fine. Use
`.start()` + `.waitForFinish()` when you want to kick off a long run and do
other work (or track progress) before collecting results.

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

Datasets hold the structured scrape output; the key-value store holds named
artifacts (screenshots, HTML snapshots, run metadata). `listItems()` paginates
internally, so it is safe on large datasets; use `limit`/`offset` when you want
explicit control.

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

More memory generally means faster runs but higher compute-unit cost. `timeout`
caps total Actor runtime; `waitSecs` caps how long `.call()` blocks the client
(set `0` to fire-and-forget and poll later, as in the async pattern above).

## Popular Starter Actors

| Actor ID | Purpose | Typical Input |
|----------|---------|---------------|
| `apify/website-content-crawler` | Crawl and extract text | `{ startUrls, maxCrawlPages }` |
| `apify/web-scraper` | General-purpose scraper | `{ startUrls, pageFunction }` |
| `apify/cheerio-scraper` | Fast HTML scraper | `{ startUrls, pageFunction }` |
| `apify/google-search-scraper` | Google SERP results | `{ queries, maxPagesPerQuery }` |

Browse the full catalog at [apify.com/store](https://apify.com/store). Each
Actor's page documents its exact input schema.
