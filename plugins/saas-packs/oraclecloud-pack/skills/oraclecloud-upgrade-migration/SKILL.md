---
name: oraclecloud-upgrade-migration
description: |
  Analyze, plan, and execute Oracle Cloud SDK upgrades with breaking change detection.
  Use when upgrading Oracle Cloud SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade oraclecloud", "oraclecloud migration",
  "oraclecloud breaking changes", "update oraclecloud SDK", "analyze oraclecloud version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, oraclecloud]
---

# Oracle Cloud Upgrade & Migration

## Overview
Guide for upgrading Oracle Cloud SDK versions and handling breaking changes.

## Prerequisites
- Current Oracle Cloud SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

### Step 1: Check Current Version
```bash
npm list @oraclecloud/sdk
npm view @oraclecloud/sdk version
```

### Step 2: Review Changelog
```bash
open https://github.com/oraclecloud/sdk/releases
```

### Step 3: Create Upgrade Branch
```bash
git checkout -b upgrade/oraclecloud-sdk-vX.Y.Z
npm install @oraclecloud/sdk@latest
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
import { Client } from '@oraclecloud/sdk';

// After (v2.x)
import { OracleCloudClient } from '@oraclecloud/sdk';
```

### Configuration Changes
```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new OracleCloudClient({
  apiKey: 'xxx',
});
```

### Rollback Procedure
```bash
npm install @oraclecloud/sdk@1.x.x --save-exact
```

### Deprecation Handling
```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Oracle Cloud]', warning.message);
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
- [Oracle Cloud Changelog](https://github.com/oraclecloud/sdk/releases)
- [Oracle Cloud Migration Guide](https://docs.oraclecloud.com/migration)

## Next Steps
For CI integration during upgrades, see `oraclecloud-ci-integration`.