---
name: brightdata-upgrade-migration
description: |
  Analyze, plan, and execute Bright Data SDK upgrades with breaking change detection.
  Use when upgrading Bright Data SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade brightdata", "brightdata migration",
  "brightdata breaking changes", "update brightdata SDK", "analyze brightdata version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Upgrade & Migration

## Overview

Guide for migrating between Bright Data products, API versions, and zone configurations. Since Bright Data uses proxy protocols and REST APIs (not versioned SDKs), migrations typically involve changing zone types, proxy endpoints, or API payload formats.

## Prerequisites

- Current Bright Data zone credentials
- Git for version control
- Staging environment for testing

## Instructions

### Step 1: Identify Migration Type

| Migration | From | To | Effort |
|----------|------|----|--------|
| Zone upgrade | Web Unlocker v1 | Web Unlocker v2 | Low |
| Product switch | Residential Proxy | Web Unlocker | Medium |
| Browser migration | Puppeteer direct | Scraping Browser | Medium |
| API migration | Datasets v2 | Datasets v3 | Medium |
| Full platform | Competitor | Bright Data | High |

### Step 2: Migrate from Direct Proxies to Web Unlocker

```typescript
// BEFORE: Raw residential proxy (manual CAPTCHA handling)
const oldProxy = {
  host: 'brd.superproxy.io',
  port: 22225,  // Old residential port
  auth: {
    username: `brd-customer-${CID}-zone-residential_zone`,
    password: OLD_PASSWORD,
  },
};

// AFTER: Web Unlocker (automatic CAPTCHA, fingerprinting)
const newProxy = {
  host: 'brd.superproxy.io',
  port: 33335,  // Web Unlocker port
  auth: {
    username: `brd-customer-${CID}-zone-web_unlocker1`,
    password: NEW_PASSWORD,
  },
};
// Changes: port 22225 → 33335, zone name, password
// Web Unlocker handles CAPTCHAs automatically — remove manual solving code
```

### Step 3: Migrate to Scraping Browser from Puppeteer

```typescript
// BEFORE: Self-hosted Puppeteer with proxy
import puppeteer from 'puppeteer';
const browser = await puppeteer.launch({
  args: [`--proxy-server=http://brd.superproxy.io:22225`],
});

// AFTER: Bright Data Scraping Browser (managed browser)
import puppeteer from 'puppeteer-core';
const AUTH = `brd-customer-${CID}-zone-scraping_browser1:${PASSWORD}`;
const browser = await puppeteer.connect({
  browserWSEndpoint: `wss://${AUTH}@brd.superproxy.io:9222`,
});
// Changes: launch → connect, local browser → remote WebSocket
// Remove: browser install, proxy args, CAPTCHA solving libraries
```

### Step 4: Migrate Datasets API v2 to v3

```typescript
// BEFORE: Datasets API v2
const v2Response = await fetch(
  `https://api.brightdata.com/dca/trigger?collector=${collectorId}`,
  { method: 'POST', headers: { 'Authorization': `Bearer ${TOKEN}` }, body: JSON.stringify(input) }
);

// AFTER: Datasets API v3 (current)
const v3Response = await fetch(
  `https://api.brightdata.com/datasets/v3/trigger?dataset_id=${datasetId}&format=json`,
  { method: 'POST', headers: { 'Authorization': `Bearer ${TOKEN}`, 'Content-Type': 'application/json' }, body: JSON.stringify(input) }
);
// Changes: /dca/trigger → /datasets/v3/trigger, collector → dataset_id
// v3 adds: format parameter, webhook delivery, snapshot status polling
```

### Step 5: Migration Checklist

```bash
# Create migration branch
git checkout -b migrate/brightdata-zone-upgrade

# Update environment variables
# OLD
BRIGHTDATA_ZONE=residential1
# NEW
BRIGHTDATA_ZONE=web_unlocker1
BRIGHTDATA_ZONE_PASSWORD=new_password

# Test against staging
BRIGHTDATA_ZONE=web_unlocker1_staging npm test

# Verify scraping still works
npm run scrape -- --url https://example.com --dry-run
```

## Rollback Procedure

```bash
# Keep old zone active during migration window
# Rollback = switch BRIGHTDATA_ZONE back to old zone name
export BRIGHTDATA_ZONE=old_zone_name
export BRIGHTDATA_ZONE_PASSWORD=old_password
```

## Output

- Updated zone configuration
- Migrated proxy code to new endpoints
- Passing test suite against new zone
- Old zone kept active for rollback

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 407 after migration | New zone password not set | Update BRIGHTDATA_ZONE_PASSWORD |
| Different response format | Zone type changed | Update response parsing |
| Higher latency | Web Unlocker overhead | Expected; CAPTCHA solving takes time |
| Missing data fields | API v3 schema change | Update TypeScript interfaces |

## Resources

- [Web Unlocker Migration](https://docs.brightdata.com/scraping-automation/web-unlocker/overview)
- [Datasets API v3](https://docs.brightdata.com/scraping-automation/web-data-apis/web-scraper-api/trigger-a-collection)
- [Scraping Browser Setup](https://docs.brightdata.com/scraping-automation/scraping-browser/overview)

## Next Steps

For CI integration during upgrades, see `brightdata-ci-integration`.
