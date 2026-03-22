---
name: firecrawl-cost-tuning
description: |
  Optimize Firecrawl costs through crawl limits, format selection, caching, and credit monitoring.
  Use when analyzing Firecrawl billing, reducing API costs,
  or implementing credit budget alerts.
  Trigger with phrases like "firecrawl cost", "firecrawl billing",
  "reduce firecrawl costs", "firecrawl pricing", "firecrawl credits", "firecrawl budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, api, monitoring, cost-optimization]

---
# Firecrawl Cost Tuning

## Overview
Firecrawl charges credits per operation: 1 credit per scrape, 1 per crawled page, 1 per map call, and variable credits for extract (LLM usage). An unbounded crawl on a large site can consume thousands of credits in minutes. This skill covers concrete techniques to reduce credit consumption by 50-80%.

## Credit Cost Table

| Operation | Credits | Notes |
|-----------|---------|-------|
| `scrapeUrl` | 1 | Per page, any format |
| `crawlUrl` | 1 per page | Each discovered page costs 1 credit |
| `mapUrl` | 1 | Regardless of URLs returned |
| `batchScrapeUrls` | 1 per URL | Same as individual scrape |
| `extract` | 5+ | LLM processing adds cost |

## Instructions

### Step 1: Always Set Crawl Limits
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// BAD: no limit — could crawl 100K pages
await firecrawl.crawlUrl("https://docs.large-project.org");
// Cost: potentially 100,000+ credits

// GOOD: bounded crawl
await firecrawl.crawlUrl("https://docs.large-project.org", {
  limit: 50,               // max 50 pages
  maxDepth: 2,             // only 2 levels deep
  includePaths: ["/api/*"], // only API docs
  excludePaths: ["/blog/*", "/changelog/*"],
  scrapeOptions: { formats: ["markdown"] },
});
// Cost: max 50 credits
```

### Step 2: Use Scrape for Known URLs Instead of Crawl
```typescript
// If you know which pages you need, don't crawl — scrape them directly
const targetUrls = [
  "https://docs.example.com/api/auth",
  "https://docs.example.com/api/users",
  "https://docs.example.com/api/billing",
];

// Cost: 3 credits (one per page)
const results = await firecrawl.batchScrapeUrls(targetUrls, {
  formats: ["markdown"],
});

// vs crawling the whole docs site: potentially 500+ credits
```

### Step 3: Map First, Then Selective Scrape
```typescript
// Map costs 1 credit and returns up to 30K URLs
const map = await firecrawl.mapUrl("https://docs.example.com");
// Cost: 1 credit

// Filter to only what you need
const apiDocs = (map.links || []).filter(url => url.includes("/api/"));
console.log(`${map.links?.length} total URLs, only ${apiDocs.length} are API docs`);

// Scrape only relevant pages
const results = await firecrawl.batchScrapeUrls(apiDocs.slice(0, 20), {
  formats: ["markdown"],
});
// Cost: 1 (map) + 20 (scrape) = 21 credits
// vs blind crawl: could be 500+ credits
```

### Step 4: Cache to Prevent Re-Scraping
```typescript
import { createHash } from "crypto";

const cache = new Map<string, { content: string; timestamp: number }>();
const CACHE_TTL = 24 * 3600 * 1000; // 24 hours

async function cachedScrape(url: string): Promise<string> {
  const key = createHash("md5").update(url).digest("hex");
  const cached = cache.get(key);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.content; // Free — no API call
  }

  const result = await firecrawl.scrapeUrl(url, { formats: ["markdown"] });
  if (result.markdown) {
    cache.set(key, { content: result.markdown, timestamp: Date.now() });
  }
  return result.markdown || "";
}
// Typical savings: 50-80% credit reduction for recurring scrapes
```

### Step 5: Monitor Credit Consumption
```bash
set -euo pipefail
# Check current credit balance
curl -s https://api.firecrawl.dev/v1/team/credits \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" | jq .
```

```typescript
// Daily credit tracker
class CreditBudget {
  private dailyLimit: number;
  private usage = new Map<string, number>();

  constructor(dailyLimit = 1000) {
    this.dailyLimit = dailyLimit;
  }

  canAfford(estimatedCredits: number): boolean {
    const today = new Date().toISOString().split("T")[0];
    const used = this.usage.get(today) || 0;
    return used + estimatedCredits <= this.dailyLimit;
  }

  record(credits: number) {
    const today = new Date().toISOString().split("T")[0];
    this.usage.set(today, (this.usage.get(today) || 0) + credits);
  }

  remaining(): number {
    const today = new Date().toISOString().split("T")[0];
    return this.dailyLimit - (this.usage.get(today) || 0);
  }
}

const budget = new CreditBudget(1000);

// Before each crawl
if (!budget.canAfford(50)) {
  throw new Error(`Daily credit budget exceeded. ${budget.remaining()} credits left`);
}
await firecrawl.crawlUrl(url, { limit: 50 });
budget.record(50);
```

### Step 6: Choose Minimal Formats
```bash
set -euo pipefail
# Cheapest: markdown only (1 credit, fastest)
curl -X POST https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}'

# Avoid requesting screenshots, rawHtml, or extract unless needed
# Extract uses LLM calls — significantly more credits
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `402 Payment Required` | Credits exhausted | Check balance, upgrade plan, or wait for reset |
| Credits drained by one crawl | No `limit` set | Always set `limit` and `maxDepth` |
| Duplicate scraping costs | Same URLs scraped daily | Implement URL-keyed caching |
| High per-page cost | Requesting all formats + extract | Use `formats: ["markdown"]` only |
| Budget overrun | No daily cap | Implement credit budget tracker |

## Cost Optimization Summary

| Technique | Credit Savings |
|-----------|---------------|
| Set crawl `limit` | Prevents 100x overages |
| Map + selective scrape | 50-90% vs blind crawl |
| Cache repeated scrapes | 50-80% reduction |
| Markdown-only format | Fastest, no extras |
| Batch scrape vs individual | Same cost, less overhead |

## Resources
- [Firecrawl Pricing](https://firecrawl.dev/pricing)
- [Firecrawl Dashboard](https://firecrawl.dev/app)
- [Rate Limits](https://docs.firecrawl.dev/rate-limits)

## Next Steps
For reference architecture, see `firecrawl-reference-architecture`.
