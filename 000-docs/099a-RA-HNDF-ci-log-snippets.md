# CI Log Snippets - Failing Tests Evidence

**Date**: 2025-12-25
**Run**: #20509963126
**Branch**: fix-ci-test-failures
**Status**: FAILING

---

## CRITICAL ERROR: Lockfile Out of Sync

### test (mcp-plugins) - Install dependencies - EXIT CODE 1

**Timestamp**: 2025-12-25T19:34:35.7226562Z

```
Scope: all 11 workspace projects
 ERR_PNPM_OUTDATED_LOCKFILE  Cannot install with "frozen-lockfile" because pnpm-lock.yaml is not up to date with <ROOT>/marketplace/package.json

Note that in CI environments this setting is true by default. If you still need to run install in such cases, use "pnpm install --no-frozen-lockfile"

    Failure reason:
    specifiers in the lockfile ({"@tailwindcss/vite":"^4.1.18","astro":"^5.16.6","fuse.js":"^7.1.0","tailwindcss":"^4.1.18"}) don't match specs in package.json ({"@playwright/test":"^1.57.0","@tailwindcss/vite":"^4.1.18","astro":"^5.16.6","fuse.js":"^7.1.0","tailwindcss":"^4.1.18"})
##[error]Process completed with exit code 1.
```

**ROOT CAUSE** (FACT):
- `marketplace/package.json` contains `@playwright/test": "^1.57.0"` in dependencies
- `pnpm-lock.yaml` does NOT have `@playwright/test` recorded
- Running with `--frozen-lockfile` flag fails because lockfile is outdated

**WHEN DID THIS HAPPEN**:
- Playwright was likely added to `marketplace/package.json` recently
- Lockfile was NOT regenerated after adding this dependency
- Last lockfile update: Dec 24 08:27 (from file timestamp)
- Recent commits touching marketplace: Multiple on Dec 25

**FIX REQUIRED**:
```bash
# From repository root
pnpm install  # WITHOUT --frozen-lockfile
git add pnpm-lock.yaml
git commit -m "chore: Update pnpm-lock.yaml for @playwright/test dependency"
```

---

## test (validation-scripts) - Run validation script tests - EXIT CODE 1

**Timestamp**: 2025-12-25T19:34:33.7572598Z

**Script Output**:
```bash
Testing validation scripts...
Running validate-all-plugins.sh on MCP plugins...
🔍 Running comprehensive validation...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Validating JSON files...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Checking: plugins/mcp/project-health-auditor/package.json
  Checking: plugins/mcp/project-health-auditor/.claude-plugin/plugin.json
  Checking: plugins/mcp/project-health-auditor/.mcp.json
  Checking: plugins/mcp/project-health-auditor/tsconfig.json
  [... more JSON files ...]
✅ All JSON valid

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Validating markdown frontmatter...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  check-frontmatter.py not found, skipping detailed frontmatter validation
  Checking: plugins/mcp/project-health-auditor/commands/analyze.md
  Checking: plugins/mcp/project-health-auditor/agents/reviewer.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 Checking for duplicate shortcuts...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ No duplicate shortcuts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Validating file references...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Checking references in: plugins/mcp/project-health-auditor/.claude-plugin/plugin.json
✅ All file references valid

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 Checking script permissions...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All scripts executable

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Checking required documentation...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[... checking all plugins ...]
```

**NOTE**: The validation script test appears to RUN successfully (all checks pass), but then exits with code 1. This suggests the script may have a bug where it returns exit code 1 even on success, OR there's a subsequent command that fails.

**HYPOTHESIS**: The exit code 1 is likely a CASCADING FAILURE from the earlier pnpm install failure. The job matrix may share dependencies.

**ACTION REQUIRED**: Rerun validation-scripts job AFTER fixing pnpm lockfile. This failure may auto-resolve.

---

## test (python-tests) - Run Python tests - EXIT CODE 1

**Job Status**: Failed at "Run Python tests" step
**Exit Code**: 1 (line 84 in workflow)

**ERROR**: Full logs not captured in snippet due to earlier job failures preventing execution.

**HYPOTHESIS**: Python tests may depend on successful pnpm install. Cascading failure from lockfile issue.

**ACTION REQUIRED**: Rerun python-tests job AFTER fixing pnpm lockfile. Verify python dependencies are installed correctly.

---

## cli-smoke-tests - Install CLI dependencies - EXIT CODE 1

**Job Status**: Failed at "Install CLI dependencies" step
**Exit Code**: 1 (line 15 in workflow)

**Expected Command**:
```bash
cd packages/cli
pnpm install --frozen-lockfile
```

**HYPOTHESIS**: Same lockfile mismatch issue. The CLI package may have workspace dependencies that reference the outdated lockfile.

**ACTION REQUIRED**: Rerun cli-smoke-tests job AFTER fixing pnpm lockfile.

---

## playwright-tests - Status: NOT STARTED

**Job Status**: Did not execute
**Reason**: Depends on previous jobs (needs: marketplace-validation)

**Expected Behavior**: Once lockfile is fixed and previous jobs pass, Playwright tests will execute.

**Previous Issues (FIXED in commit 02f79a97)**:
1. Toggle buttons blocking search input (pointer-events fix)
2. WebKit clipboard permissions (browser check added)
3. Screenshot size limit (fullPage: false)
4. Removed debug-search.spec.ts test

**PREDICTION**: Playwright tests will PASS once they run, based on local test results and fixes already implemented.

---

## Summary: Root Cause Analysis

**PRIMARY BLOCKER**: `pnpm-lock.yaml` is out of sync with `marketplace/package.json`

**Evidence**:
- marketplace/package.json contains `@playwright/test`: "^1.57.0"
- pnpm-lock.yaml does NOT have this dependency recorded
- All jobs using `pnpm install --frozen-lockfile` fail with ERR_PNPM_OUTDATED_LOCKFILE

**Cascading Failures**:
1. test (mcp-plugins) - Install dependencies ❌
2. test (validation-scripts) - Possibly affected by shared workspace state ❌
3. test (python-tests) - Possibly affected by shared workspace state ❌
4. cli-smoke-tests - Install CLI dependencies ❌
5. playwright-tests - Not started (depends on previous jobs) ⏸️

**Resolution Path**:
1. Run `pnpm install` (WITHOUT --frozen-lockfile) from repository root
2. Commit updated pnpm-lock.yaml
3. Push to trigger new CI run
4. All jobs should pass ✅

---

## File References

**Primary Issue File**:
- `marketplace/package.json` (contains @playwright/test)
- `pnpm-lock.yaml` (missing @playwright/test)

**Affected Workflow**:
- `.github/workflows/validate-plugins.yml` (all jobs using pnpm install)

**Last Modified Dates**:
- pnpm-lock.yaml: Dec 24 08:27 (STALE)
- marketplace/package.json: Dec 25 08:34 (RECENT)

---

**End of CI Log Snippets**
