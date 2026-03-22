---
name: firecrawl-known-pitfalls
description: |
  Identify and avoid Firecrawl anti-patterns and common integration mistakes.
  Use when reviewing Firecrawl code, onboarding new developers,
  or auditing existing integrations for best practices violations.
  Trigger with phrases like "firecrawl mistakes", "firecrawl anti-patterns",
  "firecrawl pitfalls", "firecrawl what not to do", "firecrawl code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, audit]

---
# Firecrawl Known Pitfalls

## Overview
Real gotchas from production Firecrawl integrations. Each pitfall includes the bad pattern, why it fails, and the correct approach. Use this as a code review checklist.

## Pitfall 1: Unbounded Crawl (Credit Bomb)
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// BAD: no limit — a docs site with 50K pages burns your entire credit balance
await firecrawl.crawlUrl("https://docs.large-project.org");

// GOOD: always set limit, maxDepth, and path filters
await firecrawl.crawlUrl("https://docs.large-project.org", {
  limit: 100,
  maxDepth: 3,
  includePaths: ["/api/*", "/guides/*"],
  excludePaths: ["/changelog/*", "/blog/*"],
  scrapeOptions: { formats: ["markdown"] },
});
```

## Pitfall 2: Not Specifying Output Format
```typescript
// BAD: default format may not include markdown
const result = await firecrawl.scrapeUrl("https://example.com");
console.log(result.markdown); // might be undefined!

// GOOD: explicitly request the format you need
const result = await firecrawl.scrapeUrl("https://example.com", {
  formats: ["markdown"],
  onlyMainContent: true,
});
console.log(result.markdown); // guaranteed present
```

## Pitfall 3: Not Waiting for JS-Heavy Pages
```typescript
// BAD: SPAs show loading state, not content
const result = await firecrawl.scrapeUrl("https://app.example.com/dashboard");
// result.markdown === "Loading..." or empty

// GOOD: wait for JS to render
const result = await firecrawl.scrapeUrl("https://app.example.com/dashboard", {
  formats: ["markdown"],
  waitFor: 5000,  // wait 5s for JS rendering
  onlyMainContent: true,
});

// BETTER: wait for a specific element
const result = await firecrawl.scrapeUrl("https://app.example.com/dashboard", {
  formats: ["markdown"],
  actions: [
    { type: "wait", selector: ".main-content" },
  ],
});
```

## Pitfall 4: Wrong Package Name / Import
```typescript
// BAD: these packages don't exist or are wrong
import FirecrawlApp from "firecrawl-js";       // wrong
import { FireCrawlClient } from "@firecrawl/sdk";  // wrong

// GOOD: the correct npm package
import FirecrawlApp from "@mendable/firecrawl-js";  // correct!

// Install: npm install @mendable/firecrawl-js
```

## Pitfall 5: Polling Too Aggressively
```typescript
// BAD: polling every 100ms wastes resources and may trigger rate limits
let status = await firecrawl.checkCrawlStatus(jobId);
while (status.status !== "completed") {
  status = await firecrawl.checkCrawlStatus(jobId);
  // No delay! Hammering the API
}

// GOOD: poll with backoff
let status = await firecrawl.checkCrawlStatus(jobId);
let interval = 2000;
while (status.status === "scraping") {
  await new Promise(r => setTimeout(r, interval));
  status = await firecrawl.checkCrawlStatus(jobId);
  interval = Math.min(interval * 1.5, 30000); // back off to 30s
}
```

## Pitfall 6: No Error Handling on Scrape
```typescript
// BAD: assuming scrape always succeeds
const result = await firecrawl.scrapeUrl(url, { formats: ["markdown"] });
processContent(result.markdown!); // crashes if scrape failed

// GOOD: check result and handle failures
const result = await firecrawl.scrapeUrl(url, { formats: ["markdown"] });
if (!result.success || !result.markdown || result.markdown.length < 50) {
  console.error(`Scrape failed or empty for ${url}`);
  return null;
}
processContent(result.markdown);
```

## Pitfall 7: Ignoring includePaths Start URL Match
```typescript
// BAD: start URL doesn't match includePaths — crawl returns 0 pages
await firecrawl.crawlUrl("https://example.com/docs/intro", {
  includePaths: ["/api/*"],  // start URL /docs/intro doesn't match /api/*
  limit: 50,
});

// GOOD: start URL must match (or omit) the include pattern
await firecrawl.crawlUrl("https://example.com", {
  includePaths: ["/docs/*", "/api/*"],  // start from root, filter paths
  limit: 50,
});
```

## Pitfall 8: Requesting Screenshots Unnecessarily
```typescript
// BAD: screenshots are expensive (latency and bandwidth)
await firecrawl.scrapeUrl(url, {
  formats: ["markdown", "html", "screenshot"],
  // screenshot adds 5-10s to every scrape
});

// GOOD: only request screenshot when you actually need visual capture
await firecrawl.scrapeUrl(url, {
  formats: ["markdown"],  // just what you need
  onlyMainContent: true,
});
```

## Pitfall 9: Not Using Batch for Multiple URLs
```typescript
// BAD: sequential scrapes (slow, N API calls)
const results = [];
for (const url of urls) {
  results.push(await firecrawl.scrapeUrl(url, { formats: ["markdown"] }));
}

// GOOD: batch scrape (1 API call, internally parallel)
const batchResult = await firecrawl.batchScrapeUrls(urls, {
  formats: ["markdown"],
  onlyMainContent: true,
});
```

## Pitfall 10: Not Validating Extracted Content
```typescript
// BAD: trusting LLM extraction blindly
const result = await firecrawl.scrapeUrl(url, {
  formats: ["extract"],
  extract: { schema: productSchema },
});
await db.insert(result.extract); // could be null, malformed, or hallucinated

// GOOD: validate with Zod before persisting
import { z } from "zod";

const ProductSchema = z.object({
  name: z.string().min(1),
  price: z.number().positive(),
});

const parsed = ProductSchema.safeParse(result.extract);
if (parsed.success) {
  await db.insert(parsed.data);
} else {
  console.error("Extraction validation failed:", parsed.error.issues);
}
```

## Code Review Checklist

- [ ] All `crawlUrl` calls have `limit` set
- [ ] `formats` explicitly specified (never rely on defaults)
- [ ] `waitFor` or `actions` used for SPAs
- [ ] Import is `@mendable/firecrawl-js`
- [ ] Async crawl polls with backoff, not tight loop
- [ ] Scrape result checked for success and content length
- [ ] Batch scrape used for multiple known URLs
- [ ] Extract results validated before persistence
- [ ] Error handling for 429, 402, and empty content

## Resources
- [Firecrawl Docs](https://docs.firecrawl.dev)
- [Scrape vs Crawl](https://docs.firecrawl.dev/features/crawl)
- [Advanced Scraping Guide](https://docs.firecrawl.dev/advanced-scraping-guide)

## Next Steps
For reference architecture, see `firecrawl-reference-architecture`.
