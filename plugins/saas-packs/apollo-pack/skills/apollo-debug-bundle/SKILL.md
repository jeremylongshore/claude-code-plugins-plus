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
---
# Apollo Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect comprehensive debug information for Apollo.io API issues to expedite support resolution. Generates a JSON diagnostic bundle with environment info, connectivity tests, rate limit status, and sanitized request/response logs.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Create the Debug Bundle Collector
```typescript
// src/scripts/debug-bundle.ts
import axios from 'axios';
import os from 'os';
import { execSync } from 'child_process';

interface DebugBundle {
  timestamp: string;
  environment: Record<string, string>;
  connectivity: { reachable: boolean; latencyMs: number; statusCode?: number };
  rateLimits: { limit?: number; remaining?: number; usedPercent?: number };
  recentErrors: Array<{ endpoint: string; status: number; message: string }>;
  systemInfo: Record<string, string>;
}

async function collectDebugBundle(): Promise<DebugBundle> {
  const bundle: DebugBundle = {
    timestamp: new Date().toISOString(),
    environment: {},
    connectivity: { reachable: false, latencyMs: 0 },
    rateLimits: {},
    recentErrors: [],
    systemInfo: {},
  };

  // Step 1: Environment check
  bundle.environment = {
    nodeVersion: process.version,
    platform: os.platform(),
    arch: os.arch(),
    apiKeySet: process.env.APOLLO_API_KEY ? 'yes (redacted)' : 'NOT SET',
    apiKeyLength: String(process.env.APOLLO_API_KEY?.length ?? 0),
    baseUrl: process.env.APOLLO_BASE_URL ?? 'https://api.apollo.io/v1 (default)',
  };

  return bundle;
}
```

### Step 2: Test API Connectivity
```typescript
async function testConnectivity(bundle: DebugBundle) {
  const start = Date.now();
  try {
    const response = await axios.post(
      'https://api.apollo.io/v1/people/search',
      { q_organization_domains: ['apollo.io'], per_page: 1 },
      {
        params: { api_key: process.env.APOLLO_API_KEY },
        headers: { 'Content-Type': 'application/json' },
        timeout: 10_000,
      },
    );
    bundle.connectivity = {
      reachable: true,
      latencyMs: Date.now() - start,
      statusCode: response.status,
    };

    // Extract rate limit info
    bundle.rateLimits = {
      limit: parseInt(response.headers['x-rate-limit-limit'] ?? '0', 10),
      remaining: parseInt(response.headers['x-rate-limit-remaining'] ?? '0', 10),
      usedPercent: 0,
    };
    if (bundle.rateLimits.limit) {
      bundle.rateLimits.usedPercent = Math.round(
        ((bundle.rateLimits.limit - (bundle.rateLimits.remaining ?? 0)) / bundle.rateLimits.limit) * 100,
      );
    }
  } catch (err: any) {
    bundle.connectivity = {
      reachable: false,
      latencyMs: Date.now() - start,
      statusCode: err.response?.status,
    };
    bundle.recentErrors.push({
      endpoint: '/people/search',
      status: err.response?.status ?? 0,
      message: err.response?.data?.message ?? err.message,
    });
  }
}
```

### Step 3: Test Key Endpoints
```typescript
async function testEndpoints(bundle: DebugBundle) {
  const endpoints = [
    { method: 'POST', path: '/people/search', body: { per_page: 1 } },
    { method: 'GET', path: '/organizations/enrich', params: { domain: 'apollo.io' } },
    { method: 'GET', path: '/emailer_campaigns' },
  ];

  for (const ep of endpoints) {
    try {
      await axios({
        method: ep.method as any,
        url: `https://api.apollo.io/v1${ep.path}`,
        params: { api_key: process.env.APOLLO_API_KEY, ...ep.params },
        data: ep.body,
        headers: { 'Content-Type': 'application/json' },
        timeout: 10_000,
      });
    } catch (err: any) {
      bundle.recentErrors.push({
        endpoint: ep.path,
        status: err.response?.status ?? 0,
        message: err.response?.data?.message ?? err.message,
      });
    }
  }
}
```

### Step 4: Collect System Information
```typescript
function collectSystemInfo(bundle: DebugBundle) {
  bundle.systemInfo = {
    hostname: os.hostname(),
    platform: `${os.platform()} ${os.release()}`,
    nodeVersion: process.version,
    memory: `${Math.round(os.freemem() / 1024 / 1024)}MB free / ${Math.round(os.totalmem() / 1024 / 1024)}MB total`,
    uptime: `${Math.round(os.uptime() / 3600)}h`,
  };

  try {
    bundle.systemInfo.npmVersion = execSync('npm --version 2>/dev/null').toString().trim();
  } catch { /* ignore */ }

  try {
    bundle.systemInfo.gitBranch = execSync('git branch --show-current 2>/dev/null').toString().trim();
    bundle.systemInfo.gitCommit = execSync('git rev-parse --short HEAD 2>/dev/null').toString().trim();
  } catch { /* ignore */ }
}
```

### Step 5: Generate and Output the Bundle
```typescript
async function main() {
  console.log('Collecting Apollo debug bundle...\n');
  const bundle = await collectDebugBundle();
  await testConnectivity(bundle);
  await testEndpoints(bundle);
  collectSystemInfo(bundle);

  // Write to file
  const fs = await import('fs');
  const filename = `apollo-debug-${Date.now()}.json`;
  fs.writeFileSync(filename, JSON.stringify(bundle, null, 2));

  // Print summary
  console.log('=== Debug Bundle Summary ===');
  console.log(`API Key Set:    ${bundle.environment.apiKeySet}`);
  console.log(`API Reachable:  ${bundle.connectivity.reachable}`);
  console.log(`Latency:        ${bundle.connectivity.latencyMs}ms`);
  console.log(`Rate Limit:     ${bundle.rateLimits.remaining}/${bundle.rateLimits.limit} remaining`);
  console.log(`Errors Found:   ${bundle.recentErrors.length}`);
  console.log(`Bundle saved:   ${filename}`);
  console.log('\nAttach this file to your Apollo support ticket.');
}

main().catch(console.error);
```

## Output
- JSON debug bundle with environment, connectivity, rate limits, and errors
- API connectivity test with latency measurement
- Endpoint-by-endpoint health check (search, enrichment, sequences)
- System info (OS, Node version, git branch/commit)
- Ready-to-attach file for Apollo support tickets

## Error Handling
| Issue | Debug Step |
|-------|------------|
| Connection timeout | Check network/firewall, verify DNS for `api.apollo.io` |
| 401 errors | `apiKeySet` field shows if key is loaded; check length matches dashboard |
| 429 errors | `rateLimits.usedPercent` shows current usage; wait for reset |
| 500 errors | Check [status.apollo.io](https://status.apollo.io) for outages |

## Examples

### Quick CLI Diagnostic
```bash
# One-liner connectivity test
curl -s -w "\nHTTP %{http_code} in %{time_total}s\n" \
  -X POST https://api.apollo.io/v1/people/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$APOLLO_API_KEY\", \"per_page\": 1}" | head -5
```

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support Portal](https://support.apollo.io)
- [Apollo API Documentation](https://apolloio.github.io/apollo-api-docs/)

## Next Steps
Proceed to `apollo-rate-limits` for rate limiting implementation.
