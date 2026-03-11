---
name: firecrawl-reliability-patterns
description: |
  Implement FireCrawl reliability patterns including circuit breakers, idempotency, and graceful degradation.
  Use when building fault-tolerant FireCrawl integrations, implementing retry strategies,
  or adding resilience to production FireCrawl services.
  Trigger with phrases like "firecrawl reliability", "firecrawl circuit breaker",
  "firecrawl idempotent", "firecrawl resilience", "firecrawl fallback", "firecrawl bulkhead".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Firecrawl Reliability Patterns

## Overview
Production reliability patterns for Firecrawl web scraping pipelines. Firecrawl's async crawl model, JavaScript rendering, and credit-based pricing create specific reliability challenges around job completion, content quality, and cost control.

## Prerequisites
- Firecrawl API key configured
- Understanding of async job polling
- Queue infrastructure for retry handling

## Instructions

### Step 1: Robust Crawl Job Polling

Crawl jobs can take minutes. Implement proper polling with timeout and failure detection.

```typescript
import FirecrawlApp from '@mendable/firecrawl-js';

async function reliableCrawl(url: string, options: any, timeoutMs = 600000) {
  const firecrawl = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY });
  const crawl = await firecrawl.asyncCrawlUrl(url, options);
  const deadline = Date.now() + timeoutMs;
  let pollInterval = 2000;

  while (Date.now() < deadline) {
    const status = await firecrawl.checkCrawlStatus(crawl.id);
    if (status.status === 'completed') return status;
    if (status.status === 'failed') throw new Error(`Crawl failed: ${status.error}`);

    await new Promise(r => setTimeout(r, pollInterval));
    pollInterval = Math.min(pollInterval * 1.5, 30000);  // back off
  }
  throw new Error(`Crawl timed out after ${timeoutMs}ms`);
}
```

### Step 2: Content Quality Validation

Scraped pages may return empty or boilerplate content. Validate before processing.

```typescript
interface ScrapedPage {
  url: string;
  markdown: string;
  metadata: { title?: string; statusCode?: number };
}

function validateContent(page: ScrapedPage): boolean {
  if (!page.markdown || page.markdown.length < 100) return false;
  if (page.metadata.statusCode && page.metadata.statusCode >= 400) return false;
  // Detect common error pages
  const errorPatterns = ['access denied', '403 forbidden', 'page not found', 'captcha'];
  const lower = page.markdown.toLowerCase();
  return !errorPatterns.some(p => lower.includes(p));
}
```

### Step 3: Credit-Aware Processing

Track credit usage per crawl to prevent budget overruns.

```typescript
class CreditTracker {
  private dailyUsage: Map<string, number> = new Map();
  private dailyLimit: number;

  constructor(dailyLimit = 5000) { this.dailyLimit = dailyLimit; }

  canAfford(estimatedPages: number): boolean {
    const today = new Date().toISOString().split('T')[0];
    const used = this.dailyUsage.get(today) || 0;
    return (used + estimatedPages) <= this.dailyLimit;
  }

  record(pages: number) {
    const today = new Date().toISOString().split('T')[0];
    this.dailyUsage.set(today, (this.dailyUsage.get(today) || 0) + pages);
  }
}
```

### Step 4: Fallback from Crawl to Individual Scrape

If a full crawl fails, fall back to scraping critical pages individually.

```typescript
async function resilientScrape(urls: string[]) {
  try {
    return await reliableCrawl(urls[0], { limit: urls.length });
  } catch (crawlError) {
    console.warn('Crawl failed, falling back to individual scrapes');
    const results = [];
    for (const url of urls) {
      try {
        const result = await firecrawl.scrapeUrl(url, {
          formats: ['markdown'], onlyMainContent: true
        });
        results.push(result);
      } catch (e) { console.error(`Failed: ${url}`); }
      await new Promise(r => setTimeout(r, 1000));
    }
    return results;
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Crawl times out | Large site, slow JS rendering | Set page limits and timeout |
| Empty markdown | Anti-bot or JS-rendered content | Increase `waitFor`, try individual scrape |
| Credit overrun | No budget tracking | Implement credit-aware circuit breaker |
| Partial crawl results | Site structure changes | Validate content, retry failed pages |

## Examples

### Health Check
```typescript
const health = {
  creditsUsedToday: tracker.getUsage(),
  activeJobs: await getActiveCrawlCount(),
  failureRate: monitor.getHourlyFailureRate()
};
```

## Resources
- [Firecrawl API Docs](https://docs.firecrawl.dev)
