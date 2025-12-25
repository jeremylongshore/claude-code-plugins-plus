# Website + CLI State Handoff

**Date**: 2025-12-25
**Author**: Claude Sonnet 4.5
**Purpose**: Complete state handoff for P0 stabilization work
**Status**: CI FAILING - Website NOT 100%

---

## PHASE 0 — FREEZE + CAPTURE

### Current Branch State

```bash
$ git branch --show-current
fix-ci-test-failures
```

**Branch Status**: UP TO DATE with origin/fix-ci-test-failures
**Working Tree**: CLEAN (all changes committed)

### Git Status

```bash
$ git status
On branch fix-ci-test-failures
Your branch is up to date with 'origin/fix-ci-test-failures'.

You are in a sparse checkout with 100% of tracked files present.

nothing to commit, working tree clean
```

### Recent Commits (Last 30)

```bash
$ git log --oneline -30
49953a3e chore(ci): Add marketplace and workflow paths to validation triggers
02f79a97 fix(ci): Fix all CI test failures - pnpm, pointer-events, webkit, screenshots
407cab1c feat: EPIC D+E - CLI reliability + workspace hygiene complete
c2a7669a feat(epic-c): 100% mobile test pass rate - homepage UX complete
c1dcdd3f Merge pull request #196 from jeremylongshore/feature/p0-fix-plugin-routes-unified-layout
acde1ffe fix(ux): Center content in Learning Hub feature card
d24284ec Merge pull request #195 from jeremylongshore/feature/p0-fix-plugin-routes-unified-layout
5014b35f fix(ux): Fix search toggle overlap + add installation instructions
e560d3d8 Merge pull request #194 from jeremylongshore/feature/p0-fix-plugin-routes-unified-layout
f7bdca17 fix(build): Fix undefined catalog.categories in plugins index
92b854dd Merge pull request #193 from jeremylongshore/feature/p0-fix-plugin-routes-unified-layout
186f5996 fix(build): Remove renamed learning pages causing syntax errors
94e0cd19 Merge pull request #192 from jeremylongshore/feature/p0-fix-plugin-routes-unified-layout
697c6815 fix(ci): Remove analytics-dashboard from workspace to unblock deployment
f71a963d Merge pull request #191 from jeremylongshore/feature/p0-fix-plugin-routes-unified-layout
b340df6c Merge origin/main into feature/p0-fix-plugin-routes-unified-layout
1f81439f fix(P0): Mobile UX + data integrity + brand consistency
5a98dc4f fix(P0): Plugin routes + unified layout + deploy reliability (#190)
ca201014 docs: Complete P0 implementation report (10,000+ words)
9abeb656 chore: Regenerate data files after optimization
a824a61b perf(skills): Bundle size optimization + route conflict fix
388108c5 feat(P0): Homepage search + /skills reframe + CI validation gates
6b902bd0 fix(P0): Plugin routes + unified layout + deploy reliability
8ca2da37 Merge pull request #189 from jeremylongshore/feature/pnpm-standardization-github-pages
87659538 fix(ci): Exclude tsconfig*.json from strict JSON validation
97975d5e Merge pull request #188 from jeremylongshore/feature/pnpm-standardization-github-pages
1be87e48 feat(P0): Unified Explorer Experience - Site-wide Design System Overhaul
912c8d91 docs: refresh badges and sponsor links
34dcf6f3 Merge remote-tracking branch 'origin/main' into feature/pnpm-standardization-github-pages
ceaf0727 feat(marketplace): Redesign landing page with production features
```

### Tool Versions

```bash
$ node -v && npm -v
v22.20.0
11.7.0

$ pnpm -v
command not found: pnpm
```

**NOTE**: pnpm is NOT available in local shell but IS specified in package.json
**Expected pnpm version**: `pnpm@9.15.9` (from packageManager field in package.json)

### Workspace Configuration

```bash
$ cat pnpm-workspace.yaml
packages:
  - 'plugins/mcp/*'
  - 'marketplace'
  - 'packages/cli'
  - 'packages/analytics-daemon'
```

**ISSUE**: `packages/analytics-dashboard` was removed from workspace (commit 697c6815) but `packages/analytics-daemon` remains. Need to verify if this is correct.

### Root Directory Listing

