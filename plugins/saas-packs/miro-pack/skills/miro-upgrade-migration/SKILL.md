---
name: miro-upgrade-migration
description: |
  Analyze, plan, and execute Miro SDK upgrades with breaking change detection.
  Use when upgrading Miro SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade miro", "miro migration",
  "miro breaking changes", "update miro SDK", "analyze miro version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, miro]
---

# Miro Upgrade & Migration

## Overview
Guide for upgrading Miro SDK versions and handling breaking changes.

## Prerequisites
- Current Miro SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

### Step 1: Check Current Version
```bash
npm list @miro/sdk
npm view @miro/sdk version
```

### Step 2: Review Changelog
```bash
open https://github.com/miro/sdk/releases
```

### Step 3: Create Upgrade Branch
```bash
git checkout -b upgrade/miro-sdk-vX.Y.Z
npm install @miro/sdk@latest
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
import { Client } from '@miro/sdk';

// After (v2.x)
import { MiroClient } from '@miro/sdk';
```

### Configuration Changes
```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new MiroClient({
  apiKey: 'xxx',
});
```

### Rollback Procedure
```bash
npm install @miro/sdk@1.x.x --save-exact
```

### Deprecation Handling
```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Miro]', warning.message);
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
- [Miro Changelog](https://github.com/miro/sdk/releases)
- [Miro Migration Guide](https://docs.miro.com/migration)

## Next Steps
For CI integration during upgrades, see `miro-ci-integration`.