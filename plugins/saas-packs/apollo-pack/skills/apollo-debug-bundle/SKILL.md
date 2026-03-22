---
name: apollo-debug-bundle
description: |
  Collect Apollo.io debug evidence for support.
  Use when preparing support tickets, documenting issues,
  or gathering diagnostic information for Apollo problems.
  Trigger with phrases like "apollo debug", "apollo support bundle",
  "collect apollo diagnostics", "apollo troubleshooting info".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, debugging]

---
# Apollo Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect comprehensive debug information for Apollo.io API issues. Generates a JSON diagnostic bundle with environment info, connectivity tests, rate limit status, key type verification, and sanitized request/response logs.

## Prerequisites
- `APOLLO_API_KEY` environment variable set
- Node.js 18+ or Python 3.10+

## Instructions

### Step 1: Create the Debug Bundle Collector
```typescript
// src/scripts/debug-bundle.ts
import axios from 'axios';
import os from 'os';

const BASE_URL = 'https://api.apollo.io/api/v1';

interface DebugBundle {
  timestamp: string;
  environment: Record<string, string>;
  connectivity: { reachable: boolean; latencyMs: number; statusCode?: number };
  keyType: 'master' | 'standard' | 'invalid' | 'unknown';
  rateLimits: { limit?: string; remaining?: string; window?: string };
  endpointTests: Array<{ endpoint: string; status: number | string; ok: boolean }>;
  systemInfo: Record<string, string>;
}

async function collectDebugBundle(): Promise<DebugBundle> {
  const headers = {
    'Content-Type': 'application/json',
    'x-api-key': process.env.APOLLO_API_KEY ?? '',
  };

  const bundle: DebugBundle = {
    timestamp: new Date().toISOString(),
    environment: {
      nodeVersion: process.version,
      platform: os.platform(),
      arch: os.arch(),
      apiKeySet: process.env.APOLLO_API_KEY ? 'yes (redacted)' : 'NOT SET',
      apiKeyLength: String(process.env.APOLLO_API_KEY?.length ?? 0),
      apiKeyPrefix: process.env.APOLLO_API_KEY?.slice(0, 4) + '...' ?? 'N/A',
    },
    connectivity: { reachable: false, latencyMs: 0 },
    keyType: 'unknown',
    rateLimits: {},
    endpointTests: [],
    systemInfo: {},
  };

  return bundle;
}
```

### Step 2: Test Connectivity and Key Type
```typescript
async function testConnectivity(bundle: DebugBundle) {
  const headers = { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! };

  // Test basic auth
  const start = Date.now();
  try {
    const resp = await axios.get(`${BASE_URL}/auth/health`, { headers, timeout: 10_000 });
    bundle.connectivity = { reachable: true, latencyMs: Date.now() - start, statusCode: resp.status };
    bundle.keyType = resp.data.is_logged_in ? 'standard' : 'invalid';  // at minimum standard
  } catch (err: any) {
    bundle.connectivity = { reachable: false, latencyMs: Date.now() - start, statusCode: err.response?.status };
    return;
  }

  // Test master key access
  try {
    await axios.post(`${BASE_URL}/contacts/search`, { per_page: 1 }, { headers, timeout: 10_000 });
    bundle.keyType = 'master';
  } catch (err: any) {
    if (err.response?.status === 403) bundle.keyType = 'standard';
  }
}
```

