---
name: firecrawl-upgrade-migration
description: |
  Upgrade Firecrawl SDK versions and migrate between API versions (v0 to v1/v2).
  Use when upgrading the SDK, handling breaking changes between versions,
  or migrating from the old API to the current v2 API.
  Trigger with phrases like "upgrade firecrawl", "firecrawl migration",
  "firecrawl v2", "update firecrawl SDK", "firecrawl breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, api, migration]

---
# Firecrawl Upgrade & Migration

## Current State
!`npm list @mendable/firecrawl-js 2>/dev/null | grep firecrawl || echo 'Not installed'`

## Overview
Guide for upgrading `@mendable/firecrawl-js` SDK versions and migrating from Firecrawl API v0/v1 to v2. Covers breaking changes in import paths, method signatures, response formats, and the new extract v2 schema format.

## Version History

| SDK Version | API Version | Key Changes |
|-------------|-------------|-------------|
| 1.x | v1 | `asyncCrawlUrl`, `checkCrawlStatus`, `mapUrl` added |
| 0.x | v0 | Legacy `crawlUrl` with `waitUntilDone` param |

## Instructions

### Step 1: Check Current Version
```bash
set -euo pipefail
# Check installed version
npm list @mendable/firecrawl-js

# Check latest available
npm view @mendable/firecrawl-js version
```

### Step 2: Create Upgrade Branch
```bash
set -euo pipefail
git checkout -b upgrade/firecrawl-sdk
npm install @mendable/firecrawl-js@latest
npm test
```

### Step 3: Migration — v0 to v1/v2

#### Import Changes
```typescript
// No change needed — import has been stable
import FirecrawlApp from "@mendable/firecrawl-js";
```

#### Crawl Method Changes (v0 -> v1)
```typescript
// BEFORE (v0): crawlUrl with waitUntilDone
const result = await firecrawl.crawlUrl("https://example.com", {
  crawlerOptions: { limit: 50 },
  pageOptions: { onlyMainContent: true },
  waitUntilDone: true,
});

// AFTER (v1+): crawlUrl returns synchronously, or use asyncCrawlUrl
const result = await firecrawl.crawlUrl("https://example.com", {
  limit: 50,
  scrapeOptions: {
    formats: ["markdown"],
    onlyMainContent: true,
  },
});

// For large crawls, use async with polling
const job = await firecrawl.asyncCrawlUrl("https://example.com", {
  limit: 500,
  scrapeOptions: { formats: ["markdown"] },
});
const status = await firecrawl.checkCrawlStatus(job.id);
```

#### Scrape Options Changes (v0 -> v1)
```typescript
// BEFORE (v0)
await firecrawl.scrapeUrl("https://example.com", {
  pageOptions: { onlyMainContent: true },
  extractorOptions: { mode: "llm-extraction", schema: mySchema },
});

// AFTER (v1+)
await firecrawl.scrapeUrl("https://example.com", {
  formats: ["markdown", "extract"],
  onlyMainContent: true,
  extract: { schema: mySchema },
});
```

#### Extract v2 Format (v1 -> v2)
```typescript
// BEFORE (v1): extract as top-level option
await firecrawl.scrapeUrl(url, {
  formats: ["extract"],
  extract: { schema: { type: "object", ... } },
});

// AFTER (v2): schema embedded in formats array
// Note: SDK handles this internally, but REST API changed
// POST /v2/extract with { urls: [...], schema: {...} }
```

#### New Methods in v1+
```typescript
// mapUrl — fast URL discovery (not available in v0)
const map = await firecrawl.mapUrl("https://example.com");
console.log(map.links);

// batchScrapeUrls — scrape multiple URLs at once
const batch = await firecrawl.batchScrapeUrls(
  ["https://a.com", "https://b.com"],
  { formats: ["markdown"] }
);

// asyncBatchScrapeUrls + checkBatchScrapeStatus
const job = await firecrawl.asyncBatchScrapeUrls(urls, { formats: ["markdown"] });
const status = await firecrawl.checkBatchScrapeStatus(job.id);
```

### Step 4: Run Tests and Verify
```bash
set -euo pipefail
npm test

# Quick integration check
npx tsx -e "
import FirecrawlApp from '@mendable/firecrawl-js';
const fc = new FirecrawlApp({ apiKey: process.env.FIRECRAWL_API_KEY! });
const r = await fc.scrapeUrl('https://example.com', { formats: ['markdown'] });
console.log('Success:', r.success, 'Chars:', r.markdown?.length);
"
```

### Step 5: Rollback if Needed
```bash
set -euo pipefail
# Pin to previous version
npm install @mendable/firecrawl-js@1.x.x --save-exact
npm test
```

## Breaking Changes Checklist
- [ ] `crawlerOptions` / `pageOptions` → flat options + `scrapeOptions`
- [ ] `waitUntilDone: true` → use `crawlUrl` (sync) or `asyncCrawlUrl` + polling
- [ ] `extractorOptions` → `extract` with `schema` or `prompt`
- [ ] Response shape: `data` array for crawl results, `markdown`/`html` for scrape
- [ ] New methods: `mapUrl`, `batchScrapeUrls`, `asyncBatchScrapeUrls`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `crawlerOptions is not valid` | Using v0 params on v1+ | Flatten to top-level options |
| `waitUntilDone is not valid` | Removed in v1 | Use `asyncCrawlUrl` + `checkCrawlStatus` |
| `pageOptions not recognized` | Renamed in v1 | Use `scrapeOptions` inside crawl |
| Missing `mapUrl` method | SDK too old | Upgrade to latest version |

## Resources
- [Migrating from v0](https://docs.firecrawl.dev/v1-welcome)
- [Migrating from v1 to v2](https://docs.firecrawl.dev/migrate-to-v2)
- [Firecrawl Changelog](https://firecrawl.dev/changelog)
- [GitHub Releases](https://github.com/mendableai/firecrawl/releases)

## Next Steps
For CI integration during upgrades, see `firecrawl-ci-integration`.
