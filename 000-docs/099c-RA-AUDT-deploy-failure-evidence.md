# Deploy Failure Evidence & History

**Date**: 2025-12-25
**Current Status**: Deployment BLOCKED by CI failures

---

## Current Deployment State

### GitHub Pages Deployment

**Production URL**: https://claudecodeplugins.io/
**Last Successful Deploy**: Unknown (need to check workflow history)
**Current Branch**: main (not fix-ci-test-failures)

**Deploy Workflow**: `.github/workflows/deploy-marketplace.yml` (if exists)
**Trigger**: Push to main branch + changes in marketplace/

---

## Recent Deployment History

### Commit Timeline (from git log):

```
407cab1c - feat: EPIC D+E - CLI reliability + workspace hygiene complete
c2a7669a - feat(epic-c): 100% mobile test pass rate - homepage UX complete
c1dcdd3f - Merge pull request #196
...
697c6815 - fix(ci): Remove analytics-dashboard from workspace to unblock deployment
```

**Note**: Commit 697c6815 (Dec 24) explicitly mentions "unblock deployment"
**Implication**: Deployment was BLOCKED before analytics-dashboard removal

---

## Deployment Blockers (Historical)

### Blocker 1: analytics-dashboard Dependency Issues

**Commit**: 697c6815 (Dec 24 22:59)
**Message**: "fix(ci): Remove analytics-dashboard from workspace to unblock deployment"

**What Happened**:
- `packages/analytics-dashboard` was causing deployment failures
- Removed from pnpm-workspace.yaml to unblock
- **HOWEVER**: pnpm-lock.yaml was NOT updated at that time
- This created the lockfile mismatch we're experiencing now

**Evidence**:
- pnpm-workspace.yaml modified: Dec 24 22:59
- pnpm-lock.yaml last update: Dec 24 08:27 (EARLIER)
- Time gap: ~14.5 hours between workspace change and lockfile

---

### Blocker 2: Missing Routes (EPIC A)

**Commit**: c314964c (from git log)
**Message**: "feat(website): Ship 521 routes - Skills + Learning Hub + CI gates"

**Previous Issue**:
- Route validation failing in CI
- 2 missing routes causing deployment blocks
- Fixed by removing invalid routes from validation

**Evidence**:
- EPIC-B-COMPLETE-EVIDENCE.md mentions route validation fixes
- P0-STABILIZATION-COMPLETE.md (EPIC A: CI/Deploy Unblock)

---

### Blocker 3: Build Syntax Errors

**Commit**: 186f5996 (from git log)
**Message**: "fix(build): Remove renamed learning pages causing syntax errors"

**Issue**:
- Renamed learning pages causing build failures
- Build process couldn't find expected files
- Syntax errors preventing successful compilation

---

## Current Deployment Workflow Analysis

### Expected Workflow Steps:

1. **Trigger**: Push to main OR PR merge to main
2. **Checkout**: Clone repository
3. **Install**: `npm install` or `pnpm install` in marketplace/
4. **Build**: `npm run build` or `astro build`
5. **Deploy**: Upload dist/ to GitHub Pages

### Current Failure Point: INSTALL (Step 3)

**Error**: ERR_PNPM_OUTDATED_LOCKFILE
**Location**: Root workspace install (if using pnpm)
**Impact**: Build never reaches, deploy never triggers

---

## Deployment Requirements (from CLAUDE.md)

### Astro Website Build:

```bash
cd marketplace/
npm install        # Uses npm, not pnpm (has own package.json)
npm run build      # Generates ./dist/
```

**Build Command**: `npm run build`
**Output**: `marketplace/dist/` (static files)
**Expected Size**: ~2MB (optimized bundle)

### GitHub Pages Configuration:

**Source**: `gh-pages` branch OR `dist/` folder
**Custom Domain**: claudecodeplugins.io
**DNS**: Configured via GitHub Pages settings

---

