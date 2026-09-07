# Apify Hello World — Worked Examples

Full, runnable examples that extend the lean snippet in SKILL.md. Copy these
verbatim; every one has been kept identical to the original skill body.

## Complete Example: Scrape and Save

Runs a crawl, guards on run status, then writes the dataset to a local JSON
file — the smallest end-to-end script you would actually ship.

```typescript
import { ApifyClient } from 'apify-client';
import { writeFileSync } from 'fs';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

async function scrapeAndSave() {
  console.log('Starting Actor run...');

  const run = await client.actor('apify/website-content-crawler').call({
    startUrls: [{ url: 'https://example.com' }],
    maxCrawlPages: 10,
  });

  if (run.status !== 'SUCCEEDED') {
    throw new Error(`Actor run failed: ${run.status} — ${run.statusMessage}`);
  }

  const { items } = await client.dataset(run.defaultDatasetId).listItems();
  writeFileSync('results.json', JSON.stringify(items, null, 2));
  console.log(`Saved ${items.length} items to results.json`);
}

scrapeAndSave().catch(console.error);
```

## Understanding the Run Object

Every `.call()` / `.start()` returns a run object. The fields you use most:

- `run.id` — unique run identifier
- `run.status` — `SUCCEEDED`, `FAILED`, `TIMED-OUT`, or `ABORTED`
- `run.defaultDatasetId` — ID of the dataset containing results
- `run.defaultKeyValueStoreId` — ID of the KV store with metadata
- `run.statusMessage` — human-readable detail, essential when status is not `SUCCEEDED`

Always branch on `run.status` before reading the dataset — an empty or partial
dataset from a `FAILED` run is a common source of silent bugs.
