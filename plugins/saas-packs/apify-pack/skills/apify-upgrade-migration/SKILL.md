---
name: apify-upgrade-migration
description: |
  Upgrade Apify SDK, apify-client, and Crawlee versions safely.
  Use when migrating between SDK versions, handling breaking changes,
  or updating from Apify SDK v2 to v3 (Crawlee split).
  Trigger: "upgrade apify", "apify migration", "apify breaking changes",
  "update apify SDK", "crawlee upgrade", "apify v2 to v3".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Upgrade & Migration

## Overview

Guide for upgrading `apify`, `apify-client`, and `crawlee` packages. The biggest migration in Apify's history was SDK v2 to v3, which split crawling functionality into the `crawlee` package. This skill covers that migration plus general upgrade procedures.

## Prerequisites

- Git branch for the upgrade
- Test suite available
- Current versions documented

## Instructions

### Step 1: Check Current Versions

```bash
# Check installed versions
npm list apify apify-client crawlee 2>/dev/null

# Check latest available versions
npm view apify version
npm view apify-client version
npm view crawlee version

# Check for outdated packages
npm outdated apify apify-client crawlee
```

### Step 2: Create Upgrade Branch

```bash
git checkout -b upgrade/apify-packages
```

### Step 3: Upgrade Packages

```bash
# Upgrade to latest
npm install apify@latest crawlee@latest apify-client@latest

# Or upgrade to specific version
npm install apify@3.2.0 crawlee@3.11.0

# Check for peer dependency issues
npm ls 2>&1 | grep "ERESOLVE\|peer dep"
```

### Step 4: Run Tests and Fix Issues

```bash
npm test
npm run build  # Catch TypeScript errors
```

## Major Migration: Apify SDK v2 to v3 (Crawlee Split)

This is the most common migration. In v3, crawling code moved to `crawlee`.

### Import Changes

```typescript
// ---- BEFORE (SDK v2) ----
import Apify from 'apify';
const { CheerioCrawler, PlaywrightCrawler, log } = Apify;

// ---- AFTER (SDK v3 + Crawlee) ----
import { Actor } from 'apify';
import { CheerioCrawler, PlaywrightCrawler, log } from 'crawlee';
```

### Initialization Changes

```typescript
// ---- BEFORE (v2) ----
Apify.main(async () => {
  const input = await Apify.getInput();
  const dataset = await Apify.openDataset();
  await Apify.pushData({ url: 'https://example.com' });
  await Apify.setValue('OUTPUT', { done: true });
});

// ---- AFTER (v3) ----
await Actor.main(async () => {
  const input = await Actor.getInput();
  const dataset = await Actor.openDataset();
  await Actor.pushData({ url: 'https://example.com' });
  await Actor.setValue('OUTPUT', { done: true });
});
```

### Crawler Configuration Changes

```typescript
// ---- BEFORE (v2) ----
const crawler = new Apify.CheerioCrawler({
  handlePageFunction: async ({ request, $ }) => {
    // ...
  },
  handleFailedRequestFunction: async ({ request }) => {
    // ...
  },
});

// ---- AFTER (v3 / Crawlee) ----
const crawler = new CheerioCrawler({
  requestHandler: async ({ request, $ }) => {
    // renamed from handlePageFunction
  },
  failedRequestHandler: async ({ request }, error) => {
    // renamed from handleFailedRequestFunction
    // error is now second argument
  },
});
```

### Proxy Configuration Changes

```typescript
// ---- BEFORE (v2) ----
const proxyConfiguration = await Apify.createProxyConfiguration({
  groups: ['RESIDENTIAL'],
});

// ---- AFTER (v3) ----
const proxyConfiguration = await Actor.createProxyConfiguration({
  groups: ['RESIDENTIAL'],
});
```

### Request Queue Changes

```typescript
// ---- BEFORE (v2) ----
const requestQueue = await Apify.openRequestQueue();
await requestQueue.addRequest({ url: 'https://example.com' });

// ---- AFTER (v3) ----
// Option A: Use enqueueLinks in crawler (preferred)
await enqueueLinks({ strategy: 'same-domain' });

// Option B: Open queue directly
const requestQueue = await Actor.openRequestQueue();
await requestQueue.addRequest({ url: 'https://example.com' });
```

