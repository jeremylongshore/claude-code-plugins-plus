---
name: maintainx-debug-bundle
description: |
  Comprehensive debugging toolkit for MaintainX integrations.
  Use when experiencing complex issues, need detailed logging,
  or troubleshooting integration problems with MaintainX.
  Trigger with phrases like "debug maintainx", "maintainx troubleshoot",
  "maintainx detailed logs", "diagnose maintainx", "maintainx issue".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`echo "API key set: $([ -n "$MAINTAINX_API_KEY" ] && echo 'yes' || echo 'no')"`

## Overview
Complete debugging toolkit for diagnosing and resolving MaintainX integration issues with diagnostic scripts, request logging, and health checks.

## Prerequisites
- MaintainX API access configured
- Node.js 18+ or curl
- `MAINTAINX_API_KEY` environment variable set

## Instructions

### Step 1: Environment Diagnostic Script

```bash
#!/bin/bash
echo "=== MaintainX Debug Report ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Node.js: $(node --version 2>/dev/null || echo 'not installed')"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')"
echo "API key set: $([ -n "$MAINTAINX_API_KEY" ] && echo 'yes (length: '${#MAINTAINX_API_KEY}')' || echo 'NO')"
echo ""

echo "=== API Connectivity ==="
HTTP_CODE=$(curl -s -o /tmp/mx-debug.json -w "%{http_code}" \
  "https://api.getmaintainx.com/v1/users?limit=1" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY")
echo "Auth status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo "Response: $(cat /tmp/mx-debug.json | jq -c '{users: (.users | length)}')"
else
  echo "Error: $(cat /tmp/mx-debug.json | jq -r '.message // .error // "unknown"')"
fi

echo ""
echo "=== DNS Resolution ==="
nslookup api.getmaintainx.com 2>/dev/null | grep -A1 "Name:"

echo ""
echo "=== Response Timing ==="
curl -s -o /dev/null -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" \
  "https://api.getmaintainx.com/v1/users?limit=1" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY"
```

### Step 2: Request/Response Logger

```typescript
// src/debug/request-logger.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

export function createDebugClient(): AxiosInstance {
  const client = axios.create({
    baseURL: 'https://api.getmaintainx.com/v1',
    headers: {
      Authorization: `Bearer ${process.env.MAINTAINX_API_KEY}`,
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  client.interceptors.request.use((config) => {
    const startTime = Date.now();
    (config as any).__startTime = startTime;
    console.log(`[REQ] ${config.method?.toUpperCase()} ${config.url}`);
    if (config.data) console.log('  Body:', JSON.stringify(config.data).slice(0, 200));
    if (config.params) console.log('  Params:', config.params);
    return config;
  });

  // Response interceptor
  client.interceptors.response.use(
    (response) => {
      const duration = Date.now() - (response.config as any).__startTime;
      console.log(`[RES] ${response.status} (${duration}ms)`);
      console.log('  Data keys:', Object.keys(response.data));
      return response;
    },
    (error: AxiosError) => {
      const duration = Date.now() - (error.config as any)?.__startTime;
      console.error(`[ERR] ${error.response?.status || 'NETWORK'} (${duration}ms)`);
      console.error('  Message:', (error.response?.data as any)?.message || error.message);
      console.error('  Headers:', JSON.stringify(error.response?.headers || {}));
      throw error;
    },
  );

  return client;
}
```

### Step 3: API Health Check

