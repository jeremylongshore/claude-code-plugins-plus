---
name: linear-upgrade-migration
description: |
  Upgrade Linear SDK versions and migrate breaking changes.
  Use when updating to a new SDK version, handling deprecations,
  or migrating between major Linear API versions.
  Trigger with phrases like "upgrade linear SDK", "linear SDK migration",
  "update linear", "linear breaking changes", "linear deprecation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Upgrade Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Safely upgrade Linear SDK versions and handle breaking changes with compatibility layers and gradual rollout.

## Prerequisites
- Existing Linear integration
- Version control (Git) configured
- Test suite for Linear operations

## Instructions

### Step 1: Check Current and Latest Versions
```bash
set -euo pipefail
npm list @linear/sdk          # Current version
npm view @linear/sdk version  # Latest available
```

### Step 2: Review Breaking Changes
Check GitHub releases and changelog for migration guides between your current and target versions.

### Step 3: Create Upgrade Branch
```bash
set -euo pipefail
git checkout -b upgrade/linear-sdk-vX.Y.Z
npm install @linear/sdk@latest
npx tsc --noEmit  # Check for type errors
```

### Step 4: Apply Migration Patterns
Common changes between versions: renamed fields, changed return types (direct to paginated), new required parameters, and removed methods.

### Step 5: Create Compatibility Layer
Wrap breaking changes in a compat client to normalize behavior across versions.

### Step 6: Test and Deploy
```bash
set -euo pipefail
npm test && npx tsc --noEmit && npm run lint
npm run deploy:staging && npm run test:integration
```

### Step 7: Gradual Rollout
Use feature flags to toggle between old and new SDK behavior in production.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for all migration patterns, compatibility layer code, and version-specific changes.

## Version Compatibility Matrix

| SDK Version | Node.js | TypeScript | Key Changes |
|-------------|---------|------------|-------------|
| 1.x | 14+ | 4.5+ | Initial release |
| 2.x | 16+ | 4.7+ | ESM support |
| 3.x | 18+ | 5.0+ | Strict types |

## Output
- SDK upgraded to target version
- Breaking changes resolved
- Compatibility layer in place
- Tests passing on new version

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Property does not exist` | Renamed field | Check migration guide for new name |
| `Type not assignable` | Changed type | Update type annotations |
| `Module not found` | ESM/CJS mismatch | Update import syntax |
| `Runtime method missing` | Version mismatch | Verify installed SDK version |

## Examples

### Check for Breaking Changes Before Upgrading
```bash
# Compare your current version with latest
npm list @linear/sdk
npm view @linear/sdk versions --json | jq '.[-5:]'
# Review changelog for breaking changes between versions
npm view @linear/sdk repository.url
```

### Compatibility Wrapper for Renamed Methods
```typescript
// Bridge pattern for gradual migration
function getIssueState(issue: any): string {
  // SDK v2: issue.state was a direct property
  // SDK v3: issue.state is a lazy-loaded relation
  if (typeof issue.state === "string") return issue.state;  // v2
  return issue.state?.name ?? "unknown";  // v3
}
```

### Verify After Upgrade
```bash
# Type-check, test, and lint after upgrading
npx tsc --noEmit && npm test && npm run lint
# If clean, commit the upgrade
git add package.json package-lock.json
git commit -m "chore: upgrade @linear/sdk to vX.Y.Z"
```

## Resources
- [Linear SDK Changelog](https://github.com/linear/linear/blob/master/packages/sdk/CHANGELOG.md)
- [Linear API Changelog](https://developers.linear.app/docs/changelog)
- [TypeScript Migration](https://www.typescriptlang.org/docs/handbook/migrating-from-javascript.html)

## Next Steps
Set up CI/CD integration with `linear-ci-integration`.