---
name: firecrawl-advanced-troubleshooting
description: |
  Debug hard-to-diagnose Firecrawl issues with systematic isolation and evidence collection.
  Use when standard troubleshooting fails, investigating why scrapes return empty content,
  crawl jobs hang, or webhooks don't fire.
  Trigger with phrases like "firecrawl hard bug", "firecrawl mystery error",
  "firecrawl impossible to debug", "firecrawl deep debug", "firecrawl not scraping".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, debugging, scaling]

---
# Firecrawl Advanced Troubleshooting

## Overview
Deep debugging techniques for complex Firecrawl issues: empty scrapes on certain domains, crawl jobs that never complete, inconsistent extraction results, and webhook delivery failures. Uses systematic layer-by-layer isolation.

## Instructions

### Step 1: Minimal Reproduction
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

// Strip everything down to the simplest failing case
async function minimalRepro() {
  const firecrawl = new FirecrawlApp({
    apiKey: process.env.FIRECRAWL_API_KEY!,
  });

  // Test 1: Can we scrape at all?
  console.log("Test 1: Basic scrape");
  const basic = await firecrawl.scrapeUrl("https://example.com", {
    formats: ["markdown"],
  });
  console.log(`  Success: ${basic.success}, Length: ${basic.markdown?.length}`);

  // Test 2: Does the target URL work?
  console.log("Test 2: Target URL");
  const target = await firecrawl.scrapeUrl("https://YOUR-FAILING-URL.com", {
    formats: ["markdown"],
  });
  console.log(`  Success: ${target.success}, Length: ${target.markdown?.length}`);

  // Test 3: With waitFor for JS rendering
  console.log("Test 3: With JS wait");
  const withWait = await firecrawl.scrapeUrl("https://YOUR-FAILING-URL.com", {
    formats: ["markdown"],
    waitFor: 10000,
    onlyMainContent: true,
  });
  console.log(`  Success: ${withWait.success}, Length: ${withWait.markdown?.length}`);

  // Test 4: With actions
  console.log("Test 4: With actions");
  const withActions = await firecrawl.scrapeUrl("https://YOUR-FAILING-URL.com", {
    formats: ["markdown", "screenshot"],
    actions: [
      { type: "wait", milliseconds: 3000 },
      { type: "scroll", direction: "down" },
      { type: "wait", milliseconds: 2000 },
    ],
  });
  console.log(`  Success: ${withActions.success}, Length: ${withActions.markdown?.length}`);
  // Screenshot will show what Firecrawl actually sees
}
```

### Step 2: Layer-by-Layer Isolation
```typescript
async function diagnose(url: string) {
  const firecrawl = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY! });
  const results: Array<{ test: string; pass: boolean; detail: string }> = [];

  // Layer 1: API connectivity
  try {
    await firecrawl.scrapeUrl("https://example.com", { formats: ["markdown"] });
    results.push({ test: "API connectivity", pass: true, detail: "OK" });
  } catch (e: any) {
    results.push({ test: "API connectivity", pass: false, detail: `${e.statusCode}: ${e.message}` });
    return results; // can't continue
  }

  // Layer 2: Target URL accessibility
  try {
    const result = await firecrawl.scrapeUrl(url, { formats: ["markdown"] });
    const hasContent = (result.markdown?.length || 0) > 50;
    results.push({
      test: "Target scrape",
      pass: result.success && hasContent,
      detail: `Success: ${result.success}, Chars: ${result.markdown?.length}, Status: ${result.metadata?.statusCode}`,
    });
  } catch (e: any) {
    results.push({ test: "Target scrape", pass: false, detail: e.message });
  }

  // Layer 3: Content quality
  try {
    const result = await firecrawl.scrapeUrl(url, {
      formats: ["markdown", "html"],
      onlyMainContent: true,
      waitFor: 5000,
    });
    const md = result.markdown || "";
    const isErrorPage = /404|403|access denied|captcha|blocked/i.test(md);
    results.push({
      test: "Content quality",
      pass: md.length > 100 && !isErrorPage,
      detail: `Chars: ${md.length}, Error page: ${isErrorPage}, Has headings: ${/^#{1,3}\s/m.test(md)}`,
    });
  } catch (e: any) {
    results.push({ test: "Content quality", pass: false, detail: e.message });
  }

  // Layer 4: Map endpoint (URL discovery)
  try {
    const map = await firecrawl.mapUrl(url);
    results.push({
      test: "Map endpoint",
      pass: (map.links?.length || 0) > 0,
      detail: `Found ${map.links?.length} URLs`,
    });
  } catch (e: any) {
    results.push({ test: "Map endpoint", pass: false, detail: e.message });
  }

  return results;
}

