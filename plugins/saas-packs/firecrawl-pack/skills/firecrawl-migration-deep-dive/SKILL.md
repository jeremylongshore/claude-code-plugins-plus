---
name: firecrawl-migration-deep-dive
description: |
  Migrate to Firecrawl from Puppeteer, Playwright, Cheerio, or other scraping tools.
  Use when replacing custom scraping code with Firecrawl, migrating between
  scraping APIs, or re-platforming content ingestion pipelines.
  Trigger with phrases like "migrate to firecrawl", "replace puppeteer with firecrawl",
  "switch to firecrawl", "firecrawl vs puppeteer", "firecrawl migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, migration]

---
# Firecrawl Migration Deep Dive

## Current State
!`npm list puppeteer playwright cheerio 2>/dev/null | grep -E "puppeteer|playwright|cheerio" || echo 'No scraping libs found'`

## Overview
Migrate from custom scraping (Puppeteer, Playwright, Cheerio) or competing APIs to Firecrawl. Firecrawl eliminates browser management, anti-bot handling, and JS rendering infrastructure. This skill shows equivalent code for common scraping patterns.

## Migration Comparison

| Feature | Puppeteer/Playwright | Cheerio | Firecrawl |
|---------|---------------------|---------|-----------|
| JS rendering | Manual browser | No | Automatic |
| Anti-bot bypass | DIY (stealth plugin) | No | Built-in |
| Output format | Raw HTML | Parsed HTML | Markdown/JSON/HTML |
| Infrastructure | Browser instances | None | API call |
| Concurrent scraping | Manage browser pool | Simple | Managed by Firecrawl |
| Cost model | Compute (CPU/RAM) | Free | Credits per page |

## Instructions

### Step 1: Replace Puppeteer Single-Page Scrape

```typescript
// BEFORE: Puppeteer (20+ lines, browser management)
import puppeteer from "puppeteer";

async function scrapePuppeteer(url: string) {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: "networkidle2" });
  const html = await page.content();
  const title = await page.title();
  await browser.close();
  return { html, title };
}

// AFTER: Firecrawl (5 lines, no browser needed)
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY! });

async function scrapeFirecrawl(url: string) {
  const result = await firecrawl.scrapeUrl(url, {
    formats: ["markdown"],
    onlyMainContent: true,
    waitFor: 2000,
  });
  return { markdown: result.markdown, title: result.metadata?.title };
}
```

### Step 2: Replace Cheerio HTML Parsing

```typescript
// BEFORE: fetch + cheerio (manual parsing)
import * as cheerio from "cheerio";

async function scrapeCheerio(url: string) {
  const html = await fetch(url).then(r => r.text());
  const $ = cheerio.load(html);
  return {
    title: $("h1").first().text(),
    content: $("main").text(),
    links: $("a").map((_, el) => $(el).attr("href")).get(),
  };
}

// AFTER: Firecrawl with extract (LLM-powered, no CSS selectors)
async function extractFirecrawl(url: string) {
  const result = await firecrawl.scrapeUrl(url, {
    formats: ["extract", "links"],
    extract: {
      schema: {
        type: "object",
        properties: {
          title: { type: "string" },
          content: { type: "string" },
        },
      },
    },
  });
  return {
    title: result.extract?.title,
    content: result.extract?.content,
    links: result.links,
  };
}
```

### Step 3: Replace Crawl Pipeline

```typescript
// BEFORE: Playwright crawler (100+ lines, queue, browser pool)
// - launch browser pool
// - manage visited URLs set
// - extract links, enqueue
// - handle errors per page
// - close browsers on exit

// AFTER: Firecrawl crawl (10 lines)
async function crawlSite(baseUrl: string) {
  const result = await firecrawl.crawlUrl(baseUrl, {
    limit: 100,
    maxDepth: 3,
    includePaths: ["/docs/*", "/api/*"],
    excludePaths: ["/blog/*"],
    scrapeOptions: {
      formats: ["markdown"],
      onlyMainContent: true,
    },
  });

  return result.data?.map(page => ({
    url: page.metadata?.sourceURL,
    title: page.metadata?.title,
    content: page.markdown,
  }));
}
```

### Step 4: Gradual Migration with Adapter Pattern

```typescript
// Adapter interface for gradual migration
interface ScrapeAdapter {
  scrape(url: string): Promise<{ title: string; content: string }>;
  crawl(url: string, maxPages: number): Promise<Array<{ url: string; content: string }>>;
}

class FirecrawlAdapter implements ScrapeAdapter {
  private client: FirecrawlApp;

  constructor() {
    this.client = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY! });
  }

  async scrape(url: string) {
    const result = await this.client.scrapeUrl(url, {
      formats: ["markdown"],
      onlyMainContent: true,
    });
    return {
      title: result.metadata?.title || "",
      content: result.markdown || "",
    };
  }

  async crawl(url: string, maxPages: number) {
    const result = await this.client.crawlUrl(url, {
      limit: maxPages,
      scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
    });
    return (result.data || []).map(page => ({
      url: page.metadata?.sourceURL || url,
      content: page.markdown || "",
    }));
  }
}

// Feature flag controlled migration
function getScrapeAdapter(): ScrapeAdapter {
  if (process.env.USE_FIRECRAWL === "true") {
    return new FirecrawlAdapter();
  }
  return new LegacyPuppeteerAdapter();
}
```

### Step 5: Remove Old Dependencies
```bash
set -euo pipefail
# After migration is complete and verified
npm uninstall puppeteer puppeteer-core
npm uninstall playwright @playwright/test
npm uninstall cheerio

# Remove browser downloads
npx playwright uninstall --all 2>/dev/null || true

# Verify no lingering references
grep -r "puppeteer\|playwright\|cheerio" src/ --include="*.ts" || echo "Clean!"
```

## Migration Checklist
- [ ] Install `@mendable/firecrawl-js`
- [ ] Create adapter layer wrapping Firecrawl
- [ ] Replace single-page scrapes with `scrapeUrl`
- [ ] Replace crawl loops with `crawlUrl`
- [ ] Replace HTML parsing with `extract` or markdown
- [ ] Feature flag to switch between old and new
- [ ] Run both in parallel, compare outputs
- [ ] Remove old scraping dependencies
- [ ] Delete browser management code

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Different output format | Puppeteer returns HTML, Firecrawl markdown | Adjust downstream consumers |
| Missing CSS selector data | Firecrawl doesn't use selectors | Use `extract` with JSON schema |
| Higher latency for single pages | API call vs local browser | Acceptable trade-off for zero infra |
| Content differences | Different JS wait timing | Tune `waitFor` parameter |

## Resources
- [Firecrawl vs Puppeteer](https://docs.firecrawl.dev/introduction)
- [Firecrawl Scrape Options](https://docs.firecrawl.dev/features/scrape)
- [Advanced Scraping Guide](https://docs.firecrawl.dev/advanced-scraping-guide)

## Next Steps
For advanced troubleshooting, see `firecrawl-advanced-troubleshooting`.
