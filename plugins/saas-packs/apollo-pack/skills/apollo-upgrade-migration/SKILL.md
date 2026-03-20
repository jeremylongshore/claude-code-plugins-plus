---
name: apollo-upgrade-migration
description: |
  Manage Apollo.io SDK upgrades.
  Use when upgrading Apollo API versions, migrating to new endpoints,
  or updating deprecated API usage.
  Trigger with phrases like "apollo upgrade", "apollo migration",
  "update apollo api", "apollo breaking changes", "apollo deprecation".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Upgrade Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Plan and execute safe upgrades for Apollo.io API integrations. Covers auditing current API usage, building compatibility layers for endpoint changes, feature-flagged rollout, parallel testing, and cleanup procedures.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Audit Current API Usage
```typescript
// src/scripts/api-audit.ts
import { execSync } from 'child_process';

interface EndpointUsage {
  endpoint: string;
  files: string[];
  method: string;
}

function auditApolloUsage(srcDir: string = 'src'): EndpointUsage[] {
  const apolloEndpoints = [
    { pattern: '/people/search', method: 'POST' },
    { pattern: '/people/match', method: 'POST' },
    { pattern: '/organizations/search', method: 'POST' },
    { pattern: '/organizations/enrich', method: 'GET' },
    { pattern: '/contacts', method: 'POST/PUT/DELETE' },
    { pattern: '/emailer_campaigns', method: 'GET/POST' },
    { pattern: '/emailer_steps', method: 'POST' },
    { pattern: '/webhooks', method: 'POST' },
  ];

  const results: EndpointUsage[] = [];

  for (const ep of apolloEndpoints) {
    try {
      const files = execSync(
        `grep -rl "${ep.pattern}" ${srcDir} --include="*.ts" --include="*.js" 2>/dev/null`,
        { encoding: 'utf-8' },
      ).trim().split('\n').filter(Boolean);

      if (files.length > 0) {
        results.push({ endpoint: ep.pattern, files, method: ep.method });
      }
    } catch { /* no matches */ }
  }

  console.log('=== Apollo API Usage Audit ===');
  for (const r of results) {
    console.log(`${r.method} ${r.endpoint}`);
    r.files.forEach((f) => console.log(`  - ${f}`));
  }
  console.log(`\nTotal endpoints used: ${results.length}`);
  return results;
}
```

### Step 2: Build a Compatibility Layer
```typescript
// src/compat/apollo-compat.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://api.apollo.io/v1',
  params: { api_key: process.env.APOLLO_API_KEY },
  headers: { 'Content-Type': 'application/json' },
});

// Map old endpoint signatures to new ones
// Example: if Apollo changes /people/search request format
interface CompatMapping {
  oldField: string;
  newField: string;
  transform?: (value: any) => any;
}

const searchCompat: CompatMapping[] = [
  // Example: Apollo renames a field
  { oldField: 'q_organization_domains', newField: 'organization_domains' },
  { oldField: 'person_titles', newField: 'titles' },
  { oldField: 'per_page', newField: 'page_size' },
];

export function applyCompat(
  body: Record<string, any>,
  mappings: CompatMapping[],
  useNewApi: boolean,
): Record<string, any> {
  if (!useNewApi) return body;  // passthrough when flag is off

  const result = { ...body };
  for (const m of mappings) {
    if (result[m.oldField] !== undefined) {
      result[m.newField] = m.transform
        ? m.transform(result[m.oldField])
        : result[m.oldField];
      delete result[m.oldField];
    }
  }
  return result;
}
```

### Step 3: Implement Feature-Flagged Rollout
```typescript
// src/compat/feature-flags.ts
interface FeatureFlags {
  useNewSearchApi: boolean;
  useNewEnrichApi: boolean;
  useNewSequenceApi: boolean;
}

function getFeatureFlags(): FeatureFlags {
  return {
    useNewSearchApi: process.env.FF_NEW_SEARCH_API === 'true',
    useNewEnrichApi: process.env.FF_NEW_ENRICH_API === 'true',
    useNewSequenceApi: process.env.FF_NEW_SEQUENCE_API === 'true',
  };
}

// Usage in service layer:
export async function searchPeople(body: Record<string, any>) {
  const flags = getFeatureFlags();
  const compatBody = applyCompat(body, searchCompat, flags.useNewSearchApi);
  return client.post('/people/search', compatBody);
}
```

