---
name: apify-reference-architecture
description: |
  Production-grade architecture patterns for Apify-powered applications.
  Use when designing scraping infrastructure, building multi-Actor pipelines,
  or integrating Apify into a larger system architecture.
  Trigger: "apify architecture", "apify best practices",
  "apify project structure", "scraping architecture", "apify system design".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Reference Architecture

## Overview

Production-ready architecture patterns for applications built on Apify. Covers standalone Actor projects, multi-Actor pipelines, and full-stack applications that integrate Apify as a data source.

## Architecture Pattern 1: Standalone Actor

For a single scraper deployed to Apify platform.

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

## Architecture Pattern 2: Multi-Actor Pipeline

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

## Architecture Pattern 3: Full-Stack Integration

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

### Service Layer

```typescript
// src/services/apify-service.ts
import { ApifyClient } from 'apify-client';

export class ApifyService {
  private client: ApifyClient;

  constructor(token: string) {
    this.client = new ApifyClient({ token });
  }

  async startScrape(urls: string[]): Promise<{ runId: string }> {
    const run = await this.client.actor('username/scraper').start({
      startUrls: urls.map(url => ({ url })),
    });
    return { runId: run.id };
  }

  async getRunStatus(runId: string): Promise<{
    status: string;
    progress?: { finished: number; failed: number };
  }> {
    const run = await this.client.run(runId).get();
    return {
      status: run.status,
      progress: {
        finished: run.stats?.requestsFinished ?? 0,
        failed: run.stats?.requestsFailed ?? 0,
      },
    };
  }

  async getResults<T>(runId: string): Promise<T[]> {
    const run = await this.client.run(runId).get();
    if (run.status !== 'SUCCEEDED') {
      throw new Error(`Run not ready: ${run.status}`);
    }
    const { items } = await this.client
      .dataset(run.defaultDatasetId)
      .listItems();
    return items as T[];
  }

  async checkHealth(): Promise<boolean> {
    try {
      const user = await this.client.user().get();
      return !!user.username;
    } catch {
      return false;
    }
  }
}
```

## Configuration Management

```typescript
// src/config/apify.ts
interface ApifyConfig {
  token: string;
  actorId: string;
  defaultMemory: number;
  defaultTimeout: number;
  webhookUrl?: string;
}

export function loadConfig(): ApifyConfig {
  const env = process.env.NODE_ENV || 'development';

  const base: ApifyConfig = {
    token: process.env.APIFY_TOKEN!,
    actorId: process.env.APIFY_ACTOR_ID!,
    defaultMemory: 1024,
    defaultTimeout: 3600,
  };

  const overrides: Record<string, Partial<ApifyConfig>> = {
    development: { defaultMemory: 256, defaultTimeout: 300 },
    staging: { defaultMemory: 512 },
    production: { webhookUrl: process.env.APIFY_WEBHOOK_URL },
  };

  return { ...base, ...overrides[env] };
}
```

## Health Check

```typescript
// src/health.ts
export async function healthCheck(apifyService: ApifyService) {
  const start = Date.now();
  const healthy = await apifyService.checkHealth();

  return {
    service: 'apify',
    status: healthy ? 'healthy' : 'unhealthy',
    latencyMs: Date.now() - start,
    timestamp: new Date().toISOString(),
  };
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Service imports service | Use dependency injection |
| Missing config | Env var not set | Validate at startup with `loadConfig()` |
| Pipeline stage failure | Actor crash mid-pipeline | Add retry logic per stage |
| State management | Tracking run status | Use webhook handler + database |

## Resources

- [Apify Platform Architecture](https://docs.apify.com/platform)
- [API Client Reference](https://docs.apify.com/api/client/js/reference)
- [Actor Development Best Practices](https://docs.apify.com/platform/actors/development)

## Flagship Skills

For multi-environment setup, see `apify-deploy-integration`.
