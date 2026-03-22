---
name: flyio-upgrade-migration
description: |
  Analyze, plan, and execute Fly.io SDK upgrades with breaking change detection.
  Use when upgrading Fly.io SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade flyio", "flyio migration",
  "flyio breaking changes", "update flyio SDK", "analyze flyio version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flyio]
---

# Fly.io Upgrade & Migration

## Overview
Guide for upgrading Fly.io SDK versions and handling breaking changes.

## Prerequisites
- Current Fly.io SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

### Step 1: Check Current Version
```bash
npm list @flyio/sdk
npm view @flyio/sdk version
```

### Step 2: Review Changelog
```bash
open https://github.com/flyio/sdk/releases
```

### Step 3: Create Upgrade Branch
```bash
git checkout -b upgrade/flyio-sdk-vX.Y.Z
npm install @flyio/sdk@latest
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
import { Client } from '@flyio/sdk';

// After (v2.x)
import { Fly.ioClient } from '@flyio/sdk';
```

### Configuration Changes
```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new Fly.ioClient({
  apiKey: 'xxx',
});
```

### Rollback Procedure
```bash
npm install @flyio/sdk@1.x.x --save-exact
```

### Deprecation Handling
```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Fly.io]', warning.message);
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
- [Fly.io Changelog](https://github.com/flyio/sdk/releases)
- [Fly.io Migration Guide](https://docs.flyio.com/migration)

## Next Steps
For CI integration during upgrades, see `flyio-ci-integration`.