```bash
$ ls -la (from root: /home/jeremy/000-projects/claude-code-plugins)

total 1208
drwxrwxr-x 27 jeremy jeremy   4096 Dec 25 11:32 .
drwxrwxr-x 40 jeremy jeremy   4096 Dec 23 13:09 ..
drwx------  2 jeremy jeremy   4096 Dec 25 13:34 .beads
drwx------  3 jeremy jeremy   4096 Dec 21 10:19 .claude
drwxrwxr-x  2 jeremy jeremy   4096 Dec 24 22:12 .claude-plugin
-rw-------  1 jeremy jeremy    542 Dec 24 13:44 .dockerignore
drwxrwxr-x 10 jeremy jeremy   4096 Dec 25 13:36 .git
drwxrwxr-x  5 jeremy jeremy   4096 Oct 20 16:20 .github
-rw-rw-r--  1 jeremy jeremy   1477 Dec 25 08:49 .gitignore
-rw-rw-r--  1 jeremy jeremy    578 Dec 24 08:26 .npmignore
-rw-------  1 jeremy jeremy      3 Dec 24 19:26 .nvmrc
drwxrwxr-x  7 jeremy jeremy   4096 Dec 21 14:11 .venv
drwxrwxr-x  2 jeremy jeremy  20480 Dec 24 22:19 000-docs
[...marketplace, node_modules, packages, plugins, scripts, etc...]
drwxrwxr-x 13 jeremy jeremy   4096 Dec 25 10:35 marketplace
-rw-rw-r--  1 jeremy jeremy    993 Dec 24 19:27 package.json
drwx------  6 jeremy jeremy   4096 Dec 24 09:08 packages
-rw-rw-r--  1 jeremy jeremy 236507 Dec 24 08:27 pnpm-lock.yaml
-rw-rw-r--  1 jeremy jeremy     99 Dec 24 22:59 pnpm-workspace.yaml
```

**Key Observations**:
- .nvmrc exists (Node version pinning)
- pnpm-lock.yaml: 236KB (relatively large)
- packages/ directory exists but likely missing analytics-dashboard

### Marketplace Directory Listing

```bash
$ ls -la marketplace/

total 216
drwxrwxr-x 13 jeremy jeremy  4096 Dec 25 10:35 .
drwxrwxr-x 27 jeremy jeremy  4096 Dec 25 11:32 ..
drwxrwxr-x  3 jeremy jeremy  4096 Dec 24 22:01 .astro
-rw-rw-r--  1 jeremy jeremy    78 Dec 25 08:43 .dockerignore
-rw-rw-r--  1 jeremy jeremy   345 Dec 25 08:49 .gitignore
drwxrwxr-x  2 jeremy jeremy  4096 Oct 16 20:17 .vscode
drwxrwxr-x  2 jeremy jeremy  4096 Dec 19 23:32 000-docs
[...build outputs, configs...]
drwxrwxr-x 16 jeremy jeremy  4096 Dec 25 10:34 dist
drwxrwxr-x  9 jeremy jeremy  4096 Dec 25 08:34 node_modules
-rw-rw-r--  1 jeremy jeremy  9756 Dec 25 08:34 package-lock.json
-rw-rw-r--  1 jeremy jeremy   576 Dec 25 08:34 package.json
drwxrwxr-x  2 jeremy jeremy  4096 Dec 25 10:35 playwright-report
-rw-------  1 jeremy jeremy  1738 Dec 25 09:01 playwright.config.ts
drwxrwxr-x  4 jeremy jeremy  4096 Dec 24 08:27 public
drwxrwxr-x  2 jeremy jeremy  4096 Dec 25 08:43 scripts
drwxrwxr-x  8 jeremy jeremy  4096 Dec 21 15:36 src
drwxrwxr-x  3 jeremy jeremy  4096 Dec 25 10:35 test-results
drwxrwxr-x  2 jeremy jeremy  4096 Dec 25 13:30 tests
```

**Key Observations**:
- dist/ exists (built successfully at some point)
- Both pnpm-lock.yaml (root) and package-lock.json (marketplace) exist - potential conflict
- playwright-report/ and test-results/ present - recent test runs
- Marketplace has its own package.json (uses npm, not pnpm)

---

## PHASE 1 — CI FAILURES (EVIDENCE ONLY)

### Last 5 Failing Runs