### Router Pattern (New in v3)

```typescript
// v3 introduced explicit routers (replaces label-based if/else)
import { createCheerioRouter } from 'crawlee';

const router = createCheerioRouter();

router.addDefaultHandler(async ({ request, $, enqueueLinks }) => {
  // Handle listing pages
  await enqueueLinks({ selector: 'a.detail', label: 'DETAIL' });
});

router.addHandler('DETAIL', async ({ request, $ }) => {
  // Handle detail pages
  await Actor.pushData({ url: request.url, title: $('h1').text() });
});

const crawler = new CheerioCrawler({ requestHandler: router });
```

## apify-client Upgrade Notes

The `apify-client` package has been more stable. Key changes across versions:

```typescript
// v1.x → v2.x: Constructor changed
// Before
const { ApifyClient } = require('apify-client');
const client = new ApifyClient({ userId: 'xxx', token: 'yyy' });

// After (v2+): userId removed, just token
const client = new ApifyClient({ token: 'yyy' });

// Method chaining style (consistent since v2)
const run = await client.actor('username/actor').call(input);
const { items } = await client.dataset(run.defaultDatasetId).listItems();
```

## Upgrade Verification Script

```typescript
// verify-upgrade.ts — run after upgrading
import { Actor } from 'apify';
import { CheerioCrawler, log } from 'crawlee';
import { ApifyClient } from 'apify-client';

async function verifyUpgrade() {
  const checks: { name: string; pass: boolean; error?: string }[] = [];

  // Check 1: Imports work
  checks.push({ name: 'Actor import', pass: typeof Actor.init === 'function' });
  checks.push({ name: 'CheerioCrawler import', pass: typeof CheerioCrawler === 'function' });
  checks.push({ name: 'ApifyClient import', pass: typeof ApifyClient === 'function' });

  // Check 2: Client connects
  try {
    const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
    const user = await client.user().get();
    checks.push({ name: 'API connection', pass: !!user.username });
  } catch (err) {
    checks.push({ name: 'API connection', pass: false, error: (err as Error).message });
  }

  // Check 3: Crawler instantiates
  try {
    const crawler = new CheerioCrawler({
      requestHandler: async () => {},
    });
    checks.push({ name: 'Crawler instantiation', pass: true });
  } catch (err) {
    checks.push({ name: 'Crawler instantiation', pass: false, error: (err as Error).message });
  }

  // Report
  console.log('\n=== Upgrade Verification ===');
  for (const check of checks) {
    const status = check.pass ? 'PASS' : 'FAIL';
    console.log(`  [${status}] ${check.name}${check.error ? ` — ${check.error}` : ''}`);
  }

  const allPassed = checks.every(c => c.pass);
  console.log(`\n${allPassed ? 'All checks passed.' : 'Some checks failed!'}`);
  process.exit(allPassed ? 0 : 1);
}

verifyUpgrade();
```

## Rollback Procedure

```bash
# Revert to previous versions
npm install apify@3.1.0 crawlee@3.10.0 apify-client@2.9.0 --save-exact

# Or restore from lock file
git checkout main -- package-lock.json
npm ci

# On the platform: roll back Actor build
# Console > Actor > Builds > select previous build > Set as default
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `handlePageFunction is not valid` | Using v2 option names in v3 | Rename to `requestHandler` |
| `Apify.main is not a function` | v2 default export removed | Import `{ Actor }` from `apify` |
| `Cannot find module 'crawlee'` | Crawlee not installed | `npm install crawlee` |
| Type errors after upgrade | Changed interfaces | Check release notes for type changes |

## Resources

- [SDK v2 to v3 Migration Guide](https://docs.apify.com/sdk/js/docs/upgrading/upgrading-to-v3)
- [Crawlee Changelog](https://crawlee.dev/js/api/core/changelog)
- [apify-client Releases](https://github.com/apify/apify-client-js/releases)

## Next Steps

For CI integration during upgrades, see `apify-ci-integration`.