```typescript
// src/debug/health-check.ts
interface HealthResult {
  endpoint: string;
  status: 'ok' | 'error';
  statusCode?: number;
  latencyMs: number;
  error?: string;
}

async function healthCheck(apiKey: string): Promise<HealthResult[]> {
  const endpoints = [
    { path: '/users?limit=1', name: 'Users' },
    { path: '/workorders?limit=1', name: 'Work Orders' },
    { path: '/assets?limit=1', name: 'Assets' },
    { path: '/locations?limit=1', name: 'Locations' },
    { path: '/teams?limit=1', name: 'Teams' },
  ];

  const results: HealthResult[] = [];

  for (const ep of endpoints) {
    const start = Date.now();
    try {
      const res = await fetch(`https://api.getmaintainx.com/v1${ep.path}`, {
        headers: { Authorization: `Bearer ${apiKey}` },
      });
      results.push({
        endpoint: ep.name,
        status: res.ok ? 'ok' : 'error',
        statusCode: res.status,
        latencyMs: Date.now() - start,
      });
    } catch (err: any) {
      results.push({
        endpoint: ep.name,
        status: 'error',
        latencyMs: Date.now() - start,
        error: err.message,
      });
    }
  }

  // Print report
  console.log('\n=== MaintainX Health Check ===');
  for (const r of results) {
    const icon = r.status === 'ok' ? 'PASS' : 'FAIL';
    console.log(`  [${icon}] ${r.endpoint}: ${r.statusCode || 'N/A'} (${r.latencyMs}ms)`);
    if (r.error) console.log(`        Error: ${r.error}`);
  }

  return results;
}

// Run: npx tsx src/debug/health-check.ts
healthCheck(process.env.MAINTAINX_API_KEY!);
```

### Step 4: Data Validation Checker

```typescript
// src/debug/validate-data.ts
async function validateWorkOrders(client: any) {
  const { workOrders } = await client.getWorkOrders({ limit: 50 });
  const issues: string[] = [];

  for (const wo of workOrders) {
    if (!wo.title) issues.push(`WO #${wo.id}: missing title`);
    if (wo.status === 'COMPLETED' && !wo.completedAt) {
      issues.push(`WO #${wo.id}: COMPLETED but no completedAt timestamp`);
    }
    if (wo.dueDate && new Date(wo.dueDate) < new Date() && wo.status === 'OPEN') {
      issues.push(`WO #${wo.id}: overdue (due ${wo.dueDate})`);
    }
    if (wo.assignees?.length === 0 && wo.priority === 'HIGH') {
      issues.push(`WO #${wo.id}: HIGH priority but no assignees`);
    }
  }

  console.log(`\n=== Data Validation (${workOrders.length} work orders) ===`);
  if (issues.length === 0) {
    console.log('  All checks passed');
  } else {
    for (const issue of issues) {
      console.log(`  WARNING: ${issue}`);
    }
  }
  return issues;
}
```

### Step 5: Generate Support Bundle

```typescript
// src/debug/support-bundle.ts
import { writeFileSync } from 'fs';

async function generateSupportBundle(client: any) {
  const bundle: Record<string, any> = {
    generated: new Date().toISOString(),
    environment: {
      node: process.version,
      platform: process.platform,
      apiKeyPrefix: process.env.MAINTAINX_API_KEY?.slice(0, 8) + '...',
    },
    health: await healthCheck(process.env.MAINTAINX_API_KEY!),
    sampleData: {
      workOrderCount: (await client.getWorkOrders({ limit: 1 })).workOrders.length,
      assetCount: (await client.getAssets({ limit: 1 })).assets.length,
    },
  };

  const filename = `maintainx-debug-${Date.now()}.json`;
  writeFileSync(filename, JSON.stringify(bundle, null, 2));
  console.log(`Support bundle saved to ${filename}`);
  return filename;
}
```

## Output
- Environment diagnostic report (Node.js version, API key status, connectivity)
- Request/response logging with timing for every API call
- Health check results for all major MaintainX endpoints
- Data validation warnings (overdue WOs, missing assignees, etc.)
- Support bundle JSON file for sharing with MaintainX support

## Error Handling
| Issue | Diagnostic Step | Solution |
|-------|----------------|----------|
| 401 on all endpoints | Run Step 1 diagnostic script | Regenerate API key |
| High latency (> 5s) | Check Step 1 response timing | Verify network, check MaintainX status |
| Intermittent 500s | Enable Step 2 request logger | Report to MaintainX with request IDs |
| Missing data | Run Step 4 data validator | Fix data quality issues, re-sync |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [MaintainX Status Page](https://status.getmaintainx.com)
- [MaintainX Help Center](https://help.getmaintainx.com)

## Next Steps
For rate limit handling, see `maintainx-rate-limits`.

## Examples

**One-liner diagnostic**:

```bash
curl -w "\nHTTP: %{http_code} | Time: %{time_total}s\n" \
  "https://api.getmaintainx.com/v1/users?limit=1" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" | jq .
```
