---
name: apollo-upgrade-migration
description: 'Manage Apollo.io API upgrades and endpoint migrations.

  Use when upgrading Apollo API versions, migrating to new endpoints,

  or updating deprecated API usage.

  Trigger with phrases like "apollo upgrade", "apollo migration",

  "update apollo api", "apollo breaking changes", "apollo deprecation".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.13.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- apollo
- api
- migration
compatibility: Designed for Claude Code
---
# Apollo Upgrade Migration

## Current State

!`npm list axios 2>/dev/null | head -5`

## Overview

Plan and execute safe upgrades for Apollo.io API integrations. Apollo has made several breaking changes historically (query param auth to header auth, endpoint URL changes, new search endpoints). This covers auditing current usage, building compatibility layers, and migrating safely.

## Prerequisites

- Valid Apollo API key
- Node.js 18+

## Instructions

### Step 1: Audit Current API Usage

```typescript
// src/scripts/api-audit.ts
import { execSync } from 'child_process';

interface EndpointUsage { endpoint: string; files: string[]; status: 'current' | 'deprecated'; }

const ENDPOINT_MAP = [
  // Current endpoints
  { pattern: '/mixed_people/api_search', status: 'current' as const },
  { pattern: '/mixed_companies/search', status: 'current' as const },
  { pattern: '/people/match', status: 'current' as const },
  { pattern: '/people/bulk_match', status: 'current' as const },
  { pattern: '/organizations/enrich', status: 'current' as const },
  { pattern: '/contacts/search', status: 'current' as const },
  { pattern: '/emailer_campaigns', status: 'current' as const },
  { pattern: '/email_accounts', status: 'current' as const },
  { pattern: '/opportunities', status: 'current' as const },
  // Deprecated patterns
  { pattern: '/people/search', status: 'deprecated' as const },  // old search endpoint
  { pattern: '/organizations/search', status: 'deprecated' as const },
  { pattern: 'api_key.*=', status: 'deprecated' as const },  // query param auth
  { pattern: 'api.apollo.io/v1', status: 'deprecated' as const },  // old base URL (should be /api/v1)
];

function auditUsage(srcDir: string = 'src'): EndpointUsage[] {
  const results: EndpointUsage[] = [];
  for (const ep of ENDPOINT_MAP) {
    try {
      const files = execSync(
        `grep -rl "${ep.pattern}" ${srcDir} --include="*.ts" --include="*.js" 2>/dev/null`,
        { encoding: 'utf-8' },
      ).trim().split('\n').filter(Boolean);
      if (files.length > 0) results.push({ endpoint: ep.pattern, files, status: ep.status });
    } catch { /* no matches */ }
  }

  console.log('=== Apollo API Usage Audit ===');
  for (const r of results) {
    const icon = r.status === 'deprecated' ? 'WARN' : 'OK';
    console.log(`${icon} ${r.endpoint} (${r.files.length} files)`);
    r.files.forEach((f) => console.log(`     ${f}`));
  }
  const deprecated = results.filter((r) => r.status === 'deprecated');
  if (deprecated.length > 0) {
    console.log(`\n${deprecated.length} deprecated pattern(s) found — migration needed`);
  }
  return results;
}
```

### Step 2: Migration Map — Old to New

```typescript
// src/migration/apollo-migration-map.ts
interface MigrationRule {
  description: string;
  find: string | RegExp;
  replace: string;
  breaking: boolean;
}

const MIGRATION_RULES: MigrationRule[] = [
  // Auth: query param -> header
  {
    description: 'Move API key from query param to x-api-key header',
    find: /params:\s*\{[^}]*api_key[^}]*\}/g,
    replace: "headers: { 'x-api-key': process.env.APOLLO_API_KEY! }",
    breaking: true,
  },
  // Base URL
  {
    description: 'Update base URL from /v1 to /api/v1',
    find: 'api.apollo.io/v1',
    replace: 'api.apollo.io/api/v1',
    breaking: true,
  },
  // People Search endpoint
  {
    description: 'Migrate people search to new endpoint',
    find: '/people/search',
    replace: '/mixed_people/api_search',
    breaking: true,
  },
  // People Search parameters
  {
    description: 'Rename q_organization_domains to q_organization_domains_list',
    find: 'q_organization_domains:',
    replace: 'q_organization_domains_list:',
    breaking: false,
  },
  // Organization Search endpoint
  {
    description: 'Migrate org search to new endpoint',
    find: '/organizations/search',
    replace: '/mixed_companies/search',
    breaking: true,
  },
];
```

