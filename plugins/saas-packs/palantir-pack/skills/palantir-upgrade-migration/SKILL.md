---
name: palantir-upgrade-migration
description: |
  Analyze, plan, and execute Palantir SDK upgrades with breaking change detection.
  Use when upgrading Palantir SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade palantir", "palantir migration",
  "palantir breaking changes", "update palantir SDK", "analyze palantir version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, palantir]
---

# Palantir Upgrade & Migration

## Overview
Guide for upgrading Palantir SDK versions and handling breaking changes.

## Prerequisites
- Current Palantir SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

### Step 1: Check Current Version
```bash
npm list @palantir/sdk
npm view @palantir/sdk version
```

### Step 2: Review Changelog
```bash
open https://github.com/palantir/sdk/releases
```

### Step 3: Create Upgrade Branch
```bash
git checkout -b upgrade/palantir-sdk-vX.Y.Z
npm install @palantir/sdk@latest
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
import { Client } from '@palantir/sdk';

// After (v2.x)
import { PalantirClient } from '@palantir/sdk';
```

### Configuration Changes
```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new PalantirClient({
  apiKey: 'xxx',
});
```

### Rollback Procedure
```bash
npm install @palantir/sdk@1.x.x --save-exact
```

### Deprecation Handling
```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Palantir]', warning.message);
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
- [Palantir Changelog](https://github.com/palantir/sdk/releases)
- [Palantir Migration Guide](https://docs.palantir.com/migration)

## Next Steps
For CI integration during upgrades, see `palantir-ci-integration`.