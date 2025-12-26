# Phase 0 Orientation + Audit

**Branch**: p0-stabilization-proof-gates
**Date**: 2025-12-25
**Author**: Claude Code (Sonnet 4.5)

## Environment Info

```
Node: v22.20.0 (MISMATCH: .nvmrc specifies 20)
npm: 11.7.0
pnpm: NOT INSTALLED (CRITICAL: This is a pnpm workspace!)
bun: 1.2.23
```

**Repository Structure**:
- pnpm workspace with 4 packages
- pnpm-lock.yaml exists (231KB)
- No package-lock.json (correct for pnpm)

## Root Causes

### 1. marketplace.json Out of Sync (CI Blocker)

**File**: `.claude-plugin/marketplace.json`
**Script**: `scripts/sync-marketplace.cjs`
**Failure**: validate-plugins.yml line 17-24

**Issue**: Running `node scripts/sync-marketplace.cjs` modifies marketplace.json (18 deletions), indicating it's out of sync with marketplace.extended.json.

**Specific Change**: Removed `agent-context-manager` plugin entry from marketplace.json.

**Root Cause**: Someone modified marketplace.json directly OR added plugin to marketplace.extended.json without syncing, then committed the out-of-sync files.

**Evidence**:
```bash
$ node scripts/sync-marketplace.cjs
✅ Synced CLI marketplace catalog
$ git diff --stat .claude-plugin/marketplace.json
 .claude-plugin/marketplace.json | 18 ------------------
```

**Fix Required**: Commit the synced marketplace.json file.

---

### 2. Missing Learning Routes (CI Blocker)

**File**: `scripts/check-routes.mjs`
**Failure**: validate-plugins.yml line 404-405 (marketplace-validation job)

**Issue**: Route validation expects 277 routes but only finds 275. Missing:
- `/learning/built-system-summary`
- `/learning/getting-started`

**Root Cause**: These pages were deleted in PR #193 (commit f7bdca17) due to syntax errors, but the expected routes list was never updated.

**Evidence**:
```bash
$ node scripts/check-routes.mjs
✗ 2 missing routes:
  - /learning/built-system-summary
  - /learning/getting-started
Found: 275/277
Missing: 2/277
Exit code: 1
```

**Fix Required**: Either restore the pages without syntax errors OR update the expected routes count to 275 and remove these from the expected list.

---

### 3. Node Version Mismatch (Environment Issue)

**File**: `.nvmrc`
**Issue**: .nvmrc specifies Node 20, but local environment runs Node 22.20.0

**Impact**: CI uses Node 20 (per workflow line 228, 378, 392), local dev uses 22. Potential for behavior differences.

**Fix Required**: Either update .nvmrc to 22 OR install nvm and switch to Node 20 locally.

---

### 4. pnpm Not Installed Locally (Development Issue)

**Issue**: This is a pnpm workspace, but pnpm is not installed locally.

**Impact**: Cannot run `pnpm install`, `pnpm build`, `pnpm test` locally. Must rely on bun or npm, which may not respect workspace configuration.

**Evidence**: `pnpm -v` returns "NOT INSTALLED"

**Fix Required**: Install pnpm globally or via corepack.

---

### 5. Validation Workflow Consistently Failing

**Workflow**: `.github/workflows/validate-plugins.yml`
**Status**: Last 5 runs all FAILED
**Deploy Status**: Last 4 runs all SUCCEEDED

**Critical Issue**: Site is deploying to production WITHOUT passing validation checks. This is a dangerous state.

**Failures**:
- Run 20499890105: validate job failed (sync-marketplace), marketplace-validation failed (routes)
- Run 20499865106: Same failures
- Run 20499363649: Same failures
- Run 20499342682: Same failures
- Run 20499309181: Same failures

**Fix Required**: Fix both root causes #1 and #2 to unblock validation workflow.

---

## Homepage Search Issues (User Reported)

### Issue: Search Bar Toggle Buttons Not Working

**User Report**: "search bar still doesnt work and the buttons it it are deas"

**Root Cause** (needs verification): Likely CSS z-index or pointer-events issue causing input to overlap toggle buttons.

**Investigation Required**: Inspect `/marketplace/src/pages/index.astro` search controls and test in mobile viewport.

---

### Issue: Missing Installation Instructions

**User Report**: "still no where to find out how to install rhe package"

**Status**: FIXED in PR #195 (installation box added to hero section)

**Verification Required**: Confirm visible on live site.

---

### Issue: Learning Hub Not Centered

**User Report**: "learning hub isnt centerd in jts box"

**Status**: FIXED in PR #196 (added text-align: center to .feature-card)

**Verification Required**: Confirm centered on live site.

---

## pnpm Workspace Status

**Current Membership** (pnpm-workspace.yaml):
- `plugins/mcp/*`
- `marketplace`
- `packages/cli`
- `packages/analytics-daemon`

**Previously Removed**: `packages/analytics-dashboard` (removed in PR #192 to bypass lockfile issue)

**Issue**: Removed package from workspace without running `pnpm install` to update lockfile. This was a shortcut to unblock deployment.

**Proper Fix Required**: Decide if analytics-dashboard should be in workspace. If yes, add it back and run `pnpm install`. If no, archive/remove it.

**Phase 1 Decision (implemented)**: Archived to `packages/_archive-analytics-dashboard/` to make workspace membership unambiguous without expanding CI scope.

---

## Recommended Phase 1 Actions

1. **Immediate**: Commit synced marketplace.json to fix CI blocker #1
2. **Immediate**: Fix missing learning routes (remove from expected or restore pages) for CI blocker #2
3. **Required**: Install pnpm locally via corepack for workspace operations
4. **Critical**: Add smoke checks to validate-plugins workflow to prevent deployment without validation passing

---

## Evidence Files

- Workflow logs: https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20499890105
- This audit: `PHASE0-AUDIT.md`
- Branch: `p0-stabilization-proof-gates`
