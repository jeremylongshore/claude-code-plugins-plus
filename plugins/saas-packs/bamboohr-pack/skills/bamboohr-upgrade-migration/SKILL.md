---
name: bamboohr-upgrade-migration
description: |
  Plan and execute BambooHR API migration with breaking change detection.
  Use when BambooHR announces API changes, adapting to deprecated endpoints,
  or migrating from legacy API patterns to current best practices.
  Trigger with phrases like "upgrade bamboohr", "bamboohr migration",
  "bamboohr breaking changes", "bamboohr API update", "bamboohr deprecated".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, migration]
compatible-with: claude-code
---

# BambooHR Upgrade & Migration

## Overview

Guide for handling BambooHR API changes, migrating from legacy patterns, and proactively detecting deprecations. BambooHR's API is versioned at v1 — breaking changes are announced on their changelog rather than through version bumps.

## Prerequisites

- Current BambooHR integration working
- Access to BambooHR API changelog
- Git for version control
- Test suite available

## Instructions

### Step 1: Check for Announced Changes

```bash
# Monitor BambooHR's official changelog pages
echo "Check these URLs before any migration work:"
echo "  Past changes:    https://documentation.bamboohr.com/docs/past-changes-to-the-api"
echo "  Planned changes: https://documentation.bamboohr.com/docs/planned-changes-to-the-api"
echo "  Status page:     https://status.bamboohr.com"
```

### Step 2: Common Migration Patterns

#### URL Format Migration

BambooHR has used two base URL formats historically:

```typescript
// Legacy format (still works)
const LEGACY = `https://api.bamboohr.com/api/gateway.php/${domain}/v1`;

// Modern format (equivalent)
const MODERN = `https://${domain}.bamboohr.com/api/v1`;

// Migration: both work, but use the gateway.php format for API key auth
// The modern format is used for browser-based OAuth flows
```

#### XML to JSON Migration

```typescript
// Legacy: XML responses (default if no Accept header)
const xmlRes = await fetch(`${BASE}/employees/directory`, {
  headers: { Authorization: AUTH },
  // No Accept header — returns XML
});

// Current: JSON responses (always set Accept header)
const jsonRes = await fetch(`${BASE}/employees/directory`, {
  headers: { Authorization: AUTH, Accept: 'application/json' },
});

// Migration checklist:
// - Add 'Accept: application/json' to ALL requests
// - Replace XML parsing with JSON.parse
// - Update response type definitions
```

#### Employee Endpoint Changes

```typescript
// Legacy: using employee ID 0 for "current user"
// GET /employees/0/?fields=firstName,lastName
// This returns the employee record for the API key's user

// Current: still works, but prefer explicit employee IDs from directory
const dir = await client.getDirectory();
const currentUser = dir.employees.find(e => e.workEmail === knownEmail);
```

### Step 3: Detect Deprecated Field Usage

```typescript
// Scan your codebase for BambooHR field references
const DEPRECATED_FIELDS = [
  // As of 2025, these field aliases may change:
  'bestEmail',       // Use 'workEmail' or 'homeEmail' explicitly
  'fullName1',       // Use 'displayName' instead
  'fullName2',       // Use firstName + lastName
  'fullName3',       // Removed
  'fullName4',       // Removed
  'fullName5',       // Removed
];

const CURRENT_FIELD_MAPPING: Record<string, string> = {
  'bestEmail': 'workEmail',
  'fullName1': 'displayName',
  'fullName2': 'displayName',  // Or construct from firstName + lastName
};

function migrateFieldName(oldField: string): string {
  if (DEPRECATED_FIELDS.includes(oldField)) {
    const replacement = CURRENT_FIELD_MAPPING[oldField];
    console.warn(`Deprecated field '${oldField}' — use '${replacement}' instead`);
    return replacement || oldField;
  }
  return oldField;
}
```

### Step 4: Migration Testing Strategy

```typescript
// tests/migration/bamboohr-compat.test.ts
import { describe, it, expect } from 'vitest';

describe('BambooHR API Compatibility', () => {
  it('should handle both old and new field names', async () => {
    const emp = await client.getEmployee(testId, [
      'displayName', 'firstName', 'lastName', 'workEmail',
    ]);

    // Verify current fields work
    expect(emp.displayName).toBeTruthy();
    expect(emp.workEmail).toBeTruthy();
  });

  it('should handle null fields gracefully', async () => {
    // BambooHR may return null for newly added fields
    const emp = await client.getEmployee(testId, [
      'firstName', 'lastName', 'supervisor', 'division',
    ]);

    // These may be null/empty for some employees
    expect(emp.firstName).toBeTruthy();
    expect(emp.supervisor).toBeDefined(); // null is valid
  });

  it('should handle table schema changes', async () => {
    const jobInfo = await client.getTableRows(testId, 'jobInfo');

    // Verify required columns still present
    if (jobInfo.length > 0) {
      const row = jobInfo[0];
      expect(row).toHaveProperty('date');
      expect(row).toHaveProperty('jobTitle');
    }
  });
});
```

### Step 5: Gradual Migration with Feature Flags

```typescript
interface MigrationConfig {
  useNewEndpoint: boolean;
  useNewFieldNames: boolean;
  enableNewWebhookFormat: boolean;
}

const MIGRATION_FLAGS: MigrationConfig = {
  useNewEndpoint: process.env.BAMBOOHR_USE_NEW_ENDPOINT === 'true',
  useNewFieldNames: true,       // Already migrated
  enableNewWebhookFormat: false, // Testing in staging
};

async function getEmployeeData(id: string): Promise<Record<string, string>> {
  const fields = MIGRATION_FLAGS.useNewFieldNames
    ? ['displayName', 'workEmail', 'jobTitle']
    : ['bestEmail', 'fullName1', 'jobTitle']; // Legacy

  return client.getEmployee(id, fields);
}
```

### Step 6: Rollback Procedure

```bash
#!/bin/bash
# If migration causes issues:

# 1. Revert to previous code
git revert HEAD --no-edit

# 2. Deploy previous version
# (use your deployment tool)

# 3. Verify old API patterns still work
curl -s -u "${BAMBOOHR_API_KEY}:x" \
  -H "Accept: application/json" \
  "${BASE}/employees/directory" | jq '.employees | length'

echo "Rollback complete. Document what failed for next attempt."
```

## Output

- Identified deprecated fields and endpoints
- Migration code with backward compatibility
- Compatibility test suite
- Feature-flagged gradual migration
- Documented rollback procedure

## Error Handling

| Migration Issue | Detection | Solution |
|----------------|-----------|----------|
| Deprecated field returns null | Runtime null checks | Map to replacement field |
| Endpoint returns 404 | HTTP status monitoring | Check BambooHR changelog |
| Response schema changed | Zod validation failure | Update schema definitions |
| New required fields | 400 on create/update | Add required fields to payload |

## Resources

- [BambooHR Past API Changes](https://documentation.bamboohr.com/docs/past-changes-to-the-api)
- [BambooHR Planned API Changes](https://documentation.bamboohr.com/docs/planned-changes-to-the-api)
- [BambooHR Field Names](https://documentation.bamboohr.com/docs/list-of-field-names)

## Next Steps

For CI integration during upgrades, see `bamboohr-ci-integration`.
