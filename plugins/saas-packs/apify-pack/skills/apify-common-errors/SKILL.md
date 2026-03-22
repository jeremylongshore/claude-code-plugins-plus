---
name: apify-common-errors
description: |
  Diagnose and fix common Apify Actor and API errors.
  Use when encountering run failures, API errors, proxy issues,
  or Actor crashes on the Apify platform.
  Trigger: "apify error", "fix apify", "actor failed",
  "apify not working", "debug apify", "apify 429".
allowed-tools: Read, Grep, Bash(curl:*), Bash(apify:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Common Errors

## Overview

Quick diagnostic reference for the most common Apify errors. Covers Actor run failures, API errors, proxy problems, anti-bot blocks, and platform-specific issues.

## Prerequisites

- Apify token configured
- Access to Apify Console for log review

## Error Reference

### 1. Actor Run Status: FAILED

```
Status: FAILED
StatusMessage: Process exited with code 1
```

**Cause:** Unhandled exception in Actor code.

**Diagnosis:**
```typescript
// Check run log via API
const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
const run = await client.run('RUN_ID').get();
console.log(run.statusMessage);

// Get the run log
const log = await client.run('RUN_ID').log().get();
console.log(log);  // Full stdout/stderr output
```

**Fix:** Read the log, find the stack trace, fix the bug. Common causes:
- Missing input validation (`Actor.getInput()` returns `null`)
- Selector returns no results (page structure changed)
- Unhandled promise rejection

---

### 2. Actor Run Status: TIMED-OUT

```
Status: TIMED-OUT
StatusMessage: Actor timed out after 3600 seconds
```

**Cause:** Actor exceeded its configured timeout.

**Fix:**
```typescript
// Increase timeout when calling via client
const run = await client.actor('user/actor').call(input, {
  timeout: 7200,  // 2 hours in seconds
});

// Or set in Actor configuration on platform
// Console > Actor > Settings > Timeout
```

**Prevention:** Reduce workload scope or increase `maxConcurrency`.

---

### 3. HTTP 429 — Rate Limited

```
ApifyApiError: Rate limit exceeded (429)
```

**Cause:** More than 60 requests/second to a single API resource.

**Fix:** The `apify-client` package retries 429s automatically (up to 8 retries with exponential backoff). If you still hit limits:

```typescript
// Add delays between API calls
import { sleep } from 'crawlee';

for (const item of items) {
  await client.dataset(dsId).pushItems([item]);
  await sleep(100);  // 100ms between calls
}

// Better: batch push items (one API call)
await client.dataset(dsId).pushItems(items);  // Up to 9MB per call
```

---

### 4. HTTP 401 — Unauthorized

```
ApifyApiError: Authentication required (401)
```

**Cause:** Invalid, expired, or missing API token.

**Diagnosis:**
```bash
# Test your token
curl -s -H "Authorization: Bearer $APIFY_TOKEN" \
  https://api.apify.com/v2/users/me | jq '.data.username'
```

**Fix:** Regenerate token at Console > Settings > Integrations.

---

### 5. Actor Build Failed

```
Build failed: npm ERR! code ERESOLVE
```

**Cause:** Dependency conflicts in `package.json` or Dockerfile issues.

**Diagnosis:**
```bash
# Check build log on platform
apify builds ls

# Test build locally
docker build -t my-actor -f .actor/Dockerfile .
```

**Fix:** Run `npm install` locally first. Ensure `package-lock.json` is committed. Check Node.js version matches the base image.

---

### 6. Proxy Connection Failed

```
Error: Proxy responded with 502 Bad Gateway
ProxyError: Could not connect to proxy
```

**Cause:** Proxy configuration issue or proxy credits exhausted.

**Fix:**
```typescript
// Check proxy configuration
const proxyConfig = await Actor.createProxyConfiguration({
  groups: ['BUYPROXIES94952'],  // Verify group name in Console
});

// Test proxy connectivity
const proxyUrl = await proxyConfig.newUrl();
console.log('Proxy URL:', proxyUrl);

// Switch to residential if datacenter is blocked
const resProxy = await Actor.createProxyConfiguration({
  groups: ['RESIDENTIAL'],
  countryCode: 'US',
});
```

---

### 7. Anti-Bot Block (403/Captcha)

```
Error: Request blocked — received status 403
Error: Captcha detected on page
```

**Cause:** Target website detected scraping activity.

**Fix:**
```typescript
const crawler = new PlaywrightCrawler({
  proxyConfiguration: await Actor.createProxyConfiguration({
    groups: ['RESIDENTIAL'],
  }),
  // Mimic real browser behavior
  launchContext: {
    launchOptions: {
      args: ['--disable-blink-features=AutomationControlled'],
    },
  },
  preNavigationHooks: [
    async ({ page }) => {
      // Randomize viewport
      await page.setViewportSize({
        width: 1280 + Math.floor(Math.random() * 200),
        height: 720 + Math.floor(Math.random() * 200),
      });
    },
  ],
  maxConcurrency: 3,  // Lower concurrency = less suspicious
  navigationTimeoutSecs: 60,
});
```

---

### 8. Out of Memory

```
FATAL ERROR: CALL_AND_RETRY_LAST Allocation failed — JavaScript heap out of memory
```

**Cause:** Actor memory allocation too low for the workload.

**Fix:**
```typescript
// Increase memory when running via API
const run = await client.actor('user/actor').call(input, {
  memory: 4096,  // MB — powers of 2: 128, 256, 512, 1024, 2048, 4096, ...
});

// Or reduce memory usage in Actor code
const crawler = new CheerioCrawler({
  maxConcurrency: 5,              // Fewer concurrent pages
  maxRequestsPerCrawl: 1000,      // Cap total requests
  requestHandlerTimeoutSecs: 30,  // Fail fast on slow pages
});
```

---

### 9. Dataset Push Too Large

```
ApifyApiError: Payload too large (413) — max 9MB per request
```

**Fix:**
```typescript
// Chunk large pushes
function chunkArray<T>(arr: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    chunks.push(arr.slice(i, i + size));
  }
  return chunks;
}

for (const chunk of chunkArray(items, 500)) {
  await client.dataset(dsId).pushItems(chunk);
}
```

---

### 10. Actor Not Found

```
ApifyApiError: Actor 'user/actor-name' not found (404)
```

**Cause:** Wrong Actor ID, or Actor is private and you lack access.

**Fix:** Actor IDs follow the format `username/actor-name` or the Actor's unique ID (alphanumeric). Check the correct ID at `https://apify.com/username/actor-name`.

## Quick Diagnostic Commands

```bash
# Check Apify platform status
curl -s https://api.apify.com/v2/health | jq '.'

# Verify your auth
curl -s -H "Authorization: Bearer $APIFY_TOKEN" \
  https://api.apify.com/v2/users/me | jq '.data.username'

# Check installed package versions
npm list apify-client apify crawlee 2>/dev/null

# Get last run status
curl -s -H "Authorization: Bearer $APIFY_TOKEN" \
  "https://api.apify.com/v2/acts/USER~ACTOR/runs?limit=1&desc=true" | \
  jq '.data.items[0] | {status, statusMessage, startedAt, finishedAt}'
```

## Error Handling

| HTTP Code | Meaning | Retryable | Action |
|-----------|---------|-----------|--------|
| 400 | Bad request | No | Fix input/params |
| 401 | Unauthorized | No | Check token |
| 403 | Forbidden | No | Check permissions |
| 404 | Not found | No | Verify resource ID |
| 408 | Timeout | Yes | Retry with backoff |
| 413 | Payload too large | No | Reduce batch size |
| 429 | Rate limited | Yes | Auto-retried by client |
| 500+ | Server error | Yes | Auto-retried by client |

## Resources

- [Apify API Error Codes](https://docs.apify.com/api/v2)
- [Apify Status Page](https://status.apify.com)
- [Actor Run Statuses](https://docs.apify.com/platform/actors/running)

## Next Steps

For comprehensive debugging, see `apify-debug-bundle`.
