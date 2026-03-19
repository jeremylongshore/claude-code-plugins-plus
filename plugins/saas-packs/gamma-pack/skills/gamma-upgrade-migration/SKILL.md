---
name: gamma-upgrade-migration
description: |
  Upgrade Gamma SDK versions and migrate between API versions.
  Use when upgrading SDK packages, handling deprecations,
  or migrating to new API versions.
  Trigger with phrases like "gamma upgrade", "gamma migration",
  "gamma new version", "gamma deprecated", "gamma SDK update".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Guide for upgrading Gamma SDK versions and migrating between API versions safely.

## Prerequisites
- Existing Gamma integration
- Version control (git)
- Test environment available

## Instructions

### Step 1: Check Current Version
```bash
set -euo pipefail
# Node.js
npm list @gamma/sdk

# Python
pip show gamma-sdk

# Check for available updates
npm outdated @gamma/sdk
```

### Step 2: Review Changelog
```bash
set -euo pipefail
# View changelog
npm info @gamma/sdk changelog

# Or visit
# https://gamma.app/docs/changelog
```

### Step 3: Upgrade SDK
```bash
set -euo pipefail
# Create upgrade branch
git checkout -b feat/gamma-sdk-upgrade

# Node.js - upgrade to latest
npm install @gamma/sdk@latest

# Python - upgrade to latest
pip install --upgrade gamma-sdk

# Or specific version
npm install @gamma/sdk@2.0.0
```

### Step 4: Handle Breaking Changes

**Common Migration Patterns:**

```typescript
// v1.x -> v2.x: Client initialization change
// Before (v1)
import Gamma from '@gamma/sdk';
const gamma = new Gamma(apiKey);

// After (v2)
import { GammaClient } from '@gamma/sdk';
const gamma = new GammaClient({ apiKey });
```

```typescript
// v1.x -> v2.x: Response format change
// Before (v1)
const result = await gamma.createPresentation({ title: 'Test' });
console.log(result.id);

// After (v2)
const result = await gamma.presentations.create({ title: 'Test' });
console.log(result.data.id);
```

```typescript
// v1.x -> v2.x: Error handling change
// Before (v1)
try {
  await gamma.create({ ... });
} catch (e) {
  if (e.code === 'RATE_LIMIT') { ... }
}

// After (v2)
import { RateLimitError } from '@gamma/sdk';
try {
  await gamma.presentations.create({ ... });
} catch (e) {
  if (e instanceof RateLimitError) { ... }
}
```

### Step 5: Update Type Definitions
```typescript
// Check for type changes
// tsconfig.json - ensure strict mode catches issues
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true
  }
}

// Run type check
npx tsc --noEmit
```

### Step 6: Test Thoroughly
```bash
set -euo pipefail
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Manual smoke test
node -e "
const { GammaClient } = require('@gamma/sdk');
const g = new GammaClient({ apiKey: process.env.GAMMA_API_KEY });
g.ping().then(() => console.log('OK')).catch(console.error);
"
```

### Step 7: Deprecation Handling
```typescript
// Enable deprecation warnings
const gamma = new GammaClient({
  apiKey: process.env.GAMMA_API_KEY,
  showDeprecationWarnings: true,
});

// Migrate deprecated methods
// Deprecated
await gamma.getPresentations();

// New
await gamma.presentations.list();
```

## Migration Checklist
- [ ] Current version documented
- [ ] Changelog reviewed
- [ ] Breaking changes identified
- [ ] Upgrade branch created
- [ ] SDK upgraded
- [ ] Type errors fixed
- [ ] Deprecation warnings addressed
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Staging deployment verified
- [ ] Production deployment planned

## Rollback Procedure
```bash
set -euo pipefail
# If issues occur after upgrade
git checkout main
npm install  # Restores previous version from lock file

# Or explicitly downgrade
npm install @gamma/sdk@1.x.x
```

## Resources
- [Gamma Changelog](https://gamma.app/docs/changelog)
- [Gamma Migration Guides](https://gamma.app/docs/migration)
- [Gamma API Versioning](https://gamma.app/docs/versioning)

## Next Steps
Proceed to `gamma-ci-integration` for CI/CD setup.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with migration |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply gamma upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize gamma upgrade migration for production environments with multiple constraints and team-specific requirements.