| Run # | Run URL | Workflow | Job | Failing Step | Error Excerpt (FACT) | Root Cause (FACT) | Root Cause (HYP) | Fix Attempted | Result |
|-------|---------|----------|-----|--------------|---------------------|-------------------|------------------|---------------|--------|
| 1 | [#20509963126](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509963126) | Validate Plugins | test (mcp-plugins) | Install dependencies | `Process completed with exit code 1` (line 14) | pnpm install failed | Dependencies conflict or lockfile out of sync | Removed pnpm version from action-setup | PENDING |
| 2 | [#20509963126](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509963126) | Validate Plugins | test (python-tests) | Run Python tests | `Process completed with exit code 1` (line 84) | Python test execution failed | Missing cryptography module or test failures | None yet | PENDING |
| 3 | [#20509963126](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509963126) | Validate Plugins | test (validation-scripts) | Run validation script tests | `Process completed with exit code 1` (line 364) | Validation scripts failed | Missing files or incorrect paths | None yet | PENDING |
| 4 | [#20509963126](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509963126) | Validate Plugins | cli-smoke-tests | Install CLI dependencies | `Process completed with exit code 1` (line 15) | pnpm install in packages/cli failed | Lockfile out of sync or missing deps | None yet | PENDING |
| 5 | [#20509963126](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509963126) | Validate Plugins | playwright-tests | (Running) | N/A - Not completed yet | Playwright tests not started due to earlier failures | Tests depend on previous jobs | Fixed toggle buttons, webkit clipboard, screenshot size | PENDING |

### Previous Run Failures (Before Current PR)

| Run # | Run URL | Workflow | Job | Failing Step | Error Excerpt (FACT) |
|-------|---------|----------|-----|--------------|---------------------|
| 6 | [#20509031975](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509031975) | Validate Plugins | cli-smoke-tests | Install pnpm | `Error: Multiple versions of pnpm specified: version 9 in the GitHub Action config with the key "version", version pnpm@9.15.9+sha512... in the package.json with the key "packageManager"` | FIXED ✅ |
| 7 | [#20509031975](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509031975) | Validate Plugins | playwright-tests | debug-search.spec.ts | `Test timeout of 30000ms exceeded. [...] <button data-type="all" class="toggle-btn active"> from <div class="search-toggle"> subtree intercepts pointer events` | FIXED ✅ (removed debug test + fixed pointer-events) |
| 8 | [#20509031975](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509031975) | Validate Plugins | playwright-tests | T1-homepage-search-redirect.spec.ts | `Error: page.screenshot: Cannot take screenshot larger than 32767 pixels on any dimension` | FIXED ✅ (changed fullPage to false) |
| 9 | [#20509031975](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509031975) | Validate Plugins | playwright-tests | T4-install-cta.spec.ts (webkit) | `browserContext.grantPermissions: Unknown permission: clipboard-write` | FIXED ✅ (added webkit check) |

**Summary**:
- Runs #6-9 had specific errors that were addressed in commits 02f79a97 and 49953a3e
- Run #1-5 (current PR) now failing on DIFFERENT issues (pnpm install, python tests, validation scripts)
- Playwright tests haven't run yet due to dependency failures

---

## PHASE 2 — LOCAL REPRO RUNBOOK

### Prerequisites

**Node Version**:
```bash
$ cat .nvmrc
22
```
Expected: Node.js v22.x

**pnpm Version**:
```bash
$ grep packageManager package.json
"packageManager": "pnpm@9.15.9+sha512.68046141893c66fad01c079231128e9afb89ef87e2691d69e4d40eee228988295fd4682181bae55b58418c3a253bde65a505ec7c5f9403ece5cc3cd37dcf2531",
```
Expected: pnpm 9.15.9 (with exact hash)

**Installation**:
```bash
corepack enable
corepack prepare pnpm@9.15.9 --activate
```

### Clean Install Steps (From Scratch)

```bash
# 1. Clone repo
git clone https://github.com/jeremylongshore/claude-code-plugins-plus-skills.git
cd claude-code-plugins-plus-skills

# 2. Checkout fix branch
git checkout fix-ci-test-failures

# 3. Install Node 22
nvm install 22
nvm use 22

# 4. Enable pnpm via corepack
corepack enable
corepack prepare pnpm@9.15.9 --activate

# 5. Install dependencies (ROOT)
pnpm install --frozen-lockfile

# 6. Build MCP plugins
pnpm build

# 7. Build CLI
cd packages/cli
pnpm build
cd ../..

# 8. Install marketplace dependencies (uses npm, not pnpm)
cd marketplace
npm install
npm run build
cd ..

# 9. Run validation scripts
./scripts/validate-all-plugins.sh

# 10. Run Playwright tests
cd marketplace
npx playwright install --with-deps chromium webkit
npx playwright test --project=chromium-desktop
npx playwright test --project=webkit-mobile
```

### Expected Artifacts

**Build Outputs**:
- `plugins/mcp/*/dist/` - Compiled MCP plugins
- `packages/cli/dist/` - Compiled CLI tool
- `marketplace/dist/` - Built Astro website

**Test Reports**:
- `marketplace/test-results/` - Playwright test results
- `marketplace/playwright-report/` - HTML test report

**Serve Locally**:
```bash
cd marketplace
npm run preview  # Serves dist/ on localhost:4321
```

---

## PHASE 3 — WEBSITE BUG LIST

### Bug 1: Homepage Search Bar Cannot Type (CRITICAL)

**URL**: `/` (homepage)

**Expected Behavior**:
- User clicks search bar
- User types search query
- Search results appear inline below input

**Actual Behavior**:
- Search input is clickable
- Typing works (inline search shows results)
- **BUT USER EXPECTS**: Search should redirect to `/explore` page instead of inline results

**User Quote**:
> "im typing in the search bar o thought we were resircint tht as a oush button thag went to skills search page"

**Root Cause**:
- EPIC C work FIXED inline search functionality (commit 86e4d4a5)
- User expectation: Search bar should be a REDIRECT BUTTON to /explore
- **CONFLICT**: Implementation restored inline search vs requirement for redirect button

**Suspected Files**:
- `marketplace/src/pages/index.astro` (lines 700-750: search input HTML)
- `marketplace/src/pages/index.astro` (lines 1000-1100: search JavaScript)

**Reproduction**:
1. Navigate to homepage
2. Click search input
3. Type any query (e.g., "prettier")
4. Observe inline results appear (CURRENT BEHAVIOR)
5. User expects redirect to /explore page (EXPECTED BEHAVIOR)

**Fix Required**:
- Remove inline search functionality
- Convert search input to button that redirects to `/explore?q={query}`
- OR provide explicit redirect button alongside search

---

### Bug 2: Toggle Buttons Overlap/Block Search Input (DESKTOP)

**URL**: `/` (homepage)
**Viewport**: Desktop (≥640px)

**Expected Behavior**:
- Search input is clickable across full width
- Toggle buttons (All/Plugins/Skills) visible but don't block input

**Actual Behavior**:
- Toggle buttons positioned absolutely with `z-index: 10`
- Buttons intercept pointer events, blocking search input clicks
- **FIXED** in commit 02f79a97 (pointer-events: none on container, auto on buttons)

**Status**: ✅ FIXED (awaiting CI verification)

**Suspected Files**:
- `marketplace/src/pages/index.astro` (lines 268-300: search-toggle CSS)

---

### Bug 3: Mobile Layout White Gaps / Horizontal Scroll

**URL**: `/` (homepage)
**Viewport**: Mobile (390x844px iPhone 13, 393x851px Pixel 5)

**Expected Behavior**:
- No horizontal scroll on mobile
- All content within viewport width
- 0px overflow

**Actual Behavior**:
- **FIXED** in EPIC C (commit 885b84ed, 809bb5b2)
- Achieved 0px overflow (bodyWidth: 393px on 393px viewport)
- 21/21 Playwright tests passing (100%)

**Status**: ✅ FIXED (verified via Playwright tests)

**Evidence**:
- `EPIC-C-COMPLETE-EVIDENCE.md` (lines 98-106)
- Test suite: `marketplace/tests/T3-mobile-viewport.spec.ts`

---

### Bug 4: "Provided By" Section Confusion

**URL**: Various plugin pages
**Issue**: Unclear ownership/attribution

**Expected Behavior**:
- Clear indication of plugin author/maintainer
- Consistent "Provided by" section across all plugin pages

**Actual Behavior**:
- (Need to investigate - not yet documented in evidence files)

**Status**: 🔍 NEEDS INVESTIGATION

---

### Bug 5: Missing "Package Manager / CLI Install" Marketing (Homepage)

**URL**: `/` (homepage)

**Expected Behavior**:
- Prominent section explaining how to install plugins via CLI
- Instructions for package manager setup
- Marketing copy about ease of installation

**Actual Behavior**:
- "Quick Install" section exists (lines 600-700 in index.astro)
- Install boxes display correctly (T4 tests passing)
- **BUT**: May lack marketing emphasis or prominence

**Status**: 🔍 NEEDS UX REVIEW

**Suspected Files**:
- `marketplace/src/pages/index.astro` (lines 600-700: install boxes)

---

## PHASE 4 — PACKAGE/WORKSPACE/LOCKFILE SITUATION

### The `analytics-dashboard` Removal

**What Happened**:

**Commit 697c6815** (Dec 24, 22:59):
```
fix(ci): Remove analytics-dashboard from workspace to unblock deployment
```

**Changes Made**:
1. Removed `packages/analytics-dashboard` from `pnpm-workspace.yaml`
2. Left pnpm-lock.yaml UNCHANGED (236KB, dated Dec 24 08:27 - BEFORE removal)

**pnpm-workspace.yaml (Current State)**:
```yaml
packages:
  - 'plugins/mcp/*'
  - 'marketplace'
  - 'packages/cli'
  - 'packages/analytics-daemon'  # ← Still present
```

**Questions**:

1. **Is `packages/analytics-dashboard` physically deleted?**
   - UNKNOWN (not visible in ls -la output of packages/)
   - Need to verify: `ls -la packages/`

2. **Is pnpm-lock.yaml inconsistent?**
   - HIGHLY LIKELY: Lockfile dated BEFORE workspace removal
   - Evidence: pnpm-lock.yaml (Dec 24 08:27) vs workspace change (Dec 24 22:59)
   - **EXPECTED ERROR**: Running `pnpm install --frozen-lockfile` should fail if lockfile references removed workspace member

3. **Is `packages/analytics-daemon` correct or should it be removed too?**
   - Workspace lists `analytics-daemon` (not `analytics-dashboard`)
   - POSSIBLE TYPO or intentional distinction?
   - Need clarification from repository owner

### The Correct Fix (HYPOTHESIS)

**If analytics-dashboard was legitimately removed**:

```bash
# 1. Verify removal
ls -la packages/  # Should NOT show analytics-dashboard

# 2. Update lockfile (REQUIRED)
pnpm install  # WITHOUT --frozen-lockfile to regenerate

# 3. Commit new lockfile
git add pnpm-lock.yaml
git commit -m "chore: Update pnpm-lock.yaml after analytics-dashboard removal"
```

**If analytics-dashboard needs to be restored**:

```bash
# 1. Restore workspace entry
# Edit pnpm-workspace.yaml to add 'packages/analytics-dashboard'

# 2. Run install
pnpm install --frozen-lockfile  # Should work with existing lockfile

# 3. Verify builds
pnpm build
```

### Evidence of Lockfile Issue (PREDICTION)

**Expected CI Error** (if lockfile is stale):
```
ERR_PNPM_OUTDATED_LOCKFILE
```

**Actual CI Error** (from Run #20509963126):
```
Process completed with exit code 1
(test (mcp-plugins): Install dependencies step)
```

**HYPOTHESIS**: Exit code 1 is likely pnpm lockfile mismatch, not dependency resolution failure.

### CLI Publishing Blockers

**Is CLI Published?**
- UNKNOWN (no npm registry check performed)
- Package name: `@claude-code-plugins/ccp` (from packages/cli/package.json)

**Check Publishing Status**:
```bash
npm view @claude-code-plugins/ccp
# Expected: Either 404 (unpublished) or version info
```

**Blockers to Publishing**:
1. ✅ Bin entrypoint verified (EPIC D)
2. ✅ No workspace: dependencies (EPIC D)
3. ✅ CI smoke tests added (EPIC D)
4. ❌ CI currently FAILING (all tests must pass before publish)
5. ❌ Lockfile likely inconsistent (blocks clean builds)

**Recommendation**: FIX CI FIRST, then publish CLI after all tests green.

---

## PHASE 5 — "READY FOR ME TO FIX" CHECKLIST

### A) Links

**Pull Request**:
- [PR #199: fix(ci): Fix all CI test failures - website 100%](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/199)

**Failing Runs**:
- [Run #20509963126](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509963126) (Current PR - IN PROGRESS)
- [Run #20509031975](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/20509031975) (main branch - FAILED)

**Preview Build URL**:
- No Netlify/Vercel preview configured
- GitHub Pages deployment: https://claudecodeplugins.io/
- Build from commit: 407cab1c (main branch, Dec 25 18:11)

**Production URL**:
- https://claudecodeplugins.io/

### B) What I Need From You

**1. Clarify Search Bar Requirement** (CRITICAL):
- Should homepage search be:
  - **Option A**: Inline search with results (current implementation after EPIC C)
  - **Option B**: Redirect button to /explore page (user's stated expectation)
  - **Option C**: Hybrid (inline search + explicit "Browse All" button)

**2. Confirm `analytics-dashboard` Removal**:
- Is `packages/analytics-dashboard` intentionally deleted?
- Is `packages/analytics-daemon` the correct name (not a typo)?
- Should I regenerate pnpm-lock.yaml or restore the workspace member?

**3. Approve pnpm-lock.yaml Regeneration**:
- Current lockfile likely stale (dated before workspace change)
- Need permission to run `pnpm install` (without --frozen-lockfile) and commit new lock

### C) Next 3 Commits (NOT IMPLEMENTED YET)

**Commit 1: Fix pnpm Lockfile Inconsistency**
```bash
# Navigate to root
cd /home/jeremy/000-projects/claude-code-plugins

# Regenerate lockfile
pnpm install

# Verify no unexpected changes
git diff pnpm-lock.yaml | head -100

# Commit if clean
git add pnpm-lock.yaml
git commit -m "chore: Regenerate pnpm-lock.yaml after workspace changes"
git push
```

**Commit 2: Fix Remaining CI Failures (Python/Validation Scripts)**
```bash
# Install Python dependencies
cd /home/jeremy/000-projects/claude-code-plugins
pip install -r requirements.txt  # If exists

# Run validation scripts locally to identify failures
./scripts/validate-all-plugins.sh

# Fix any missing dependencies or script errors
# (Specific fixes depend on error output)

git add <fixed-files>
git commit -m "fix(ci): Resolve python-tests and validation-scripts failures"
git push
```

**Commit 3: Implement Search Bar Redirect (If User Chooses Option B)**
```bash
# Edit homepage to convert search to redirect button
cd marketplace/src/pages/index.astro

# Remove inline search JavaScript (lines ~1000-1100)
# Convert input to button with href="/explore"
# OR add prominent "Browse All Skills" button

git add src/pages/index.astro
git commit -m "feat(ux): Convert homepage search to /explore redirect"
git push
```

---

## APPENDIX: File References

### Key Configuration Files

- `.github/workflows/validate-plugins.yml` - CI workflow (lines 1-10: triggers, 230-240: pnpm setup, 530-616: CLI smoke tests)
- `pnpm-workspace.yaml` - Workspace members (currently missing analytics-dashboard)
- `package.json` (root) - Defines packageManager: pnpm@9.15.9
- `marketplace/package.json` - Uses npm (not pnpm)
- `marketplace/playwright.config.ts` - Test configuration

### Key Evidence Files

- `P0-STABILIZATION-COMPLETE.md` - Master evidence for EPICs A-E
- `EPIC-C-COMPLETE-EVIDENCE.md` - 100% mobile test pass rate evidence
- `EPIC-B-COMPLETE-EVIDENCE.md` - Virtual env + Playwright setup
- `marketplace/tests/T1-homepage-search-redirect.spec.ts` - Search tests
- `marketplace/tests/T4-install-cta.spec.ts` - Install box tests

### Suspected Problem Files

- `marketplace/src/pages/index.astro` (lines 700-750, 1000-1100: search implementation)
- `marketplace/src/pages/index.astro` (lines 268-300: toggle button CSS)
- `marketplace/src/pages/index.astro` (lines 600-700: install boxes)

---

## STATUS SUMMARY

**Branch**: fix-ci-test-failures
**PR**: #199
**CI Status**: ❌ FAILING (4 jobs)

**Blockers**:
1. pnpm lockfile inconsistency (HYPOTHESIS - needs verification)
2. Python test failures (unknown cause - need logs)
3. Validation script failures (unknown cause - need logs)
4. Search bar UX mismatch (inline results vs redirect requirement)

**Ready to Fix**: YES (with user input on search bar requirement + lockfile regeneration approval)

**Estimated Next Actions**:
1. Get user approval for lockfile regeneration
2. Run `pnpm install` and commit new lock
3. Debug python-tests and validation-scripts failures (need CI logs)
4. Clarify and implement search bar requirement
5. Verify all CI jobs pass (target: 100% green)

---

**End of Handoff**
**Next Update**: After user clarifications + CI results from current PR
