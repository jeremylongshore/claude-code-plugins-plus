---
name: maintainx-upgrade-migration
description: |
  Migrate MaintainX API versions and handle breaking changes.
  Use when upgrading API versions, handling deprecations,
  or migrating between MaintainX API releases.
  Trigger with phrases like "maintainx upgrade", "maintainx api version",
  "maintainx migration", "maintainx breaking changes", "maintainx deprecation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`

## Overview
Handle MaintainX API version upgrades, deprecations, and breaking changes with a safe, incremental migration strategy.

## Prerequisites
- Existing MaintainX integration
- Test environment with separate API key
- Version control (git) for all integration code

## Instructions

### Step 1: Audit Current API Usage

```typescript
// scripts/audit-api-usage.ts
// Scan your codebase for all MaintainX API calls

import { readFileSync, readdirSync, statSync } from 'fs';
import { join } from 'path';

function findApiCalls(dir: string): Array<{ file: string; line: number; endpoint: string }> {
  const results: Array<{ file: string; line: number; endpoint: string }> = [];

  function scan(d: string) {
    for (const entry of readdirSync(d)) {
      const full = join(d, entry);
      if (statSync(full).isDirectory()) {
        if (!entry.startsWith('.') && entry !== 'node_modules') scan(full);
      } else if (full.endsWith('.ts') || full.endsWith('.js')) {
        const content = readFileSync(full, 'utf-8');
        const lines = content.split('\n');
        for (let i = 0; i < lines.length; i++) {
          // Match API endpoint patterns
          const match = lines[i].match(/['"`](\/(?:workorders|assets|locations|users|teams|parts|procedures|webhooks)[^'"`]*)/);
          if (match) {
            results.push({ file: full, line: i + 1, endpoint: match[1] });
          }
        }
      }
    }
  }

  scan(dir);
  return results;
}

const calls = findApiCalls('./src');
console.log('=== MaintainX API Usage Audit ===');
console.log(`Found ${calls.length} API calls:\n`);

// Group by endpoint
const grouped = new Map<string, typeof calls>();
for (const call of calls) {
  const base = call.endpoint.split('?')[0].replace(/\/\d+/, '/:id');
  const existing = grouped.get(base) || [];
  existing.push(call);
  grouped.set(base, existing);
}

for (const [endpoint, usages] of grouped) {
  console.log(`${endpoint} (${usages.length} calls):`);
  for (const u of usages) {
    console.log(`  ${u.file}:${u.line}`);
  }
}
```

### Step 2: Version Compatibility Layer

```typescript
// src/migration/compat.ts

type ApiVersion = 'v1' | 'v2';

interface VersionAdapter {
  baseUrl: string;
  transformRequest(endpoint: string, data: any): { endpoint: string; data: any };
  transformResponse(endpoint: string, data: any): any;
}

const adapters: Record<ApiVersion, VersionAdapter> = {
  v1: {
    baseUrl: 'https://api.getmaintainx.com/v1',
    transformRequest: (endpoint, data) => ({ endpoint, data }),
    transformResponse: (endpoint, data) => data,
  },
  v2: {
    baseUrl: 'https://api.getmaintainx.com/v2',
    transformRequest: (endpoint, data) => {
      // Handle breaking changes in v2
      if (endpoint.startsWith('/workorders') && data) {
        // Example: v2 renamed 'assignees' to 'assignedTo'
        if (data.assignees) {
          data.assignedTo = data.assignees;
          delete data.assignees;
        }
      }
      return { endpoint, data };
    },
    transformResponse: (endpoint, data) => {
      // Normalize v2 response to v1 shape
      if (data.assignedTo) {
        data.assignees = data.assignedTo;
      }
      return data;
    },
  },
};

class VersionedClient {
  private adapter: VersionAdapter;

  constructor(version: ApiVersion = 'v1') {
    this.adapter = adapters[version];
  }