### Step 4: Run Parallel Testing (Shadow Mode)
```typescript
// src/compat/shadow-test.ts
async function shadowTest(
  endpoint: string,
  body: Record<string, any>,
  compatMappings: CompatMapping[],
) {
  // Run both old and new API calls in parallel
  const [oldResult, newResult] = await Promise.allSettled([
    client.post(endpoint, body),
    client.post(endpoint, applyCompat(body, compatMappings, true)),
  ]);

  const comparison = {
    endpoint,
    oldStatus: oldResult.status === 'fulfilled' ? oldResult.value.status : 'error',
    newStatus: newResult.status === 'fulfilled' ? newResult.value.status : 'error',
    resultsMatch: false,
  };

  if (oldResult.status === 'fulfilled' && newResult.status === 'fulfilled') {
    const oldCount = oldResult.value.data.people?.length ?? 0;
    const newCount = newResult.value.data.people?.length ?? 0;
    comparison.resultsMatch = oldCount === newCount;
  }

  console.log(`Shadow test ${endpoint}:`, comparison);
  return comparison;
}

// Run shadow tests against production traffic
// await shadowTest('/people/search', searchParams, searchCompat);
```

### Step 5: Cleanup After Migration
```typescript
// src/scripts/cleanup-compat.ts
async function cleanupCompatLayer(srcDir: string = 'src') {
  const { execSync } = await import('child_process');

  // Find files still using old field names
  const oldPatterns = ['q_organization_domains', 'person_titles', 'per_page'];
  const filesToUpdate: string[] = [];

  for (const pattern of oldPatterns) {
    try {
      const files = execSync(
        `grep -rl "${pattern}" ${srcDir} --include="*.ts" 2>/dev/null`,
        { encoding: 'utf-8' },
      ).trim().split('\n').filter(Boolean);
      filesToUpdate.push(...files);
    } catch { /* no matches */ }
  }

  const uniqueFiles = [...new Set(filesToUpdate)];
  console.log('=== Compat Cleanup ===');
  console.log(`Files still using old API patterns: ${uniqueFiles.length}`);
  uniqueFiles.forEach((f) => console.log(`  - ${f}`));
  console.log('\nAfter updating these files, remove:');
  console.log('  - src/compat/apollo-compat.ts');
  console.log('  - Feature flag environment variables (FF_NEW_*)');
}
```

## Output
- API usage audit script scanning codebase for all Apollo endpoint references
- Compatibility layer mapping old request fields to new ones
- Feature-flagged rollout controlled by environment variables
- Shadow testing utility running old and new APIs in parallel
- Post-migration cleanup script identifying remaining old patterns

## Error Handling
| Issue | Resolution |
|-------|------------|
| Audit finds unknown endpoints | Check Apollo API changelog for deprecation notices |
| Compat layer fails | Verify field mappings match actual API changes |
| Shadow test results differ | Investigate API response format changes |
| Canary deployment issues | Disable feature flag immediately (`FF_*=false`) |

## Examples

### Step-by-Step Upgrade Process
```bash
# 1. Audit current usage
npx tsx src/scripts/api-audit.ts

# 2. Deploy with feature flags OFF (compat layer ready but inactive)
FF_NEW_SEARCH_API=false npm start

# 3. Enable shadow testing in staging
FF_NEW_SEARCH_API=true NODE_ENV=staging npm start
# Monitor logs for shadow test results

# 4. Enable in production (canary 10%)
FF_NEW_SEARCH_API=true npm start  # on 1 of 10 instances

# 5. Full rollout and cleanup
FF_NEW_SEARCH_API=true  # on all instances
npx tsx src/scripts/cleanup-compat.ts
```

## Resources
- [Apollo API Changelog](https://apolloio.github.io/apollo-api-docs/#changelog)
- [Feature Flag Best Practices](https://martinfowler.com/articles/feature-toggles.html)
- [Canary Deployment Pattern](https://martinfowler.com/bliki/CanaryRelease.html)

## Next Steps
Proceed to `apollo-ci-integration` for CI/CD setup.
