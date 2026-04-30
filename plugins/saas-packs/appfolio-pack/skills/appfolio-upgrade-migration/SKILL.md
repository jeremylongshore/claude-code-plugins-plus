---
name: appfolio-upgrade-migration
description: 'Migrate between AppFolio API versions and handle endpoint changes.

  Trigger: "appfolio upgrade".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio Upgrade & Migration

## Overview
AppFolio property management integrations depend on versioned REST API endpoints that
evolve with the platform. Upgrades can rename fields on property and tenant objects,
change pagination models, deprecate work-order endpoints, and alter the basic-auth
flow. This skill detects your current API version, maps deprecated response shapes
to replacements, and rolls back automatically if the new version fails.

## Prerequisites
- Current API version prefix documented (e.g., `/api/v1/`)
- Access to the AppFolio API changelog and release notes
- Staging environment with test property and tenant data
- Client ID and secret stored in environment variables
- Existing integration test suite that covers core endpoints

## Instructions
1. Run version detection to compare your active API version against the latest.
2. Review the AppFolio changelog for breaking changes between the two versions.
3. Apply schema migration transforms to property and tenant response objects.
4. Update endpoint URLs from the old version prefix to the new one.
5. Switch pagination from offset to cursor-based if required by the new version.
6. Run the smoke test suite against staging to verify all endpoints respond.
7. Deploy to production with the rollback strategy enabled.
8. Monitor error logs for 410/401 responses indicating missed migration steps.

## Output
After a successful migration the skill produces:
- A `VersionInfo` object confirming current, latest, and deprecated versions
- Transformed property and tenant objects matching the new schema
- Smoke test results for properties, tenants, work orders, and accounting endpoints
- Rollback log entries if any endpoint fell back to the previous version

## Version Detection
```typescript
interface VersionInfo { current: string; latest: string; deprecated: string[]; }

async function detectApiVersion(baseUrl: string, headers: Record<string, string>): Promise<VersionInfo> {
  const res = await fetch(`${baseUrl}/api/status`, { headers });
  const body = await res.json();
  const current = res.headers.get("X-AppFolio-Api-Version") ?? body.api_version;
  const deprecated: string[] = body.deprecated_versions ?? [];
  if (deprecated.includes(current)) {
    console.warn(`Version ${current} is deprecated. Migrate to ${body.latest_version}.`);
  }
  return { current, latest: body.latest_version, deprecated };
}
```

## Schema Migration
```typescript
interface LegacyProperty { address_line1: string; unit_count: number; mgr_id: string; }
interface CurrentProperty { street_address: string; total_units: number; manager_id: string; }

function migrateProperty(old: LegacyProperty): CurrentProperty {
  return { street_address: old.address_line1, total_units: old.unit_count, manager_id: old.mgr_id };
}

interface LegacyTenant { lease_end: string; balance_due: number; }
interface CurrentTenant { lease_expiry_date: string; outstanding_balance: number; }

function migrateTenant(old: LegacyTenant): CurrentTenant {
  return { lease_expiry_date: old.lease_end, outstanding_balance: old.balance_due };
}
```

## Rollback Strategy
```typescript
async function versionAwareRequest(
  baseUrl: string, path: string, headers: Record<string, string>,
  targetVersion: string, fallbackVersion: string
): Promise<any> {
  const res = await fetch(`${baseUrl}/api/${targetVersion}${path}`, { headers });
  if (res.status === 410 || res.status === 404) {
    console.warn(`${targetVersion} rejected; falling back to ${fallbackVersion}`);
    const fallback = await fetch(`${baseUrl}/api/${fallbackVersion}${path}`, { headers });
    if (!fallback.ok) throw new Error(`Fallback failed: ${fallback.status}`);
    return fallback.json();
  }
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}
```

## Examples
```typescript
// Detect version and migrate if needed
const info = await detectApiVersion("https://acme.appfolio.com", authHeaders);
if (info.deprecated.includes(info.current)) {
  const oldProps = await fetchLegacyProperties();
  const migrated = oldProps.map(migrateProperty);
  await smokeTestEndpoints("https://acme.appfolio.com", authHeaders);
}
```

## Error Handling
| Migration Issue | Symptom | Fix |
|---|---|---|
| Deprecated version prefix | `410 Gone` on every request | Update base URL to latest version prefix |
| Renamed property fields | `undefined` values in property sync | Apply `migrateProperty` transform |
| Removed pagination offset | Empty result sets after page one | Switch to cursor-based pagination |
| Auth header rejected | `401 Unauthorized` after upgrade | Regenerate client secret, update env vars |
| Webhook envelope change | Event handler parse errors | Update payload parser for new envelope |

## Resources
- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
- See `appfolio-ci-integration` for post-migration CI validation
