---
name: salesforce-upgrade-migration
description: |
  Analyze, plan, and execute Salesforce SDK upgrades with breaking change detection.
  Use when upgrading Salesforce SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade salesforce", "salesforce migration",
  "salesforce breaking changes", "update salesforce SDK", "analyze salesforce version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesforce]
---

# Salesforce Upgrade & Migration

## Overview
Guide for upgrading Salesforce SDK versions and handling breaking changes.

## Prerequisites
- Current Salesforce SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

### Step 1: Check Current Version
```bash
npm list @salesforce/sdk
npm view @salesforce/sdk version
```

### Step 2: Review Changelog
```bash
open https://github.com/salesforce/sdk/releases
```

### Step 3: Create Upgrade Branch
```bash
git checkout -b upgrade/salesforce-sdk-vX.Y.Z
npm install @salesforce/sdk@latest
npm test
```

### Step 4: Handle Breaking Changes
Update import statements, configuration, and method signatures as needed.

## Output
- Updated SDK version
- Fixed breaking changes
- Passing test suite
- Documented rollback procedure

## Error Handling
| SDK Version | API Version | Node.js | Breaking Changes |
|-------------|-------------|---------|------------------|
| 3.x | 2024-01 | 18+ | Major refactor |
| 2.x | 2023-06 | 16+ | Auth changes |
| 1.x | 2022-01 | 14+ | Initial release |

## Examples

### Import Changes
```typescript
// Before (v1.x)
import { Client } from '@salesforce/sdk';

// After (v2.x)
import { SalesforceClient } from '@salesforce/sdk';
```

### Configuration Changes
```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new SalesforceClient({
  apiKey: 'xxx',
});
```

### Rollback Procedure
```bash
npm install @salesforce/sdk@1.x.x --save-exact
```

### Deprecation Handling
```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Salesforce]', warning.message);
      // Log to tracking system for proactive updates
    }
  });
}

// Common deprecation patterns to watch for:
// - Renamed methods: client.oldMethod() -> client.newMethod()
// - Changed parameters: { key: 'x' } -> { apiKey: 'x' }
// - Removed features: Check release notes before upgrading
```

## Resources
- [Salesforce Changelog](https://github.com/salesforce/sdk/releases)
- [Salesforce Migration Guide](https://docs.salesforce.com/migration)

## Next Steps
For CI integration during upgrades, see `salesforce-ci-integration`.