## Analytics Dashboard Removal Impact

### What Was Removed:

```yaml
# Before (pnpm-workspace.yaml):
packages:
  - 'plugins/mcp/*'
  - 'marketplace'
  - 'packages/cli'
  - 'packages/analytics-dashboard'  # ← REMOVED
  - 'packages/analytics-daemon'

# After:
packages:
  - 'plugins/mcp/*'
  - 'marketplace'
  - 'packages/cli'
  - 'packages/analytics-daemon'
```

### Why It Was Blocking Deployment (HYPOTHESIS):

1. **Missing Dependencies**: analytics-dashboard had unresolved deps
2. **Build Failures**: Dashboard compilation failing
3. **Lockfile Conflicts**: Dashboard deps conflicting with other packages
4. **Path Issues**: References to dashboard in other packages

### Current State (UNKNOWN):

- Is `packages/analytics-dashboard/` directory still on disk?
- Is `packages/analytics-daemon/` the correct name or a typo?
- Are there references to analytics-dashboard elsewhere in the codebase?

**Verification Needed**:
```bash
ls -la packages/
# Expected: analytics-daemon present, analytics-dashboard absent
```

---

## Deployment Workflow Triggers

### Current Triggers (INFERENCE):

**On Push to Main**:
- Trigger marketplace build + deploy
- Run validation checks first
- Only deploy if validation passes

**On PR Merge**:
- Same as push to main
- Squash commits preserve history

### Current Blocking Workflow:

**validate-plugins.yml**: FAILING
- All jobs blocked by lockfile mismatch
- Deployment likely gated behind successful validation
- **Result**: No deployment until validation passes

---

## Production Deployment Status

### Last Known Good Deploy:

**Commit**: Unknown (need to check gh-pages branch or workflow history)
**Version**: Unknown
**Date**: Unknown

**To Verify**:
```bash
# Check deployed commit hash
curl -I https://claudecodeplugins.io/ | grep x-github-request-id

# OR check gh-pages branch
git checkout gh-pages
git log -1
```

---

## Deployment Readiness Checklist

Current PR (#199) readiness for deployment:

- ❌ **CI Passing**: All validation jobs must pass
- ❌ **Lockfile Current**: pnpm-lock.yaml must be regenerated
- ✅ **Build Artifacts**: marketplace/dist/ can be generated (locally verified)
- ✅ **Mobile UX**: 100% Playwright test pass rate achieved
- ✅ **Search Fixed**: JavaScript errors resolved
- ❌ **Merged to Main**: Still on feature branch

---

## Next Deployment Steps

### After Lockfile Fix:

1. **Verify CI Green**: All validation jobs pass
2. **Merge PR #199**: Squash merge to main
3. **Monitor Deploy Workflow**: Watch for successful deployment
4. **Verify Production**: Check https://claudecodeplugins.io/
5. **Test Mobile**: Verify 0px horizontal scroll on live site
6. **Test Search**: Verify search functionality works

### If Deploy Fails Again:

1. **Check workflow logs**: Identify specific failure point
2. **Verify package.json**: Ensure marketplace/package.json has correct deps
3. **Check gh-pages branch**: Verify deployment history
4. **Manual deploy**: `npm run build && gh-pages -d dist` (if needed)

---

## Historical Deployment Issues (Summary)

1. **Dec 24**: analytics-dashboard blocking → Removed from workspace
2. **Dec 24**: Missing routes → Fixed in route validation
3. **Dec 24**: Syntax errors from renamed pages → Removed problematic files
4. **Dec 25**: pnpm lockfile mismatch → Awaiting fix

**Pattern**: Deployment has been blocked multiple times by different issues
**Current**: All previous blockers resolved, only lockfile remains

---

**Status**: DEPLOYMENT READY (pending lockfile fix + CI green)
**Confidence**: HIGH (all UX issues resolved, build verified locally)
**Next**: Fix lockfile → Merge PR → Deploy to production