// Run diagnosis
const results = await diagnose("https://YOUR-URL.com");
console.table(results);
```

### Step 3: Debug Empty Scrapes
```typescript
// When scrapeUrl returns empty or thin markdown:
async function debugEmptyScrape(url: string) {
  const firecrawl = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY! });

  // Get all formats to understand what Firecrawl sees
  const result = await firecrawl.scrapeUrl(url, {
    formats: ["markdown", "html", "screenshot"],
    waitFor: 10000,
  });

  console.log("=== Scrape Debug ===");
  console.log(`URL: ${result.metadata?.sourceURL}`);
  console.log(`Status: ${result.metadata?.statusCode}`);
  console.log(`Markdown length: ${result.markdown?.length || 0}`);
  console.log(`HTML length: ${result.html?.length || 0}`);
  console.log(`Title: ${result.metadata?.title}`);

  // Check if HTML has content but markdown doesn't
  if ((result.html?.length || 0) > 1000 && (result.markdown?.length || 0) < 100) {
    console.log("DIAGNOSIS: HTML has content but markdown extraction failed");
    console.log("FIX: Content may be in iframes or shadow DOM. Try with actions.");
  }

  // Check for bot detection
  if (/captcha|cloudflare|access denied|please verify/i.test(result.html || "")) {
    console.log("DIAGNOSIS: Bot detection / CAPTCHA detected");
    console.log("FIX: Site blocks automated scraping. Contact Firecrawl support.");
  }

  return result;
}
```

### Step 4: Debug Stuck Crawl Jobs
```typescript
async function debugCrawlJob(jobId: string) {
  const firecrawl = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY! });

  const status = await firecrawl.checkCrawlStatus(jobId);
  console.log("=== Crawl Job Debug ===");
  console.log(`Status: ${status.status}`);
  console.log(`Completed: ${status.completed}/${status.total}`);
  console.log(`Error: ${status.error || "none"}`);

  if (status.status === "scraping" && status.completed === status.total) {
    console.log("DIAGNOSIS: All pages scraped but job not marked complete");
    console.log("FIX: This is a Firecrawl backend issue. Wait or start a new crawl.");
  }

  if (status.completed === 0 && status.status === "scraping") {
    console.log("DIAGNOSIS: Crawl started but no pages scraped");
    console.log("FIX: Check if start URL returns content. Try scrapeUrl first.");
  }
}
```

### Step 5: Timing Analysis
```typescript
async function timeScrape(url: string, iterations = 5) {
  const firecrawl = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY! });
  const times: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const start = Date.now();
    await firecrawl.scrapeUrl(url, { formats: ["markdown"] });
    times.push(Date.now() - start);
  }

  times.sort((a, b) => a - b);
  console.log(`p50: ${times[Math.floor(times.length * 0.5)]}ms`);
  console.log(`p95: ${times[Math.floor(times.length * 0.95)]}ms`);
  console.log(`min: ${times[0]}ms, max: ${times[times.length - 1]}ms`);
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Empty markdown, HTML exists | Shadow DOM or iframes | Use `actions` to interact with page |
| Scrape returns CAPTCHA | Bot detection | Try with `mobile: true`, contact Firecrawl |
| Crawl stuck at 0 pages | Start URL blocked | Verify URL loads in browser first |
| Inconsistent results | JS rendering timing | Increase `waitFor`, use selector-based wait |
| Webhook never fires | URL unreachable | Test with `curl` to your endpoint first |

## Support Escalation Template
```
Subject: [P1/P2/P3] [Brief description]

URL: [failing URL]
API Key prefix: fc-xxx (first 6 chars)
Timestamp: [ISO 8601]

Expected: [what should happen]
Actual: [what happens]

Diagnostic output: [paste from diagnose() above]
Screenshot: [if available from screenshot format]

Workarounds tried:
1. [what you tried] — result: [outcome]
```

## Resources
- [Firecrawl Advanced Scraping](https://docs.firecrawl.dev/advanced-scraping-guide)
- [GitHub Issues](https://github.com/mendableai/firecrawl/issues)
- [Firecrawl Discord](https://discord.gg/firecrawl)

## Next Steps
For load testing, see `firecrawl-load-scale`.
