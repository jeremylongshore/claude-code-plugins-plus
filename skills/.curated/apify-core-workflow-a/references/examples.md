# Apify Core Workflow A — Worked Examples

Concrete end-to-end runs that chain the workflow steps. Each example assumes the
Actor from [implementation.md](implementation.md) is in place.

## Example 1: Scrape a product catalog locally, then deploy

```bash
# 1. Seed a local test input (5 products, one listing URL)
mkdir -p storage/key_value_stores/default
echo '{"startUrls":[{"url":"https://example-store.com/products"}],"maxItems":5}' \
  > storage/key_value_stores/default/INPUT.json

# 2. Run the Actor locally against that input
apify run

# 3. Inspect the scraped dataset and the run summary
ls storage/datasets/default/
cat storage/key_value_stores/default/SUMMARY.json

# 4. Once results look right, deploy to the platform
apify push
```

Expected `SUMMARY.json` after a clean run:

```json
{
  "itemCount": 5,
  "finishedAt": "2026-07-17T14:12:03.000Z",
  "startUrls": ["https://example-store.com/products"]
}
```

## Example 2: Run the deployed Actor and export results as CSV

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

const run = await client.actor('username/my-actor').call({
  startUrls: [{ url: 'https://target-store.com/products' }],
  maxItems: 500,
});

const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(`Scraped ${items.length} products`);

const csv = await client.dataset(run.defaultDatasetId).downloadItems('csv');
// Persist `csv` to disk or pipe it into a downstream ETL job.
```

## Example 3: Route through Apify residential proxy for anti-bot sites

When a target blocks datacenter IPs, pass a residential proxy group in the run
input — the Actor already reads `proxyConfig` and wires it into the crawler:

```typescript
const run = await client.actor('username/my-actor').call({
  startUrls: [{ url: 'https://protected-store.com/products' }],
  maxItems: 200,
  proxyConfig: { useApifyProxy: true, groups: ['RESIDENTIAL'] },
});
```
