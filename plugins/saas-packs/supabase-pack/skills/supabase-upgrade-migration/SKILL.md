---
name: supabase-upgrade-migration
description: |
  Supabase SDK upgrades and breaking change migrations.
  Trigger phrases: "upgrade supabase", "supabase migration",
  "supabase breaking changes", "update supabase SDK".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Upgrade & Migration

## Overview
Guide for upgrading Supabase SDK versions and handling breaking changes.

## Version Check

```bash
# Current installed version
npm list @supabase/supabase-js

# Latest available version
npm view @supabase/supabase-js version

# Check for breaking changes
npm view @supabase/supabase-js changelog
```

## Upgrade Procedure

### 1. Review Changelog
```bash
# Check release notes
open https://github.com/supabase/sdk/releases
```

### 2. Test in Isolation
```bash
# Create test branch
git checkout -b upgrade/supabase-sdk-vX.Y.Z

# Update dependency
npm install @supabase/supabase-js@latest

# Run tests
npm test
```

### 3. Handle Breaking Changes

#### Common Migration Patterns

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

**Method Signature Changes:**
```typescript
// Before (v1.x)
client.create(data);

// After (v2.x)
client.create({ data, // New required params });
```

### 4. Codemods (If Available)

```bash
# Run official codemod
npx @supabase/codemod --transform v1-to-v2

# Or use jscodeshift for custom transforms
npx jscodeshift -t supabase-v2-transform.js src/
```

## Deprecation Handling

```typescript
// Find deprecated usage
const DEPRECATED_PATTERNS = [
  'client.oldMethod',
];

// Suppress warnings during migration (temporary)
process.env.SUPABASE_SUPPRESS_DEPRECATION = 'true';
```

## Rollback Plan

```bash
# 1. Keep old version pinned in package-lock.json
npm install @supabase/supabase-js@1.x.x --save-exact

# 2. Document rollback command
echo "Rollback: npm install @supabase/supabase-js@1.x.x"

# 3. Test rollback in staging first
```

## Version Compatibility Matrix

| SDK Version | API Version | Node.js | Breaking Changes |
|-------------|-------------|---------|------------------|
| 3.x | 2024-01 | 18+ | Major refactor |
| 2.x | 2023-06 | 16+ | Auth changes |
| 1.x | 2022-01 | 14+ | Initial release |

## Migration Checklist

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

## Pro Tier Skills
For CI integration during upgrades, see `supabase-ci-integration`.