---
name: salesforce-upgrade-migration
description: |
  Analyze, plan, and execute Salesforce API version upgrades and jsforce major version migrations.
  Use when upgrading Salesforce API versions, migrating jsforce v1 to v3,
  or adapting to deprecated API changes.
  Trigger with phrases like "upgrade salesforce", "salesforce API version",
  "jsforce upgrade", "salesforce deprecation", "salesforce version migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(sf:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Upgrade & Migration

## Overview
Guide for upgrading Salesforce API versions (v55.0 to v59.0+), migrating between jsforce major versions, and handling Salesforce seasonal release changes.

## Prerequisites
- Current jsforce or simple-salesforce installed
- Git for version control
- Test suite with Salesforce integration tests
- Sandbox environment for validation

## Instructions

### Step 1: Check Current Versions
```bash
# jsforce version
npm list jsforce

# Current API version in use
node -e "const jsforce = require('jsforce'); const c = new jsforce.Connection({}); console.log('Default API version:', c.version)"

# Available API versions from your org
sf org display --target-org my-org --json | jq '.result.apiVersion'
```

### Step 2: Salesforce API Version Changes

| API Version | Release | Key Changes |
|------------|---------|-------------|
| v59.0 | Winter '24 | Composite Graph improvements, Einstein AI endpoints |
| v58.0 | Summer '23 | Enhanced Bulk API 2.0, Flow API updates |
| v57.0 | Spring '23 | SOQL `TYPEOF` improvements, new standard fields |
| v56.0 | Winter '23 | sObject Collections batch size changes |
| v55.0 | Summer '22 | Retirement of old SOAP API features |

**Salesforce retires API versions periodically.** Versions older than 3 years are typically deprecated. Check [Salesforce Release Notes](https://help.salesforce.com/s/articleView?id=release-notes.salesforce_release_notes.htm) each season.

### Step 3: jsforce Major Version Migration

```typescript
// jsforce v1.x → v2.x/v3.x migration
// Key breaking changes:

// BEFORE (v1.x): Callback-based
import jsforce from 'jsforce';
const conn = new jsforce.Connection();
conn.login(username, password, (err, userInfo) => {
  conn.query('SELECT Id FROM Account', (err, result) => {});
});

// AFTER (v2.x+): Promise-based (still supports callbacks)
import jsforce from 'jsforce';
const conn = new jsforce.Connection();
await conn.login(username, password);
const result = await conn.query('SELECT Id FROM Account');

// BEFORE (v1.x): Bulk API v1
const job = conn.bulk.createJob('Account', 'insert');
const batch = job.createBatch();

// AFTER (v2.x+): Bulk API 2.0
const results = await conn.bulk2.loadAndWaitForResults({
  object: 'Account',
  operation: 'insert',
  input: csvData,
});
```

### Step 4: Update API Version in Code
```typescript
// Pin API version explicitly (recommended for stability)
const conn = new jsforce.Connection({
  loginUrl: process.env.SF_LOGIN_URL,
  version: '59.0', // Pin to specific version
});

// Or use latest (auto-detected from org)
const conn = new jsforce.Connection({
  loginUrl: process.env.SF_LOGIN_URL,
  // version defaults to org's latest
});
```

### Step 5: Create Upgrade Branch and Test
```bash
# Create upgrade branch
git checkout -b upgrade/jsforce-v3

# Upgrade jsforce
npm install jsforce@latest

# Run tests against sandbox
SF_LOGIN_URL=https://test.salesforce.com npm test

# Check for deprecation warnings
npm test 2>&1 | grep -i "deprecat"

# If tests pass, merge
```

### Step 6: Handle Seasonal Release Breaking Changes
```typescript
// Salesforce releases 3 times/year (Spring, Summer, Winter)
// Check release notes for:
// 1. Retired API versions
// 2. Changed field behavior (e.g., field becoming read-only)
// 3. New required fields on standard objects
// 4. Permission model changes

// Query org's supported API versions
const versions = await conn.request('/services/data/');
console.log('Supported versions:', versions.map((v: any) => v.version));
// If your pinned version isn't listed, you must upgrade
```

## Output
- Updated jsforce/simple-salesforce to latest
- API version pinned to current stable release
- Breaking changes identified and resolved
- Test suite passing against sandbox
- Rollback procedure documented

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `UNSUPPORTED_API_VERSION` | API version retired | Upgrade version string in Connection |
| `INVALID_FIELD` after upgrade | Field removed in new version | Check release notes for field changes |
| `MODULE_NOT_FOUND` | Import path changed in jsforce v3 | Update import statements |
| Bulk API errors | v1 vs v2 API mismatch | Migrate to `conn.bulk2` methods |

## Resources
- [Salesforce Release Notes](https://help.salesforce.com/s/articleView?id=release-notes.salesforce_release_notes.htm)
- [jsforce Changelog](https://github.com/jsforce/jsforce/releases)
- [API Version Lifecycle](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_api_versioning.htm)
- [Minimum API Version Retirement](https://help.salesforce.com/s/articleView?id=000381744)

## Next Steps
For CI integration during upgrades, see `salesforce-ci-integration`.
