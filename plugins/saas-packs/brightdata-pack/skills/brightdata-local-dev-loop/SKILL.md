---
name: brightdata-local-dev-loop
description: |
  Configure Bright Data local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Bright Data.
  Trigger with phrases like "brightdata dev setup", "brightdata local development",
  "brightdata dev environment", "develop with brightdata".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for Bright Data scraping projects with mocked proxy responses, cached results, and vitest integration.

## Prerequisites

- Completed `brightdata-install-auth` setup
- Node.js 18+ with npm/pnpm
- brd-ca.crt SSL certificate downloaded

## Instructions

### Step 1: Create Project Structure

```
my-scraper/
├── src/
│   ├── brightdata/
│   │   ├── proxy.ts         # Proxy configuration helper
│   │   ├── scraper.ts       # Scraping functions
│   │   └── cache.ts         # Response caching for dev
│   └── index.ts
├── tests/
│   ├── fixtures/            # Cached HTML responses
│   │   └── example.html
│   └── scraper.test.ts
├── .env.local               # Local credentials (git-ignored)
├── .env.example             # Template for team
├── brd-ca.crt               # Bright Data SSL cert (git-ignored)
└── package.json
```

### Step 2: Build Proxy Configuration Module

```typescript
// src/brightdata/proxy.ts
import 'dotenv/config';

export interface BrightDataProxy {
  host: string;
  port: number;
  auth: { username: string; password: string };
}

export function getProxy(options?: {
  country?: string;
  city?: string;
  session?: string;
}): BrightDataProxy {
  const { BRIGHTDATA_CUSTOMER_ID, BRIGHTDATA_ZONE, BRIGHTDATA_ZONE_PASSWORD } = process.env;
  if (!BRIGHTDATA_CUSTOMER_ID || !BRIGHTDATA_ZONE || !BRIGHTDATA_ZONE_PASSWORD) {
    throw new Error('Missing BRIGHTDATA_* environment variables');
  }

  let username = `brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}`;
  if (options?.country) username += `-country-${options.country}`;
  if (options?.city) username += `-city-${options.city}`;
  if (options?.session) username += `-session-${options.session}`;

  return {
    host: 'brd.superproxy.io',
    port: 33335,
    auth: { username, password: BRIGHTDATA_ZONE_PASSWORD },
  };
}
```

### Step 3: Add Response Cache for Development

```typescript
// src/brightdata/cache.ts — cache scraped pages to avoid burning proxy credits
import { createHash } from 'crypto';
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const CACHE_DIR = join(process.cwd(), '.scrape-cache');

export function getCachedResponse(url: string): string | null {
  const key = createHash('md5').update(url).digest('hex');
  const path = join(CACHE_DIR, `${key}.html`);
  return existsSync(path) ? readFileSync(path, 'utf-8') : null;
}

export function setCachedResponse(url: string, html: string): void {
  mkdirSync(CACHE_DIR, { recursive: true });
  const key = createHash('md5').update(url).digest('hex');
  writeFileSync(join(CACHE_DIR, `${key}.html`), html);
}
```

### Step 4: Configure Testing with Mocked Responses

```typescript
// tests/scraper.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

vi.mock('axios');
const mockedAxios = vi.mocked(axios);

describe('Bright Data Scraper', () => {
  beforeEach(() => vi.clearAllMocks());

  it('should scrape through proxy and return HTML', async () => {
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: '<html><head><title>Test</title></head></html>',
    });

    const { scrape } = await import('../src/brightdata/scraper');
    const html = await scrape('https://example.com');
    expect(html).toContain('<title>Test</title>');

    // Verify proxy was configured
    expect(mockedAxios.get).toHaveBeenCalledWith(
      'https://example.com',
      expect.objectContaining({
        proxy: expect.objectContaining({ host: 'brd.superproxy.io' }),
      }),
    );
  });

  it('should retry on 502 proxy errors', async () => {
    mockedAxios.get
      .mockRejectedValueOnce({ response: { status: 502 } })
      .mockResolvedValueOnce({ status: 200, data: '<html>OK</html>' });

    const { scrapeWithRetry } = await import('../src/brightdata/scraper');
    const html = await scrapeWithRetry('https://example.com');
    expect(html).toContain('OK');
    expect(mockedAxios.get).toHaveBeenCalledTimes(2);
  });
});
```

### Step 5: Package Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "scrape": "tsx src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:live": "BRIGHTDATA_LIVE=1 vitest --testPathPattern=integration"
  }
}
```

## Output

- Proxy config module with geo-targeting support
- Response cache to avoid burning credits during development
- Mocked test suite that doesn't require live proxy access
- Live integration test flag (`BRIGHTDATA_LIVE=1`)

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing BRIGHTDATA_* vars` | No `.env.local` | Copy from `.env.example` |
| Cache stale | Old cached HTML | Delete `.scrape-cache/` directory |
| Mock not working | Import order | Use `vi.mock()` before dynamic imports |
| SSL errors in tests | CA cert path | Tests use mocks, not live proxy |

## Resources

- [Bright Data Proxy Docs](https://docs.brightdata.com/general/account/proxy-infrastructure)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)

## Next Steps

See `brightdata-sdk-patterns` for production-ready code patterns.
