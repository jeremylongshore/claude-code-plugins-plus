---
name: lokalise-upgrade-migration
description: |
  Analyze, plan, and execute Lokalise SDK upgrades with breaking change detection.
  Use when upgrading Lokalise SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade lokalise", "lokalise migration",
  "lokalise breaking changes", "update lokalise SDK", "analyze lokalise version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(git:*), Bash(node:*), Bash(grep:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Upgrade Migration

## Current State
!`npm list @lokalise/node-api 2>/dev/null | grep lokalise || echo 'SDK not installed'`
!`lokalise2 --version 2>/dev/null || echo 'CLI not installed'`
!`node --version 2>/dev/null || echo 'Node.js not available'`
!`cat package.json 2>/dev/null | grep -E '"type"|"module"' || echo 'No package.json type field'`

## Overview

Upgrade the `@lokalise/node-api` SDK between major versions with full breaking change detection, automated code transformation, and verification. The most significant migration is v8 (CommonJS) to v9+ (ESM-only), which requires changes to imports, module configuration, and potentially your build pipeline.

## Prerequisites

- Existing project using `@lokalise/node-api` (any version 6.x through 9.x)
- Node.js 18+ for SDK v9 (Node.js 14+ for v8 and below)
- Git repository with clean working tree (for safe rollback)
- Test suite that exercises Lokalise API calls

## Instructions

### Step 1: Assess Current Version and Target

```bash
set -euo pipefail
echo "=== Current SDK Version ==="
CURRENT=$(npm list @lokalise/node-api --json 2>/dev/null | node -e "
  const d = JSON.parse(require('fs').readFileSync(0,'utf8'));
  const v = d.dependencies?.['@lokalise/node-api']?.version || 'not found';
  console.log(v);
")
echo "Installed: ${CURRENT}"

echo -e "\n=== Latest Available ==="
LATEST=$(npm view @lokalise/node-api version)
echo "Latest: ${LATEST}"

echo -e "\n=== All Major Versions ==="
npm view @lokalise/node-api versions --json | node -e "
  const versions = JSON.parse(require('fs').readFileSync(0,'utf8'));
  const majors = {};
  versions.forEach(v => { const m = v.split('.')[0]; majors[m] = v; });
  Object.entries(majors).forEach(([m, v]) => console.log('  v' + m + '.x latest: ' + v));
"
```

### Step 2: Review Breaking Changes by Version

| Version | Node.js | Module System | Key Breaking Changes |
|---------|---------|---------------|---------------------|
| **9.x** | 18+ | ESM only | `require()` removed, `import` only. Pagination returns typed cursors. `ApiError` export path changed. |
| **8.x** | 14+ | CJS + ESM | Last version supporting `require()`. Constructor accepts `apiKey` (not `token`). |
| **7.x** | 14+ | CJS | Cursor pagination introduced. `list()` methods return paginated objects. |
| **6.x** | 12+ | CJS | TypeScript rewrite. Method signatures changed from callbacks to promises. |

### Step 3: Migrate Imports (v8 CJS to v9 ESM)

This is the most impactful change. Every `require()` call must become an `import`.

**Find all Lokalise imports in your codebase:**

```bash
set -euo pipefail
grep -rn "require.*lokalise\|from.*lokalise" --include="*.ts" --include="*.js" --include="*.mjs" . || echo "No imports found"
```

**Transform patterns:**

```typescript
// BEFORE (v8 CommonJS)
const { LokaliseApi } = require('@lokalise/node-api');
const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN });

// AFTER (v9 ESM)
import { LokaliseApi } from '@lokalise/node-api';
const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN });
```

**Update `package.json` for ESM:**

```json
{
  "type": "module"
}
```

**Update `tsconfig.json` if using TypeScript:**

```json
{
  "compilerOptions": {
    "module": "ES2022",
    "moduleResolution": "bundler",
    "target": "ES2022"
  }
}
```

### Step 4: Update Pagination Code (v6/v7 to v9)

```typescript
// BEFORE (v6 offset pagination)
const keys = await lok.keys().list({
  project_id: projectId,
  page: 2,
  limit: 100,
});

// AFTER (v9 cursor pagination — preferred for large datasets)
const keys = await lok.keys().list({
  project_id: projectId,
  limit: 500,
  pagination: 'cursor',
  cursor: previousCursor,
});
// Access next cursor: keys.nextCursor
// Check for more: keys.hasNextCursor()
```

### Step 5: Update Error Handling

