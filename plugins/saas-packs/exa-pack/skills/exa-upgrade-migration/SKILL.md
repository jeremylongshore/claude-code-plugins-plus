---
name: exa-upgrade-migration
description: |
  Analyze, plan, and execute Exa SDK upgrades with breaking change detection.
  Use when upgrading Exa SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade exa", "exa migration",
  "exa breaking changes", "update exa SDK", "analyze exa version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Exa Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Guide for upgrading Exa SDK versions and handling breaking changes.

## Prerequisites
- Current Exa SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

### Step 1: Check Current Version
```bash
set -euo pipefail
npm list @exa/sdk
npm view @exa/sdk version
```

### Step 2: Review Changelog
```bash
open https://github.com/exa/sdk/releases
```

### Step 3: Create Upgrade Branch
```bash
set -euo pipefail
git checkout -b upgrade/exa-sdk-vX.Y.Z
npm install @exa/sdk@latest
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
import { Client } from '@exa/sdk';

// After (v2.x)
import { ExaClient } from '@exa/sdk';
```

### Configuration Changes
```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new ExaClient({
  apiKey: 'xxx',
});
```

### Rollback Procedure
```bash
set -euo pipefail
npm install @exa/sdk@1.x.x --save-exact
```

### Deprecation Handling
```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Exa]', warning.message);
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
- [Exa Changelog](https://github.com/exa/sdk/releases)
- [Exa Migration Guide](https://docs.exa.com/migration)

## Next Steps
For CI integration during upgrades, see `exa-ci-integration`.