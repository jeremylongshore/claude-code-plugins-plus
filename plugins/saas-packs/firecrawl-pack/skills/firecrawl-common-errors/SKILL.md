---
name: firecrawl-common-errors
description: |
  Diagnose and fix Firecrawl common errors and API response codes.
  Use when encountering Firecrawl errors, debugging failed scrapes,
  or troubleshooting crawl job issues.
  Trigger with phrases like "firecrawl error", "fix firecrawl",
  "firecrawl not working", "debug firecrawl", "firecrawl 429", "firecrawl 402".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, debugging]

---
# Firecrawl Common Errors

## Overview
Quick-reference diagnostic guide for the most common Firecrawl API errors. Covers HTTP status codes, SDK exceptions, empty content, and crawl job failures with concrete fixes.

## Prerequisites
- Firecrawl SDK installed (`@mendable/firecrawl-js`)
- `FIRECRAWL_API_KEY` environment variable set
- Access to error logs or console output

## Error Reference

### 401 Unauthorized — Invalid API Key
```
Error: Unauthorized. Invalid API key.
```
**Cause:** API key is missing, malformed, or revoked.
```bash
set -euo pipefail
# Verify key is set and starts with fc-
echo "Key prefix: ${FIRECRAWL_API_KEY:0:3}"

# Test directly
curl -s https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}' | jq .success
```
**Fix:** Regenerate key at [firecrawl.dev/app](https://firecrawl.dev/app). Ensure it starts with `fc-`.

---

### 402 Payment Required — Credits Exhausted
```
Error: Payment required. You have exceeded your credit limit.
```
**Cause:** Monthly or plan credits are used up.
```bash
set -euo pipefail
# Check remaining credits
curl -s https://api.firecrawl.dev/v1/team/credits \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" | jq .
```
**Fix:** Upgrade plan or wait for monthly credit reset. Failed requests do not consume credits.

---

### 429 Too Many Requests — Rate Limited
```
Error: Rate limit exceeded. Retry after X seconds.
```
**Cause:** Too many concurrent requests or requests per minute.
```typescript
// Fix: implement exponential backoff
async function scrapeWithBackoff(url: string, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      return await firecrawl.scrapeUrl(url, { formats: ["markdown"] });
    } catch (err: any) {
      if (err.statusCode !== 429 || i === retries - 1) throw err;
      const delay = 1000 * Math.pow(2, i);
      console.warn(`Rate limited, retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```
**Fix:** Respect `Retry-After` header. Queue requests with p-queue.

---

### Empty Markdown — JS Content Not Rendered
```typescript
const result = await firecrawl.scrapeUrl("https://spa-app.com");
console.log(result.markdown); // "" or just nav text
```
**Cause:** Single-page app or JS-heavy site needs time to render.
```typescript
// Fix: add waitFor and use actions for dynamic content
const result = await firecrawl.scrapeUrl("https://spa-app.com", {
  formats: ["markdown"],
  waitFor: 5000,  // wait 5s for JS rendering
  onlyMainContent: true,
});
```

---

### Crawl Returns Zero Pages
```typescript
const crawl = await firecrawl.crawlUrl("https://example.com/docs", {
  includePaths: ["/api/*"],
});
// crawl.data is empty
```
**Cause:** Start URL does not match `includePaths` pattern, or paths are too restrictive.
```typescript
// Fix: ensure start URL matches include patterns
const crawl = await firecrawl.crawlUrl("https://example.com", {
  includePaths: ["/docs/*", "/api/*"],  // start URL must match too
  limit: 50,
});
```

---

### Crawl Stuck at "scraping" Status
```typescript
const status = await firecrawl.checkCrawlStatus(jobId);
// status.status === "scraping" for >10 minutes
```
**Cause:** Large site, slow JS rendering, or Firecrawl queue backup.
```typescript
// Fix: set timeout and fall back to individual scrapes
const TIMEOUT_MS = 600000; // 10 minutes
const deadline = Date.now() + TIMEOUT_MS;

while (Date.now() < deadline) {
  const status = await firecrawl.checkCrawlStatus(jobId);
  if (status.status === "completed") return status;
  if (status.status === "failed") throw new Error(status.error);
  await new Promise(r => setTimeout(r, 5000));
}
throw new Error("Crawl timed out — try reducing limit or using scrapeUrl");
```

---

### MODULE_NOT_FOUND — Wrong Package Name
```
Error: Cannot find module '@firecrawl/sdk'
```
**Cause:** Using wrong npm package name.
```bash
set -euo pipefail
# The correct package is @mendable/firecrawl-js
npm install @mendable/firecrawl-js
```
**Import:** `import FirecrawlApp from "@mendable/firecrawl-js"`

## Quick Diagnostic
```bash
set -euo pipefail
# 1. Check Firecrawl API health
curl -s https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}' | jq '{success, markdown_length: (.markdown | length)}'

# 2. Verify SDK version
npm list @mendable/firecrawl-js 2>/dev/null

# 3. Check env var
env | grep FIRECRAWL
```

## Error Handling
| Status | Meaning | Retryable | Action |
|--------|---------|-----------|--------|
| 200 | Success | N/A | Process result |
| 401 | Bad API key | No | Check/rotate key |
| 402 | No credits | No | Upgrade or wait for reset |
| 408 | Timeout | Yes | Increase timeout, simplify request |
| 429 | Rate limited | Yes | Backoff, check Retry-After |
| 500 | Server error | Yes | Retry with backoff |
| 503 | Service down | Yes | Check status page, retry later |

## Examples

### Comprehensive Error Handler
```typescript
async function safeScrape(url: string) {
  try {
    return await firecrawl.scrapeUrl(url, { formats: ["markdown"] });
  } catch (err: any) {
    const status = err.statusCode;
    if (status === 401) console.error("Invalid API key");
    else if (status === 402) console.error("Credits exhausted");
    else if (status === 429) console.error("Rate limited — retry later");
    else console.error(`Firecrawl error ${status}:`, err.message);
    return null;
  }
}
```

## Resources
- [Firecrawl API Reference](https://docs.firecrawl.dev/api-reference/introduction)
- [Rate Limits](https://docs.firecrawl.dev/rate-limits)
- [Firecrawl Dashboard](https://firecrawl.dev/app)

## Next Steps
For comprehensive debugging, see `firecrawl-debug-bundle`.
