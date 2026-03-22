---
name: brightdata-ci-integration
description: |
  Configure Bright Data CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Bright Data tests into your build process.
  Trigger with phrases like "brightdata CI", "brightdata GitHub Actions",
  "brightdata automated tests", "CI brightdata".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data CI Integration

## Overview

Set up CI/CD pipelines for Bright Data scraping projects with GitHub Actions. Includes mocked unit tests that run without proxy access and optional live integration tests that verify actual proxy connectivity.

## Prerequisites

- GitHub repository with Actions enabled
- Bright Data test zone credentials
- npm/pnpm project configured

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/scraper-tests.yml
name: Scraper Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
        # Unit tests use mocked proxy responses — no credentials needed

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      BRIGHTDATA_CUSTOMER_ID: ${{ secrets.BRIGHTDATA_CUSTOMER_ID }}
      BRIGHTDATA_ZONE: ${{ secrets.BRIGHTDATA_ZONE }}
      BRIGHTDATA_ZONE_PASSWORD: ${{ secrets.BRIGHTDATA_ZONE_PASSWORD }}
      BRIGHTDATA_API_TOKEN: ${{ secrets.BRIGHTDATA_API_TOKEN }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Download Bright Data CA cert
        run: curl -sO https://brightdata.com/ssl/brd-ca.crt
      - name: Verify proxy connectivity
        run: |
          curl -x "http://brd-customer-${BRIGHTDATA_CUSTOMER_ID}-zone-${BRIGHTDATA_ZONE}:${BRIGHTDATA_ZONE_PASSWORD}@brd.superproxy.io:33335" \
            -s https://lumtest.com/myip.json | python3 -m json.tool
      - run: npm run test:integration
```

### Step 2: Configure GitHub Secrets

```bash
gh secret set BRIGHTDATA_CUSTOMER_ID --body "c_abc123"
gh secret set BRIGHTDATA_ZONE --body "web_unlocker_test"
gh secret set BRIGHTDATA_ZONE_PASSWORD --body "z_test_password"
gh secret set BRIGHTDATA_API_TOKEN --body "test_api_token"
```

### Step 3: Write Mocked Unit Tests

```typescript
// tests/unit/scraper.test.ts — runs without Bright Data credentials
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

vi.mock('axios');

describe('Scraper', () => {
  beforeEach(() => vi.clearAllMocks());

  it('should configure proxy correctly', async () => {
    vi.mocked(axios.create).mockReturnValue({
      get: vi.fn().mockResolvedValue({ status: 200, data: '<html>OK</html>' }),
    } as any);

    const { getBrightDataClient } = await import('../../src/brightdata/client');
    const client = getBrightDataClient();

    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        proxy: expect.objectContaining({ host: 'brd.superproxy.io', port: 33335 }),
      })
    );
  });

  it('should parse HTML response into structured data', async () => {
    const { parseProductPage } = await import('../../src/brightdata/parser');
    const result = parseProductPage('<html><h1>Product</h1><span class="price">$29.99</span></html>');
    expect(result.title).toBe('Product');
    expect(result.price).toBe('$29.99');
  });
});
```

### Step 4: Write Live Integration Tests

```typescript
// tests/integration/proxy.test.ts
import { describe, it, expect } from 'vitest';

const LIVE = process.env.BRIGHTDATA_CUSTOMER_ID && process.env.BRIGHTDATA_ZONE;

describe.skipIf(!LIVE)('Bright Data Live Integration', () => {
  it('should connect through proxy', async () => {
    const { getBrightDataClient } = await import('../../src/brightdata/client');
    const client = getBrightDataClient();
    const res = await client.get('https://lumtest.com/myip.json');
    expect(res.status).toBe(200);
    expect(res.data).toHaveProperty('ip');
    expect(res.data).toHaveProperty('country');
  }, 30000);

  it('should scrape through Web Unlocker', async () => {
    const { getBrightDataClient } = await import('../../src/brightdata/client');
    const client = getBrightDataClient();
    const res = await client.get('https://example.com');
    expect(res.status).toBe(200);
    expect(res.data).toContain('Example Domain');
  }, 60000);
});
```

## Output

- Unit tests run on every PR without proxy credentials
- Integration tests run on main push with live proxy
- GitHub secrets configured securely
- CA certificate downloaded in CI

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Integration tests fail | Missing secrets | Add via `gh secret set` |
| Proxy timeout in CI | Slow CAPTCHA | Increase test timeout to 60s |
| Flaky tests | IP rotation variability | Use `lumtest.com` for stable verification |

## Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Bright Data Status API](https://status.brightdata.com)

## Next Steps

For deployment patterns, see `brightdata-deploy-integration`.
