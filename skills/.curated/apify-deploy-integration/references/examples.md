# Apify Deploy & Integration — Worked Examples

Three end-to-end scenarios that combine the patterns in
[implementation.md](implementation.md). Each shows the deploy step, the
integration wiring, and the expected result.

## Example 1: Ship an Actor and call it synchronously from a script

Goal: deploy a scraper and get results back in one blocking call — good for CLI
tools, batch jobs, and small request volumes.

```bash
# 1. Deploy the Actor
apify push username/product-scraper
```

```typescript
// 2. Call it and use the typed results (see scrapeProducts in implementation.md)
import { scrapeProducts } from './services/apify';

const products = await scrapeProducts([
  'https://store.example.com/p/1',
  'https://store.example.com/p/2',
]);
console.log(`Got ${products.length} products, first: ${products[0].title}`);
```

Expected: the call blocks until the run reaches `SUCCEEDED`, then resolves to a
typed `ScrapeResult[]`. A non-success status throws with the platform's
`statusMessage`.

## Example 2: Non-blocking scrape behind a Next.js API

Goal: a web app kicks off a long scrape without holding the HTTP request open,
then polls for completion — avoids serverless function timeouts.

```
POST /api/scrape        → { runId, status: "READY", statusUrl: "/api/scrape/<id>" }
GET  /api/scrape/<id>   → { status: "RUNNING" }        (poll)
GET  /api/scrape/<id>   → { status: "SUCCEEDED", items: [...] }
```

Full route handlers are in implementation.md (§ Next.js API Route Integration).
The client polls `statusUrl` every few seconds until `status === 'SUCCEEDED'`.

## Example 3: Scheduled daily pipeline with CSV export + archive

Goal: run unattended on a schedule, export a CSV artifact, and keep a
date-stamped historical copy in a named dataset.

```bash
# Register a webhook so failures page the team, then schedule the run
#   Apify Console → Actor → Webhooks → ACTOR.RUN.FAILED → your Express receiver
```

The `dailyScrapeAndExport` function (implementation.md § Scheduled Pipeline) runs
the Actor, writes `exports/products-<timestamp>.csv`, and appends each item —
tagged with `scrapedDate` — to the `product-archive` dataset. A failed run throws
before export so a downstream cron reports non-zero.