```typescript
// BEFORE (v8)
const { ApiError } = require('@lokalise/node-api');
try {
  await lok.projects().get(projectId);
} catch (e) {
  if (e instanceof ApiError) {
    console.error(e.message, e.code);
  }
}

// AFTER (v9 — ApiError import path unchanged, but must use import)
import { ApiError } from '@lokalise/node-api';
try {
  await lok.projects().get(projectId);
} catch (e) {
  if (e instanceof ApiError) {
    console.error(e.message, e.code);
  }
}
```

### Step 6: Install and Verify

```bash
set -euo pipefail
# Create a safety branch
git checkout -b upgrade/lokalise-sdk-v9

# Install the target version
npm install @lokalise/node-api@latest

# Run TypeScript compilation check
npx tsc --noEmit 2>&1 | head -40 || true

# Run tests
npm test
```

### Step 7: Verify API Compatibility

```typescript
// Quick smoke test after upgrade
import { LokaliseApi } from '@lokalise/node-api';

const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

// Test basic operations still work
const projects = await lok.projects().list({ limit: 1 });
console.log('API connection OK:', projects.items[0]?.name ?? 'no projects');

const keys = await lok.keys().list({
  project_id: projects.items[0].project_id,
  limit: 5,
  pagination: 'cursor',
});
console.log('Cursor pagination OK:', keys.items.length, 'keys fetched');
```

## Output

- Updated `@lokalise/node-api` to target version
- All `require()` calls converted to ESM `import` (if upgrading to v9)
- `package.json` and `tsconfig.json` updated for ESM compatibility
- Pagination code migrated to cursor-based pattern
- Tests passing against the new SDK version
- Git branch with all changes for review

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `ERR_REQUIRE_ESM` | Using `require()` with v9 SDK | Convert to `import` syntax and set `"type": "module"` in package.json |
| `SyntaxError: Cannot use import` | Node.js file not recognized as ESM | Rename `.js` to `.mjs` or add `"type": "module"` |
| `TypeError: lok.keys is not a function` | API changed between major versions | Check SDK changelog for renamed methods |
| `ERR_UNKNOWN_FILE_EXTENSION .ts` | TypeScript not configured for ESM | Use `tsx` runner or configure `ts-node` with `"esm": true` |
| Tests fail after upgrade | Breaking API changes | Check test against the version-specific migration notes above |

## Examples

### Rollback Procedure

```bash
set -euo pipefail
# If the upgrade causes issues, revert immediately
git stash  # Save any work in progress
npm install @lokalise/node-api@8  # Last CJS version
git checkout HEAD -- tsconfig.json package.json
npm test
echo "Rolled back to v8. Investigate failures before retrying."
```

### CLI Upgrade (Separate from SDK)

```bash
set -euo pipefail
# macOS
brew upgrade lokalise2

# Linux — download latest release binary
LATEST_CLI=$(curl -s https://api.github.com/repos/lokalise/lokalise-cli-2-go/releases/latest | grep -oP '"tag_name": "\K[^"]+')
curl -sL "https://github.com/lokalise/lokalise-cli-2-go/releases/download/${LATEST_CLI}/lokalise2_linux_x86_64.tar.gz" | tar xz
sudo mv lokalise2 /usr/local/bin/

# Verify
lokalise2 --version
```

### Check for Deprecated API Usage

```bash
set -euo pipefail
# Patterns that indicate outdated SDK usage
echo "=== Deprecated Patterns ==="
grep -rn "\.page\s*:" --include="*.ts" --include="*.js" . && echo "^ Offset pagination — migrate to cursor" || echo "No offset pagination found"
grep -rn "require.*lokalise" --include="*.ts" --include="*.js" . && echo "^ CommonJS require — migrate to ESM import" || echo "No CJS requires found"
grep -rn "new LokaliseApi.*token:" --include="*.ts" --include="*.js" . && echo "^ Old constructor — use apiKey instead of token" || echo "No old constructor pattern found"
```

## Resources

- [Node SDK Changelog](https://lokalise.github.io/node-lokalise-api/additional_info/changelog.html)
- [Node SDK GitHub](https://github.com/lokalise/node-lokalise-api)
- [API Changelog](https://developers.lokalise.com/docs/api-changelog)
- [CLI Releases](https://github.com/lokalise/lokalise-cli-2-go/releases)
- [ESM Migration Guide (Node.js)](https://nodejs.org/api/esm.html)

## Next Steps

- For CI pipeline changes needed after ESM migration, see `lokalise-ci-integration`.
- For performance improvements with the new cursor pagination, see `lokalise-performance-tuning`.
- Run `lokalise-debug-bundle` if the upgrade causes unexpected API errors.
