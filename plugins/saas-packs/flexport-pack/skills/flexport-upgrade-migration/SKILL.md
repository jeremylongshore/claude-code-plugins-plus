---
name: flexport-upgrade-migration
description: 'Migrate between Flexport API versions (v1 to v2, Logistics API versions).

  Use when upgrading API version headers, handling deprecated endpoints,

  or migrating from legacy Flexport API patterns.

  Trigger: "upgrade flexport", "flexport API version", "flexport migration".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- logistics
- flexport
compatibility: Designed for Claude Code
---
# Flexport Upgrade & Migration

## Overview

Guide for migrating between Flexport API versions. The main API uses `Flexport-Version` header (currently `2`). The Logistics API has dated versions (`2023-10`, `2024-04`). Breaking changes are versioned -- old versions remain available during deprecation windows.

## Prerequisites

- Current vendor release information and an inventory of version headers, endpoints, mappings, consumers, and retention rules.
- Sandbox access, fictional shipment fixtures, a rollback owner, and explicit reconciliation criteria.

## Output

Keep an upgrade receipt listing versions reviewed, affected mappings, sandbox result, canary result, reconciliation evidence, approver, and rollback decision. Exclude commercial documents, addresses, invoice details, and credentials.

## Error Handling

- Classify unexpected response changes as schema, permission, pagination, delivery, or retention failures.
- Stop promotion and restore the prior version/mapping on a mismatch; do not bulk replay live bookings or documents to diagnose it.
- Quarantine failed records by opaque identifier for reviewed reconciliation.

## Examples

Run old and proposed headers against a fictional sandbox shipment, compare only approved schema fields and aggregate results, and test an unauthorized response. If any mapping or access behavior changes unexpectedly, disable the canary and retain the prior path pending review.

## Instructions

### Step 1: Identify Current API Usage

```bash
# Find all Flexport API calls in your codebase
grep -rn "Flexport-Version\|api.flexport.com\|logistics-api.flexport.com" src/ --include="*.ts" --include="*.py"

# Check which version header you're sending
grep -rn "Flexport-Version" src/ --include="*.ts"
```

### Step 2: API v1 to v2 Migration

| Change | v1 | v2 |
|--------|----|----|
| Header | `Flexport-Version: 1` | `Flexport-Version: 2` |
| Response wrapper | `{ "_object": "Shipment", ... }` | `{ "data": { ... } }` |
| Pagination | `{ "next": "/shipments?page=2" }` | `{ "data": { "records": [], "total_count": N } }` |
| Error format | `{ "errors": [...] }` | `{ "error": { "code": "...", "message": "..." } }` |
| Date format | Mixed | ISO 8601 consistently |

```typescript
// v1 pattern (deprecated)
const res = await fetch(`${BASE}/shipments`, { headers: { 'Flexport-Version': '1' } });
const { _object, id, status } = await res.json();

// v2 pattern (current)
const res = await fetch(`${BASE}/shipments`, { headers: { 'Flexport-Version': '2' } });
const { data } = await res.json();
data.records.forEach(s => console.log(s.id, s.status));
```

### Step 3: Logistics API Version Migration

```typescript
// The Logistics API has separate versioned URLs
// Old: https://docs.logistics-api.flexport.com/2023-10/
// New: https://docs.logistics-api.flexport.com/2024-04/

// Check OpenAPI spec for changes
// https://logistics-api.flexport.com/logistics/api/2024-04/documentation/raw
```

### Step 4: Dual-Version Testing

```typescript
// Run both versions in parallel during migration
async function migrateEndpoint(path: string) {
  const [v1Res, v2Res] = await Promise.all([
    fetch(`${BASE}${path}`, { headers: { ...auth, 'Flexport-Version': '1' } }),
    fetch(`${BASE}${path}`, { headers: { ...auth, 'Flexport-Version': '2' } }),
  ]);

  const v1 = await v1Res.json();
  const v2 = await v2Res.json();

  // Compare key fields to verify migration correctness
  console.log('v1 count:', v1.total || 'N/A');
  console.log('v2 count:', v2.data?.total_count || 'N/A');
}
```

## Migration Checklist

- [ ] Update `Flexport-Version` header to `2`
- [ ] Update response parsing from `_object` to `data.records`
- [ ] Update pagination logic for v2 format
- [ ] Update error handling for v2 error format
- [ ] Run test suite against v2 endpoints
- [ ] Deploy to staging and verify
- [ ] Monitor error rates after production deployment

## Resources

- [Flexport API Reference](https://apidocs.flexport.com/)
- [Logistics API Changelog](https://docs.logistics-api.flexport.com/)

## Next Steps

For CI integration during upgrades, see `flexport-ci-integration`.
