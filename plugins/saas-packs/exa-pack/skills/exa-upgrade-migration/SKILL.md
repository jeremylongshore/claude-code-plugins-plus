---
name: exa-upgrade-migration
description: |
  Upgrade exa-js SDK versions and handle breaking changes safely.
  Use when upgrading the Exa SDK, detecting deprecations,
  or migrating between exa-js versions.
  Trigger with phrases like "upgrade exa", "exa update",
  "exa breaking changes", "update exa-js", "exa new version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, api, migration, upgrade]

---
# Exa Upgrade & Migration

## Current State
!`npm list exa-js 2>/dev/null | grep exa-js || echo 'exa-js not installed'`
!`npm view exa-js version 2>/dev/null || echo 'cannot check latest'`

## Overview
Guide for upgrading the `exa-js` SDK. The SDK import is `import Exa from "exa-js"` and the client is instantiated with `new Exa(apiKey)`. This skill covers checking for updates, handling breaking changes, and validating after upgrade.

## Instructions

### Step 1: Check Current vs Latest Version
```bash
set -euo pipefail
echo "Current version:"
npm list exa-js 2>/dev/null || echo "Not installed"

echo ""
echo "Latest available:"
npm view exa-js version

echo ""
echo "Changelog:"
npm view exa-js repository.url
```

### Step 2: Create Upgrade Branch
```bash
set -euo pipefail
git checkout -b upgrade/exa-js-latest
npm install exa-js@latest
npm test
```

### Step 3: Verify API Compatibility
```typescript
import Exa from "exa-js";

async function verifyUpgrade() {
  const exa = new Exa(process.env.EXA_API_KEY);
  const checks = [];

  // Check 1: Basic search
  try {
    const r = await exa.search("upgrade test", { numResults: 1 });
    checks.push({ method: "search", status: "OK", results: r.results.length });
  } catch (err: any) {
    checks.push({ method: "search", status: "FAIL", error: err.message });
  }

  // Check 2: searchAndContents
  try {
    const r = await exa.searchAndContents("upgrade test", {
      numResults: 1,
      text: { maxCharacters: 100 },
      highlights: { maxCharacters: 100 },
    });
    checks.push({
      method: "searchAndContents",
      status: "OK",
      hasText: !!r.results[0]?.text,
      hasHighlights: !!r.results[0]?.highlights,
    });
  } catch (err: any) {
    checks.push({ method: "searchAndContents", status: "FAIL", error: err.message });
  }

  // Check 3: findSimilar
  try {
    const r = await exa.findSimilar("https://nodejs.org", { numResults: 1 });
    checks.push({ method: "findSimilar", status: "OK", results: r.results.length });
  } catch (err: any) {
    checks.push({ method: "findSimilar", status: "FAIL", error: err.message });
  }

  // Check 4: getContents
  try {
    const r = await exa.getContents(["https://nodejs.org"], { text: true });
    checks.push({ method: "getContents", status: "OK", hasContent: !!r.results[0]?.text });
  } catch (err: any) {
    checks.push({ method: "getContents", status: "FAIL", error: err.message });
  }

  console.table(checks);
  const allPassed = checks.every(c => c.status === "OK");
  console.log(`\nUpgrade verification: ${allPassed ? "PASSED" : "FAILED"}`);
  return allPassed;
}
```

### Step 4: Common Breaking Change Patterns

```typescript
// Import style (has been stable)
import Exa from "exa-js";  // default export

// Constructor (has been stable)
const exa = new Exa("api-key");

// If upgrading from a very old version, check:
// - Method names: searchAndContents (not searchWithContents)
// - findSimilarAndContents (not findSimilarWithContents)
// - Parameter names: numResults (not num_results)
// - Content options: text, highlights, summary as objects

// Check for deprecated parameters
// - livecrawl may be replaced by maxAgeHours in newer versions
// - Check changelog for parameter renames
```

### Step 5: Rollback Procedure
```bash
set -euo pipefail
# If tests fail, rollback
npm install exa-js@<previous-version> --save-exact
git checkout -- package-lock.json  # restore lockfile
npm test  # verify rollback works
```

## Upgrade Checklist
- [ ] Create branch: `upgrade/exa-js-latest`
- [ ] Run `npm install exa-js@latest`
- [ ] Run full test suite: `npm test`
- [ ] Run upgrade verification script (checks all methods)
- [ ] Check for deprecation warnings in output
- [ ] Review changelog for breaking changes
- [ ] Update any changed parameter names
- [ ] Merge after all checks pass

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Import error after upgrade | API change | Check `import Exa from "exa-js"` still works |
| Method not found | Renamed method | Check SDK changelog |
| Type errors | Parameter type changes | Update TypeScript types |
| Tests fail | Breaking change | Review changelog, update code |

## Resources
- [exa-js on npm](https://www.npmjs.com/package/exa-js)
- [exa-js GitHub](https://github.com/exa-labs/exa-js)
- [Exa Changelog](https://docs.exa.ai/changelog)

## Next Steps
For CI integration during upgrades, see `exa-ci-integration`.
