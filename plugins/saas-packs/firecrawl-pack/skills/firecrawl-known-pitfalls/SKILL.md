---
name: firecrawl-known-pitfalls
description: |
  Identify and avoid FireCrawl anti-patterns and common integration mistakes.
  Use when reviewing FireCrawl code for issues, onboarding new developers,
  or auditing existing FireCrawl integrations for best practices violations.
  Trigger with phrases like "firecrawl mistakes", "firecrawl anti-patterns",
  "firecrawl pitfalls", "firecrawl what not to do", "firecrawl code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Firecrawl Known Pitfalls

## Overview
Real gotchas when using Firecrawl for web scraping and crawling. Firecrawl handles JavaScript rendering and anti-bot bypassing, but its async crawl model and credit-based pricing create specific failure modes.

## Prerequisites
- Firecrawl API key configured
- Understanding of async job patterns
- Awareness of credit-based billing model

## Instructions

### Step 1: Handle Async Crawl Jobs Properly

`crawlUrl` returns a job ID, not results. Polling too aggressively wastes credits and may trigger rate limits.

```typescript
import FirecrawlApp from '@mendable/firecrawl-js';
const firecrawl = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY });

// BAD: assuming synchronous results
const result = await firecrawl.crawlUrl('https://example.com');
console.log(result.data); // This is a job object, not page data!

// GOOD: use the async crawl with proper polling
const crawl = await firecrawl.asyncCrawlUrl('https://example.com', {
  limit: 50,
  scrapeOptions: { formats: ['markdown'] }
});
// Poll with backoff
let status;
do {
  await new Promise(r => setTimeout(r, 5000));
  status = await firecrawl.checkCrawlStatus(crawl.id);
} while (status.status === 'scraping');
```

### Step 2: Avoid Credit Burn on Large Sites

Firecrawl charges per page. Crawling without limits on large sites burns credits fast.

```typescript
// BAD: no limit on a site with 100K pages
await firecrawl.crawlUrl('https://docs.large-project.org');  // burns entire quota

// GOOD: set explicit limits and use URL filters
await firecrawl.crawlUrl('https://docs.large-project.org', {
  limit: 100,
  includePaths: ['/api/*', '/guides/*'],
  excludePaths: ['/changelog/*', '/blog/*'],
  maxDepth: 3
});
```

### Step 3: Don't Assume Markdown Output by Default

Firecrawl can return HTML, markdown, links, or screenshots. Not specifying format returns raw HTML.

```typescript
// BAD: getting HTML when you wanted clean text
const result = await firecrawl.scrapeUrl('https://example.com');
// result.html exists but result.markdown may be absent

// GOOD: specify output format explicitly
const result = await firecrawl.scrapeUrl('https://example.com', {
  formats: ['markdown', 'links'],
  onlyMainContent: true  // strips nav, footer, sidebars
});
console.log(result.markdown);
```

### Step 4: Handle JavaScript-Heavy Pages

Some SPAs need extra wait time for content to render. Default timeouts may capture loading states.

```typescript
// BAD: scraping an SPA with default settings
const result = await firecrawl.scrapeUrl('https://app.example.com/dashboard');
// Gets "Loading..." instead of actual content

// GOOD: configure wait time for JS rendering
const result = await firecrawl.scrapeUrl('https://app.example.com/dashboard', {
  waitFor: 5000,  // wait 5s for JS to render
  formats: ['markdown'],
  onlyMainContent: true
});
```

### Step 5: Respect robots.txt and Rate Limits

Firecrawl honors robots.txt by default. Disabling it risks IP bans and legal issues.

```typescript
// BAD: aggressive crawling that ignores site limits
await firecrawl.crawlUrl('https://example.com', {
  limit: 10000,
  // No delay between requests = potential IP ban
});

// GOOD: respect site constraints
await firecrawl.crawlUrl('https://example.com', {
  limit: 200,
  maxDepth: 3,
  // Firecrawl handles rate limiting internally
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Empty markdown | JS not rendered | Increase `waitFor` timeout |
| Credit depletion | No crawl limit set | Always set `limit` parameter |
| 402 Payment Required | Out of credits | Check balance before large crawls |
| Partial crawl results | Site blocks crawler | Use `scrapeUrl` for individual pages |
| Stale job status | Polling stopped early | Poll until `completed` or `failed` |

## Examples

### Safe Batch Scraping
```typescript
const urls = ['https://a.com', 'https://b.com', 'https://c.com'];
const results = await firecrawl.batchScrapeUrls(urls, {
  formats: ['markdown'],
  onlyMainContent: true
});
```

## Resources
- [Firecrawl Docs](https://docs.firecrawl.dev)
- [Crawl vs Scrape](https://docs.firecrawl.dev/features/crawl)
