# Apify Error Reference — Full Catalog

The ten most common Apify Actor and API errors, each with the raw error
signature, root cause, diagnosis steps, and a copy-paste fix. Jump to the
error whose signature matches your run log or API response.

1. [Actor Run Status: FAILED](#1-actor-run-status-failed)
2. [Actor Run Status: TIMED-OUT](#2-actor-run-status-timed-out)
3. [HTTP 429 — Rate Limited](#3-http-429--rate-limited)
4. [HTTP 401 — Unauthorized](#4-http-401--unauthorized)
5. [Actor Build Failed](#5-actor-build-failed)
6. [Proxy Connection Failed](#6-proxy-connection-failed)
7. [Anti-Bot Block (403/Captcha)](#7-anti-bot-block-403captcha)
8. [Out of Memory](#8-out-of-memory)
9. [Dataset Push Too Large](#9-dataset-push-too-large)
10. [Actor Not Found](#10-actor-not-found)

---

## 1. Actor Run Status: FAILED

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

## 2. Actor Run Status: TIMED-OUT

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

## 3. HTTP 429 — Rate Limited

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

## 4. HTTP 401 — Unauthorized

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

## 5. Actor Build Failed

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

## 6. Proxy Connection Failed

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

## 7. Anti-Bot Block (403/Captcha)

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

## 8. Out of Memory

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

## 9. Dataset Push Too Large

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

## 10. Actor Not Found

```
ApifyApiError: Actor 'user/actor-name' not found (404)
```

**Cause:** Wrong Actor ID, or Actor is private and you lack access.

**Fix:** Actor IDs follow the format `username/actor-name` or the Actor's unique ID (alphanumeric). Check the correct ID at `https://apify.com/username/actor-name`.
</content>
</invoke>