### Step 3: Test Key Endpoints
```typescript
async function testEndpoints(bundle: DebugBundle) {
  const headers = { 'Content-Type': 'application/json', 'x-api-key': process.env.APOLLO_API_KEY! };

  const tests = [
    { name: 'Auth Health', method: 'GET', url: `${BASE_URL}/auth/health` },
    { name: 'People Search', method: 'POST', url: `${BASE_URL}/mixed_people/api_search`,
      body: { per_page: 1, q_organization_domains_list: ['apollo.io'] } },
    { name: 'Org Enrichment', method: 'GET', url: `${BASE_URL}/organizations/enrich?domain=apollo.io` },
    { name: 'Contacts Search', method: 'POST', url: `${BASE_URL}/contacts/search`, body: { per_page: 1 } },
    { name: 'Sequences Search', method: 'POST', url: `${BASE_URL}/emailer_campaigns/search`, body: { per_page: 1 } },
    { name: 'Email Accounts', method: 'GET', url: `${BASE_URL}/email_accounts` },
  ];

  for (const test of tests) {
    try {
      const resp = await axios({ method: test.method as any, url: test.url, data: test.body, headers, timeout: 10_000 });
      bundle.endpointTests.push({ endpoint: test.name, status: resp.status, ok: true });

      // Capture rate limit headers from any successful response
      if (resp.headers['x-rate-limit-limit']) {
        bundle.rateLimits = {
          limit: resp.headers['x-rate-limit-limit'],
          remaining: resp.headers['x-rate-limit-remaining'],
          window: resp.headers['x-rate-limit-window'],
        };
      }
    } catch (err: any) {
      bundle.endpointTests.push({
        endpoint: test.name,
        status: err.response?.status ?? err.code ?? err.message,
        ok: false,
      });
    }
  }
}
```

### Step 4: Generate and Output
```typescript
async function main() {
  console.log('Collecting Apollo debug bundle...\n');
  const bundle = await collectDebugBundle();
  await testConnectivity(bundle);
  await testEndpoints(bundle);

  // System info
  bundle.systemInfo = {
    hostname: os.hostname(),
    platform: `${os.platform()} ${os.release()}`,
    memory: `${Math.round(os.freemem() / 1024 / 1024)}MB free / ${Math.round(os.totalmem() / 1024 / 1024)}MB total`,
  };

  // Write to file
  const fs = await import('fs');
  const filename = `apollo-debug-${Date.now()}.json`;
  fs.writeFileSync(filename, JSON.stringify(bundle, null, 2));

  // Print summary
  console.log('=== Apollo Debug Summary ===');
  console.log(`API Key:     ${bundle.environment.apiKeySet} (${bundle.environment.apiKeyLength} chars)`);
  console.log(`Key Type:    ${bundle.keyType}`);
  console.log(`Reachable:   ${bundle.connectivity.reachable} (${bundle.connectivity.latencyMs}ms)`);
  console.log(`Rate Limit:  ${bundle.rateLimits.remaining ?? '?'}/${bundle.rateLimits.limit ?? '?'} remaining`);
  console.log(`Endpoints:`);
  for (const t of bundle.endpointTests) {
    console.log(`  ${t.ok ? 'OK' : 'FAIL'}  ${t.endpoint}: ${t.status}`);
  }
  console.log(`\nBundle saved: ${filename}`);
}

main().catch(console.error);
```

## Output
- JSON debug bundle with environment, connectivity, key type, rate limits, and endpoint results
- Key type detection (master vs standard vs invalid)
- Endpoint-by-endpoint health check (auth, search, enrichment, contacts, sequences)
- Rate limit header capture
- Ready-to-attach file for Apollo support tickets

## Error Handling
| Issue | Debug Step |
|-------|------------|
| Connection timeout | Check network/firewall, verify DNS for `api.apollo.io` |
| Key type = invalid | Key was revoked — regenerate in Apollo dashboard |
| Key type = standard | Master key needed — check which endpoints fail with 403 |
| All endpoints fail | Check [status.apollo.io](https://status.apollo.io) for outages |

## Examples

### Quick CLI Diagnostic
```bash
# One-liner: test auth + connectivity
curl -s -w "\nHTTP %{http_code} in %{time_total}s\n" \
  -H "x-api-key: $APOLLO_API_KEY" \
  "https://api.apollo.io/api/v1/auth/health"

# Test rate limit headers
curl -s -D - -o /dev/null \
  -H "Content-Type: application/json" -H "x-api-key: $APOLLO_API_KEY" \
  -X POST -d '{"per_page":1,"q_organization_domains_list":["apollo.io"]}' \
  "https://api.apollo.io/api/v1/mixed_people/api_search" 2>/dev/null | grep -i "x-rate"
```

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [API Usage Stats](https://docs.apollo.io/reference/view-api-usage-stats)
- [Apollo Support](https://support.apollo.io)

## Next Steps
Proceed to `apollo-rate-limits` for rate limiting implementation.
