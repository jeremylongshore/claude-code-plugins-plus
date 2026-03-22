---
name: brightdata-reference-architecture
description: |
  Implement Bright Data reference architecture with best-practice project layout.
  Use when designing new Bright Data integrations, reviewing project structure,
  or establishing architecture standards for Bright Data applications.
  Trigger with phrases like "brightdata architecture", "brightdata best practices",
  "brightdata project structure", "how to organize brightdata", "brightdata layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Reference Architecture

## Overview

Production-ready architecture for Bright Data scraping systems. Covers project layout, data pipeline design, and integration patterns for Web Unlocker, Scraping Browser, SERP API, and Datasets API.

## Prerequisites

- Understanding of layered architecture
- Node.js/TypeScript project setup
- Database for storing scraped data

## Project Structure

```
my-scraper/
├── src/
│   ├── brightdata/
│   │   ├── proxy.ts            # Proxy config helper (zone, country, session)
│   │   ├── client.ts           # Axios client with proxy + retry
│   │   ├── browser.ts          # Scraping Browser connection manager
│   │   ├── api.ts              # REST API client (trigger, snapshot)
│   │   ├── cache.ts            # Response cache (LRU + optional Redis)
│   │   └── types.ts            # Shared TypeScript interfaces
│   ├── scrapers/
│   │   ├── product-scraper.ts  # Domain-specific scraper
│   │   ├── serp-scraper.ts     # Search result collector
│   │   └── parser.ts           # HTML → structured data (cheerio)
│   ├── pipeline/
│   │   ├── scheduler.ts        # Cron-based scraping scheduler
│   │   ├── processor.ts        # Raw HTML → clean data
│   │   └── storage.ts          # Database/file output
│   ├── webhooks/
│   │   └── brightdata.ts       # Webhook delivery handler
│   └── api/
│       ├── health.ts           # Health check endpoint
│       └── scrape.ts           # On-demand scrape endpoint
├── tests/
│   ├── unit/                   # Mocked tests (no proxy needed)
│   ├── integration/            # Live proxy tests
│   └── fixtures/               # Cached HTML for testing
├── config/
│   ├── zones.json              # Zone configuration per environment
│   └── targets.json            # Target URLs and scraping schedules
└── .env.example
```

## Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│                    API / Scheduler                     │
│         (On-demand scrape, cron jobs, webhooks)        │
├──────────────────────────────────────────────────────┤
│                   Scraper Layer                        │
│    (Product scraper, SERP scraper, custom parsers)     │
├────────────┬─────────────────┬───────────────────────┤
│ Web        │  Scraping       │  SERP / Datasets      │
│ Unlocker   │  Browser        │  API                  │
│ (Proxy)    │  (WebSocket)    │  (REST)               │
├────────────┴─────────────────┴───────────────────────┤
│          Bright Data Infrastructure Layer              │
│  (Proxy config, retry, cache, session management)      │
├──────────────────────────────────────────────────────┤
│              Storage / Pipeline                        │
│    (Database, file output, webhook delivery)           │
└──────────────────────────────────────────────────────┘
```

## Key Components

### Step 1: Multi-Product Client

```typescript
// src/brightdata/client.ts
import axios, { AxiosInstance } from 'axios';
import https from 'https';
import { chromium } from 'playwright';

export class BrightDataClient {
  private proxyClient: AxiosInstance;
  private apiToken: string;

  constructor(private config: {
    customerId: string;
    zone: string;
    zonePassword: string;
    apiToken: string;
  }) {
    this.apiToken = config.apiToken;
    this.proxyClient = axios.create({
      proxy: {
        host: 'brd.superproxy.io',
        port: 33335,
        auth: {
          username: `brd-customer-${config.customerId}-zone-${config.zone}`,
          password: config.zonePassword,
        },
      },
      httpsAgent: new https.Agent({ keepAlive: true, rejectUnauthorized: false }),
      timeout: 60000,
    });
  }

  // Web Unlocker — simple HTTP through proxy
  async scrape(url: string, country?: string): Promise<string> {
    const response = await this.proxyClient.get(url);
    return response.data;
  }

  // Scraping Browser — Playwright over CDP
  async scrapeWithBrowser(url: string, extract: (page: any) => Promise<any>) {
    const auth = `brd-customer-${this.config.customerId}-zone-scraping_browser1:${this.config.zonePassword}`;
    const browser = await chromium.connectOverCDP(`wss://${auth}@brd.superproxy.io:9222`);
    try {
      const page = await browser.newPage();
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      return await extract(page);
    } finally {
      await browser.close();
    }
  }

  // Web Scraper API — async bulk collection
  async triggerCollection(datasetId: string, inputs: any[]) {
    const response = await fetch(
      `https://api.brightdata.com/datasets/v3/trigger?dataset_id=${datasetId}&format=json`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${this.apiToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(inputs),
      }
    );
    return response.json();
  }
}
```

### Step 2: Scraping Pipeline

```typescript
// src/pipeline/scheduler.ts
import cron from 'node-cron';

interface ScrapeJob {
  name: string;
  urls: string[];
  product: 'web_unlocker' | 'scraping_browser' | 'datasets_api';
  schedule: string; // cron expression
  parser: (html: string) => any;
}

export function startScheduler(jobs: ScrapeJob[], client: BrightDataClient) {
  for (const job of jobs) {
    cron.schedule(job.schedule, async () => {
      console.log(`Running job: ${job.name}`);
      if (job.product === 'datasets_api') {
        await client.triggerCollection('dataset_id', job.urls.map(url => ({ url })));
      } else {
        for (const url of job.urls) {
          const html = await client.scrape(url);
          const data = job.parser(html);
          await saveToDatabase(job.name, data);
        }
      }
    });
  }
}
```

### Step 3: Environment Configuration

```json
// config/zones.json
{
  "development": {
    "web_unlocker": "web_unlocker_dev",
    "scraping_browser": "scraping_browser_dev",
    "api_datasets": true
  },
  "production": {
    "web_unlocker": "web_unlocker_prod",
    "scraping_browser": "scraping_browser_prod",
    "api_datasets": true
  }
}
```

## Decision Matrix

| Scenario | Product | Why |
|----------|---------|-----|
| Simple HTML pages | Web Unlocker | Cheapest, fastest |
| JavaScript SPA | Scraping Browser | Needs browser rendering |
| Search results | SERP API | Pre-parsed JSON output |
| 1000+ URLs one-time | Web Scraper API | Async, handles parallelism |
| Amazon/LinkedIn/etc. | Pre-built Datasets | No code needed |
| Login-required pages | Scraping Browser + sticky session | Session persistence |

## Output

- Multi-product Bright Data client
- Domain-specific scrapers with parsers
- Cron-based scraping pipeline
- Environment-isolated zone configuration

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Mixed product confusion | Wrong zone for task | Use decision matrix above |
| Circular dependencies | Tight coupling | Keep scraper layer separate from proxy layer |
| Test pollution | Shared mocks | Use dependency injection |
| Config mismatch | Wrong environment | Load zone config from `zones.json` |

## Resources

- [Bright Data Products Overview](https://brightdata.com/products)
- [Scraping Browser](https://docs.brightdata.com/scraping-automation/scraping-browser/overview)
- [Web Scraper API](https://docs.brightdata.com/scraping-automation/web-data-apis/web-scraper-api/overview)
- [SERP API](https://docs.brightdata.com/scraping-automation/serp-api/overview)

## Next Steps

For multi-environment setup, see `brightdata-deploy-integration`.
