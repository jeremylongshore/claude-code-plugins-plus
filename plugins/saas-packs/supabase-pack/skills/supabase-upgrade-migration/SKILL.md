---
name: supabase-upgrade-migration
description: |
  Analyze, plan, and execute Supabase SDK upgrades with breaking change detection.
  Use when upgrading Supabase SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade supabase", "supabase migration",
  "supabase breaking changes", "update supabase SDK", "analyze supabase version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Upgrade & Migration

## Overview
Guide for upgrading Supabase SDK versions and handling breaking changes.

## Prerequisites
- Current Supabase SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

### Step 1: Check Current Version
```bash
npm list @supabase/supabase-js
npm view @supabase/supabase-js version
```

### Step 2: Review Changelog
```bash
open https://github.com/supabase/sdk/releases
```

### Step 3: Create Upgrade Branch
```bash
git checkout -b upgrade/supabase-sdk-vX.Y.Z
npm install @supabase/supabase-js@latest
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
import { Client } from '@supabase/supabase-js';

// After (v2.x)
import { SupabaseClient } from '@supabase/supabase-js';
```

### Configuration Changes
```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new SupabaseClient({
  apiKey: 'xxx',
});
```

### Rollback Procedure
```bash
npm install @supabase/supabase-js@1.x.x --save-exact
```

### Deprecation Handling
```typescript
// Monitor for deprecation warnings in development
if (process.env.NODE_ENV === 'development') {
  process.on('warning', (warning) => {
    if (warning.name === 'DeprecationWarning') {
      console.warn('[Supabase]', warning.message);
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
- [Supabase Changelog](https://github.com/supabase/sdk/releases)
- [Supabase Migration Guide](https://supabase.com/docs/migration)

## Next Steps
For CI integration during upgrades, see `supabase-ci-integration`.