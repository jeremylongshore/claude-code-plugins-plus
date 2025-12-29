---
name: supabase-upgrade-migration
description: |
  Analyze and execute Supabase SDK version upgrades with breaking change migrations.
  Use when updating to a new SDK version or handling deprecations.
  Trigger with phrases like "upgrade supabase", "supabase migration",
  "supabase breaking changes", "update supabase SDK".
allowed-tools: Read, Write, Edit, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Upgrade & Migration

## Overview
Guide for upgrading Supabase SDK versions and handling breaking changes.

## Prerequisites
- Current integration working
- Test suite passing
- Git repository with clean working directory
- Changelog reviewed for target version

## Instructions

### Step 1: Check Current and Available Versions
```bash
# Current installed version
npm list @supabase/supabase-js

# Latest available version
npm view @supabase/supabase-js version

# Check for breaking changes
npm view @supabase/supabase-js changelog
```

### Step 2: Create Upgrade Branch
```bash
git checkout -b upgrade/supabase-sdk-vX.Y.Z
npm install @supabase/supabase-js@latest
npm test
```

### Step 3: Handle Breaking Changes

**Import Changes:**
```typescript
// Before (v1.x)
import { Client } from '@supabase/supabase-js';

// After (v2.x)
import { SupabaseClient } from '@supabase/supabase-js';
```

**Configuration Changes:**
```typescript
// Before (v1.x)
const client = new Client({ key: 'xxx' });

// After (v2.x)
const client = new SupabaseClient({
  apiKey: 'xxx',
  // New required options
});
```

### Step 4: Run Codemods (If Available)
```bash
npx @supabase/codemod --transform v1-to-v2
```

## Output
- SDK upgraded to target version
- All breaking changes addressed
- Test suite passing
- Migration documented for team

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| TypeScript errors | API signature changes | Update method calls per changelog |
| Test failures | Behavior changes | Update tests to match new behavior |
| Runtime errors | Missing config | Add new required configuration |
| Deprecation warnings | Old API usage | Migrate to new API patterns |

## Examples

### Version Compatibility Matrix

| SDK Version | API Version | Node.js | Breaking Changes |
|-------------|-------------|---------|------------------|
| 3.x | 2024-01 | 18+ | Major refactor |
| 2.x | 2023-06 | 16+ | Auth changes |
| 1.x | 2022-01 | 14+ | Initial release |

### Deprecation Handling
```typescript
// Find deprecated usage
const DEPRECATED_PATTERNS = [
  'client.oldMethod',
];

// Suppress warnings during migration (temporary)
process.env.SUPABASE_SUPPRESS_DEPRECATION = 'true';
```

### Rollback Plan
```bash
# Keep old version pinned
npm install @supabase/supabase-js@1.x.x --save-exact

# Document rollback command
echo "Rollback: npm install @supabase/supabase-js@1.x.x"
```

### Migration Checklist
- [ ] Read full changelog for target version
- [ ] Create upgrade branch
- [ ] Update package.json
- [ ] Fix TypeScript compilation errors
- [ ] Update configuration code
- [ ] Fix breaking API changes
- [ ] Run full test suite
- [ ] Test in staging environment
- [ ] Deploy with rollback plan ready
- [ ] Monitor for errors post-deployment

## Resources
- [Supabase Changelog](https://github.com/supabase/sdk/releases)
- [Migration Guide](https://supabase.com/docs/migration)
- [Breaking Changes](https://supabase.com/docs/breaking-changes)

## Next Steps
For CI integration during upgrades, see `supabase-ci-integration`.