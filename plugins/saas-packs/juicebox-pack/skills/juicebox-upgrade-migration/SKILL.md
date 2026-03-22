---
name: juicebox-upgrade-migration
description: |
  Analyze, plan, and execute Juicebox SDK upgrades with breaking change detection.
  Use when upgrading Juicebox SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade juicebox", "juicebox migration",
  "juicebox breaking changes", "update juicebox SDK", "analyze juicebox version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, juicebox]
---

# Juicebox Upgrade & Migration

## Overview
Guide for upgrading Juicebox SDK versions and handling breaking changes.

## Prerequisites
- Current Juicebox SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

### Step 1: Check Current Version
```bash
npm list @juicebox/sdk
npm view @juicebox/sdk version
```

### Step 2: Review Changelog
```bash
open https://github.com/juicebox/sdk/releases
```

### Step 3: Create Upgrade Branch
```bash
git checkout -b upgrade/juicebox-sdk-vX.Y.Z
npm install @juicebox/sdk@latest
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
import { Client } from '@juicebox/sdk';

// After (v2.x)
import { JuiceboxClient } from '@juicebox/sdk';
```

### Configuration Changes
```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new JuiceboxClient({
  apiKey: 'xxx',
});
```

### Rollback Procedure
```bash
npm install @juicebox/sdk@1.x.x --save-exact
```

### Deprecation Handling
```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Juicebox]', warning.message);
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
- [Juicebox Changelog](https://github.com/juicebox/sdk/releases)
- [Juicebox Migration Guide](https://docs.juicebox.com/migration)

## Next Steps
For CI integration during upgrades, see `juicebox-ci-integration`.