### Step 3: Build a Feature-Flagged Migration

```typescript
// src/migration/feature-flags.ts
const flags = {
  useNewSearchEndpoint: process.env.FF_NEW_SEARCH === 'true',
};

export function getSearchEndpoint(): string {
  return flags.useNewSearchEndpoint ? '/mixed_people/api_search' : '/people/search';
}

export function getBaseUrl(): string {
  return 'https://api.apollo.io/api/v1';
}

export function getAuthConfig(): Record<string, any> {
  // Header authentication is mandatory in every migration state.
  return { headers: { 'x-api-key': process.env.APOLLO_API_KEY! } };
}
```

### Step 4: Run Parallel Comparison

```typescript
function compareRecordedResponses(oldFixture: { people?: unknown[] }, newFixture: { people?: unknown[] }) {
  const oldCount = oldFixture.people?.length ?? 0;
  const newCount = newFixture.people?.length ?? 0;
  return { oldCount, newCount, countsMatch: oldCount === newCount };
}
```

Capture the fixture once from an authorized staging request, redact contact
data, and run the comparison offline. Do not keep a production key or a
query-string authentication path alive merely to compare a deprecated endpoint.

### Step 5: Post-Migration Cleanup

```bash
# Find remaining deprecated patterns
grep -rn "api.apollo.io/v1[^/]" src/ --include="*.ts" || echo "No old base URL found"
grep -rn "api_key.*=" src/ --include="*.ts" | grep -v "x-api-key" || echo "No query param auth found"
grep -rn "/people/search" src/ --include="*.ts" | grep -v "mixed_people" || echo "No old search endpoint found"

echo "Cleanup complete. Remove feature flags: FF_NEW_SEARCH, FF_HEADER_AUTH, FF_NEW_BASE_URL"
```

## Output

- API usage audit identifying current and deprecated patterns
- Migration rule map for auth, base URL, and endpoint changes
- Feature-flagged migration with environment variable controls
- Offline fixture comparison for checking old vs new API response contracts
- Post-migration cleanup script

## Examples

For an endpoint migration, inventory deprecated calls, add the new endpoint
behind a staging-only feature flag, and compare its result shape with a
redacted recorded fixture rather than replaying a live legacy request. Keep
header authentication and the current base URL mandatory throughout the change.
After the new path meets the agreed count and field-contract checks, promote it
gradually, monitor error and credit signals, then delete the legacy route and
all migration flags. If the comparison diverges, an audit finds query-string
auth, or a rollback would restore an insecure credential path, halt and repair
the migration before release.

## Error Handling

| Issue | Resolution |
|-------|------------|
| Audit finds deprecated patterns | Apply migration rules file by file |
| Shadow test results differ | Check parameter name changes (e.g., `q_organization_domains` vs `_list`) |
| Feature flag issues | Disable flag immediately (`FF_*=false`) |
| Old endpoints still work | Apollo maintains backward compatibility, but migrate proactively |

## Resources

- [Apollo API Documentation](https://docs.apollo.io/)
- [Apollo API Overview](https://docs.apollo.io/docs/api-overview)
- [Authentication Reference](https://docs.apollo.io/reference/authentication)

## Next Steps

Proceed to `apollo-ci-integration` for CI/CD setup.
