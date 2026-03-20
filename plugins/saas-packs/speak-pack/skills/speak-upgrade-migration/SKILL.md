---
name: speak-upgrade-migration
description: |
  Analyze, plan, and execute Speak SDK upgrades with breaking change detection.
  Use when upgrading Speak SDK versions, detecting deprecations,
  or migrating to new API versions for language learning features.
  Trigger with phrases like "upgrade speak", "speak migration",
  "speak breaking changes", "update speak SDK", "analyze speak version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Upgrade Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Guide for upgrading Speak SDK versions and handling breaking changes in language learning integrations.

## Prerequisites
- Current Speak SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions
1. **Deprecation Handling**
2. **Rollback Procedure**
3. **Testing Upgrade in Staging**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Updated SDK version
- Fixed breaking changes
- Passing test suite
- Documented rollback procedure

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Import errors | Path changed | Update import paths |
| Type errors | Interface changed | Update type definitions |
| Runtime errors | API behavior changed | Review changelog |
| Test failures | Mock outdated | Update test mocks |

## Resources
- [Speak Changelog](https://github.com/speak/language-sdk/releases)
- [Speak Migration Guide](https://developer.speak.com/docs/migration)
- [Speak API Versioning](https://developer.speak.com/docs/versioning)

## Next Steps
For CI integration during upgrades, see `speak-ci-integration`.

## Examples

### Basic: Upgrade Speak SDK and Check for Breaking Changes
```bash
# Check current version
npm list @speak/sdk 2>/dev/null | grep speak

# Upgrade to latest
npm install @speak/sdk@latest

# Run type-check to catch breaking changes
npx tsc --noEmit 2>&1 | grep -i "speak\|error TS"

# Run existing tests
npm test -- --grep "speak" 2>&1 | tail -20
```

### Advanced: Automated Migration with Rollback Support
```typescript
import { execSync } from "child_process";
import * as fs from "fs";

interface MigrationResult {
  previousVersion: string;
  newVersion: string;
  breakingChanges: string[];
  testsPass: boolean;
}

async function migrateSpeakSdk(targetVersion: string): Promise<MigrationResult> {
  // Snapshot current state for rollback
  const lockfile = fs.readFileSync("package-lock.json", "utf-8");
  const prevVersion = execSync("npm list @speak/sdk --json 2>/dev/null")
    .toString();

  try {
    // Upgrade
    execSync(`npm install @speak/sdk@${targetVersion}`, { stdio: "pipe" });

    // Detect breaking changes via TypeScript compiler
    let breakingChanges: string[] = [];
    try {
      execSync("npx tsc --noEmit", { stdio: "pipe" });
    } catch (err: any) {
      breakingChanges = err.stdout
        .toString()
        .split("\n")
        .filter((l: string) => l.includes("error TS"));
    }

    // Run tests
    let testsPass = false;
    try {
      execSync("npm test -- --grep speak", { stdio: "pipe" });
      testsPass = true;
    } catch {
      testsPass = false;
    }

    // Auto-rollback if tests fail and there are breaking changes
    if (!testsPass && breakingChanges.length > 0) {
      console.warn("Rolling back — tests failed with breaking changes");
      fs.writeFileSync("package-lock.json", lockfile);
      execSync("npm ci", { stdio: "pipe" });
    }

    return {
      previousVersion: JSON.parse(prevVersion).dependencies?.["@speak/sdk"]?.version || "unknown",
      newVersion: targetVersion,
      breakingChanges,
      testsPass,
    };
  } catch (err) {
    // Rollback on any failure
    fs.writeFileSync("package-lock.json", lockfile);
    execSync("npm ci", { stdio: "pipe" });
    throw err;
  }
}
```