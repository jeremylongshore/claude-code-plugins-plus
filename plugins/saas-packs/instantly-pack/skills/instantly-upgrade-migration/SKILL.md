---
name: instantly-upgrade-migration
description: |
  Analyze, plan, and execute Instantly SDK upgrades with breaking change detection.
  Use when upgrading Instantly SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade instantly", "instantly migration",
  "instantly breaking changes", "update instantly SDK", "analyze instantly version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Instantly Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Guide for upgrading Instantly SDK versions and handling breaking changes.

## Prerequisites
- Current Instantly SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

### Step 1: Check Current Version
```bash
set -euo pipefail
npm list @instantly/sdk
npm view @instantly/sdk version
```

### Step 2: Review Changelog
```bash
open https://github.com/instantly/sdk/releases
```

### Step 3: Create Upgrade Branch
```bash
set -euo pipefail
git checkout -b upgrade/instantly-sdk-vX.Y.Z
npm install @instantly/sdk@latest
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
import { Client } from '@instantly/sdk';

// After (v2.x)
import { InstantlyClient } from '@instantly/sdk';
```

### Configuration Changes
```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new InstantlyClient({
  apiKey: 'xxx',
});
```

### Rollback Procedure
```bash
set -euo pipefail
npm install @instantly/sdk@1.x.x --save-exact
```

### Deprecation Handling
```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Instantly]', warning.message);
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
- [Instantly Changelog](https://github.com/instantly/sdk/releases)
- [Instantly Migration Guide](https://docs.instantly.com/migration)

## Next Steps
For CI integration during upgrades, see `instantly-ci-integration`.