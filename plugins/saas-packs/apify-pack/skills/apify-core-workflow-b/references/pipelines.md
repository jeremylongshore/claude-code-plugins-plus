# Apify Multi-Actor Pipelines & Run Monitoring — Full Reference

Deep companion to `SKILL.md`. Chains Actors together (scrape → transform →
export) and monitors Actor runs for status, cost, and abort control.

## Step 4: Multi-Actor Pipeline

```typescript
// Pipeline: Scrape -> Transform -> Export
async function runPipeline(urls: string[]) {
  const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

  // Stage 1: Scrape raw data
  console.log('Stage 1: Scraping...');
  const scrapeRun = await client.actor('username/product-scraper').call({
    startUrls: urls.map(url => ({ url })),
    maxItems: 1000,
  });
  const { items: rawData } = await client
    .dataset(scrapeRun.defaultDatasetId)
    .listItems();
  console.log(`Scraped ${rawData.length} items`);

  // Stage 2: Transform (using a data-processing Actor)
  console.log('Stage 2: Transforming...');
  const transformRun = await client.actor('username/data-transformer').call({
    datasetId: scrapeRun.defaultDatasetId,
    transformations: {
      dedup: { field: 'sku' },
      filter: { field: 'price', operator: 'gt', value: 0 },
    },
  });

  // Stage 3: Export to named dataset for long-term storage
  console.log('Stage 3: Exporting...');
  const { items: cleanData } = await client
    .dataset(transformRun.defaultDatasetId)
    .listItems();

  const exportDs = await client.datasets().getOrCreate('product-catalog-clean');
  await client.dataset(exportDs.id).pushItems(cleanData);

  console.log(`Pipeline complete. ${cleanData.length} clean items stored.`);
  return exportDs.id;
}
```

## Step 5: Monitor Actor Runs

```typescript
// List recent runs for an Actor
const { items: runs } = await client.actor('username/my-actor').runs().list({
  limit: 10,
  desc: true,
});

runs.forEach(run => {
  console.log(`${run.id} | ${run.status} | ${run.startedAt} | ${run.usageTotalUsd?.toFixed(4)} USD`);
});

// Get detailed run info
const runDetail = await client.run('RUN_ID').get();
console.log({
  status: runDetail.status,
  statusMessage: runDetail.statusMessage,
  datasetItems: runDetail.stats?.datasetItemCount,
  computeUnits: runDetail.usage?.ACTOR_COMPUTE_UNITS,
  durationSecs: runDetail.stats?.runTimeSecs,
});

// Abort a running Actor
await client.run('RUN_ID').abort();
```