  async request(method: string, endpoint: string, data?: any) {
    const { endpoint: ep, data: d } = this.adapter.transformRequest(endpoint, data);
    const response = await fetch(`${this.adapter.baseUrl}${ep}`, {
      method,
      headers: {
        Authorization: `Bearer ${process.env.MAINTAINX_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: d ? JSON.stringify(d) : undefined,
    });
    const result = await response.json();
    return this.adapter.transformResponse(ep, result);
  }
}
```

### Step 3: Feature Flag Migration

```typescript
// src/migration/feature-flags.ts

const MIGRATION_FLAGS: Record<string, boolean> = {
  USE_V2_WORKORDERS: false,   // Set to true when ready to switch
  USE_V2_ASSETS: false,
  USE_V2_PAGINATION: false,   // v2 might use offset instead of cursor
};

function getApiVersion(endpoint: string): ApiVersion {
  if (endpoint.startsWith('/workorders') && MIGRATION_FLAGS.USE_V2_WORKORDERS) return 'v2';
  if (endpoint.startsWith('/assets') && MIGRATION_FLAGS.USE_V2_ASSETS) return 'v2';
  return 'v1';
}

// Gradually roll out v2 per-endpoint
async function migratedRequest(method: string, endpoint: string, data?: any) {
  const version = getApiVersion(endpoint);
  const client = new VersionedClient(version);
  return client.request(method, endpoint, data);
}
```

### Step 4: Migration Tests

```typescript
// tests/migration.test.ts
import { describe, it, expect } from 'vitest';

describe('API Version Migration', () => {
  it('v1 and v2 return equivalent work order data', async () => {
    const v1Client = new VersionedClient('v1');
    const v2Client = new VersionedClient('v2');

    const v1Result = await v1Client.request('GET', '/workorders?limit=5');
    const v2Result = await v2Client.request('GET', '/workorders?limit=5');

    // After adapter normalization, shapes should match
    expect(v1Result.workOrders.length).toBe(v2Result.workOrders.length);
    expect(v1Result.workOrders[0]).toHaveProperty('id');
    expect(v1Result.workOrders[0]).toHaveProperty('title');
    expect(v1Result.workOrders[0]).toHaveProperty('status');
  });

  it('compatibility adapter transforms assignees correctly', () => {
    const adapter = adapters.v2;
    const { data } = adapter.transformRequest('/workorders', {
      title: 'Test',
      assignees: [{ type: 'USER', id: 1 }],
    });
    expect(data.assignedTo).toBeDefined();
    expect(data.assignees).toBeUndefined();
  });
});
```

### Step 5: Rollback Procedure

```bash
#!/bin/bash
# rollback-api-version.sh
# Revert to v1 API if v2 migration causes issues

echo "=== MaintainX API Version Rollback ==="
echo "1. Set all feature flags to false:"
echo '   MIGRATION_FLAGS.USE_V2_WORKORDERS = false'
echo '   MIGRATION_FLAGS.USE_V2_ASSETS = false'
echo ""
echo "2. Redeploy with v1 configuration:"
echo "   git revert HEAD --no-edit && git push"
echo ""
echo "3. Verify v1 endpoints are working:"
echo '   curl -s https://api.getmaintainx.com/v1/workorders?limit=1 \'
echo '     -H "Authorization: Bearer $MAINTAINX_API_KEY" | jq .status'
echo ""
echo "4. Monitor error rates for 30 minutes"
echo "5. Document issues for v2 retry"
```

## Output
- API usage audit report listing all endpoints and call sites
- Version compatibility layer with request/response adapters
- Feature flag system for incremental per-endpoint migration
- Migration tests verifying v1/v2 equivalence
- Rollback procedure for safe revert

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 404 on v2 endpoint | Endpoint path changed | Update adapter mappings |
| Field missing in v2 response | Breaking schema change | Add field mapping in `transformResponse` |
| Mixed v1/v2 data in DB | Partial migration state | Run reconciliation to normalize |
| Feature flag stuck | Config not reloaded | Restart service or use dynamic config |

## Resources
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html) -- Incremental migration strategy

## Next Steps
For CI/CD integration, see `maintainx-ci-integration`.

## Examples

**Dual-write during migration** (write to both v1 and v2):

```typescript
async function dualWrite(endpoint: string, data: any) {
  const v1 = new VersionedClient('v1');
  const v2 = new VersionedClient('v2');

  const v1Result = await v1.request('POST', endpoint, data);

  try {
    await v2.request('POST', endpoint, data);
  } catch (err) {
    console.warn('v2 write failed (non-blocking):', err);
    // Log for investigation, don't fail the operation
  }

  return v1Result; // v1 is source of truth during migration
}
```
