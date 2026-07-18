# Apify Architecture Patterns — Full Reference

Three production-ready patterns for applications built on Apify, from a single scraper to a full-stack integration. Pick the pattern that matches your scope, then copy the directory layout and skeleton code below.

## Pattern 1: Standalone Actor

For a single scraper deployed to the Apify platform.

```
my-scraper/
├── .actor/
│   ├── actor.json           # Actor metadata
│   ├── INPUT_SCHEMA.json    # Input definition (generates UI)
│   └── Dockerfile           # Build configuration
├── src/
│   ├── main.ts              # Entry point (Actor.main)
│   ├── routes/
│   │   ├── listing.ts       # Router handler: listing pages
│   │   └── detail.ts        # Router handler: detail pages
│   ├── types.ts             # Input/output TypeScript types
│   └── utils/
│       ├── extractors.ts    # Data extraction functions
│       └── validators.ts    # Input/output validation
├── tests/
│   ├── extractors.test.ts   # Unit tests for extraction logic
│   └── integration.test.ts  # Integration tests (live API)
├── storage/                  # Local storage (git-ignored)
├── package.json
├── tsconfig.json
└── .gitignore
```

### Key Files

```typescript
// src/main.ts — Actor entry point
import { Actor } from 'apify';
import { CheerioCrawler } from 'crawlee';
import { router } from './routes/listing';
import { validateInput, ScraperInput } from './types';

await Actor.main(async () => {
  const rawInput = await Actor.getInput<ScraperInput>();
  const input = validateInput(rawInput);

  const proxyConfiguration = input.proxyConfig?.useApifyProxy
    ? await Actor.createProxyConfiguration({ groups: input.proxyConfig.groups })
    : undefined;

  const crawler = new CheerioCrawler({
    requestHandler: router,
    proxyConfiguration,
    maxRequestsPerCrawl: input.maxItems ?? 100,
    maxConcurrency: input.concurrency ?? 10,
  });

  await crawler.run(input.startUrls.map(s => s.url));
});
```

```typescript
// src/types.ts — Shared types and validation
import { z } from 'zod';

export const InputSchema = z.object({
  startUrls: z.array(z.object({ url: z.string().url() })).min(1),
  maxItems: z.number().int().positive().optional().default(100),
  concurrency: z.number().int().min(1).max(50).optional().default(10),
  proxyConfig: z.object({
    useApifyProxy: z.boolean(),
    groups: z.array(z.string()).optional(),
  }).optional(),
});

export type ScraperInput = z.infer<typeof InputSchema>;

export function validateInput(raw: unknown): ScraperInput {
  return InputSchema.parse(raw);
}

export interface ProductOutput {
  url: string;
  name: string;
  price: number | null;
  currency: string;
  inStock: boolean;
  scrapedAt: string;
}
```

## Pattern 2: Multi-Actor Pipeline

For complex scraping workflows with multiple stages.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Discover    │────▶│  Scrape      │────▶│  Transform   │
│  Actor       │     │  Actor       │     │  Actor       │
│              │     │              │     │              │
│ Finds URLs   │     │ Extracts     │     │ Dedup,       │
│ to scrape    │     │ raw data     │     │ clean,       │
│              │     │              │     │ enrich       │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
  Request Queue         Dataset A            Dataset B
  (URLs to scrape)      (raw data)          (clean data)
```

### Pipeline Orchestrator

```typescript
// pipeline/orchestrator.ts
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

interface PipelineConfig {
  discoverActorId: string;
  scrapeActorId: string;
  transformActorId: string;
  seedUrls: string[];
  maxItems: number;
}

async function runPipeline(config: PipelineConfig) {
  const results = {
    discover: { runId: '', items: 0, cost: 0 },
    scrape: { runId: '', items: 0, cost: 0 },
    transform: { runId: '', items: 0, cost: 0 },
  };

  // Stage 1: Discover URLs
  console.log('Stage 1: Discovering URLs...');
  const discoverRun = await client.actor(config.discoverActorId).call({
    seedUrls: config.seedUrls,
    maxPages: 50,
  });
  const { items: urls } = await client
    .dataset(discoverRun.defaultDatasetId)
    .listItems();
  results.discover = {
    runId: discoverRun.id,
    items: urls.length,
    cost: discoverRun.usageTotalUsd ?? 0,
  };

  // Stage 2: Scrape each discovered URL
  console.log(`Stage 2: Scraping ${urls.length} URLs...`);
  const scrapeRun = await client.actor(config.scrapeActorId).call({
    startUrls: urls.map((u: any) => ({ url: u.url })),
    maxItems: config.maxItems,
  });
  results.scrape = {
    runId: scrapeRun.id,
    items: scrapeRun.stats?.datasetItemCount ?? 0,
    cost: scrapeRun.usageTotalUsd ?? 0,
  };

  // Stage 3: Transform and deduplicate
  console.log('Stage 3: Transforming...');
  const transformRun = await client.actor(config.transformActorId).call({
    sourceDatasetId: scrapeRun.defaultDatasetId,
    dedupField: 'url',
    filterEmpty: true,
  });
  results.transform = {
    runId: transformRun.id,
    items: transformRun.stats?.datasetItemCount ?? 0,
    cost: transformRun.usageTotalUsd ?? 0,
  };

  // Store final results in named dataset
  const finalDs = await client.datasets().getOrCreate('pipeline-output');
  const { items: cleanData } = await client
    .dataset(transformRun.defaultDatasetId)
    .listItems();
  await client.dataset(finalDs.id).pushItems(cleanData);

  // Summary
  const totalCost = Object.values(results).reduce((s, r) => s + r.cost, 0);
  console.log('\n=== Pipeline Summary ===');
  console.log(`Discovered: ${results.discover.items} URLs`);
  console.log(`Scraped:    ${results.scrape.items} items`);
  console.log(`Clean:      ${results.transform.items} items`);
  console.log(`Total cost: $${totalCost.toFixed(4)}`);

  return results;
}
```

## Pattern 3: Full-Stack Integration

Application that uses Apify as a data source.

```
┌─────────────────────────────────────────────────────────┐
│                    Your Application                      │
│                                                          │
│  ┌─────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │ Frontend │──▶│ API Server   │──▶│ Apify Service    │  │
│  │ (React)  │   │ (Express/    │   │ (apify-client)   │  │
│  │          │◀──│  Next.js)    │◀──│                  │  │
│  └─────────┘   └──────┬───────┘   └────────┬─────────┘  │
│                       │                     │             │
│                       ▼                     ▼             │
│                 ┌──────────┐         ┌────────────┐      │
│                 │ Your DB  │         │ Apify      │      │
│                 │ (results)│         │ Platform   │      │
│                 └──────────┘         └────────────┘      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Webhook Handler                                   │   │
│  │ Receives run completion → saves results to DB     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

The service-layer, configuration, and health-check code for this pattern lives in
[implementation.md](implementation.md).
