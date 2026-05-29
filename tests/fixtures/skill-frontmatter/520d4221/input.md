---
name: pr-review
description: |
  Orchestrates a multi-AI PR review pipeline for large open-source repositories.
  Mirrors upstream PRs on a fork, collects reviews from 5+ AI bots (CodeRabbit,
  Gemini, Greptile, CodeQL, Qodo), runs full test suites via Codespace, and
  composes structured review + journal artifacts with audit trail.
  Use when reviewing PRs, clearing PR backlogs, or validating contributor fixes.
  Trigger with "/pr-review", "review PR", "review pipeline", "next PR".
allowed-tools: 'Read,Write,Edit,Bash(gh:*,git:*,curl:*,jq:*,sleep:*,base64:*,wc:*,mkdir:*,cat:*,echo:*,sqlite3:*,tee:*,tail:*,grep:*,head:*),Glob,Grep,Task,AskUserQuestion,WebFetch'
license: 'MIT'
metadata:
  author: 'Jeremy Longshore <jeremy@intentsolutions.io>'
  version: '1.7.0'
  tier: enterprise
  category: automation
---

# Multi-AI PR Review Pipeline

Automated PR review system using 5+ independent AI reviewers on a fork,
with structured review artifacts, fix validation, and full audit trail.
Applicable to any large open-source repository.

## Overview

This skill runs the complete PR review pipeline:

1. Pick PR from priority queue
2. Mirror on fork via Codespace (proper cherry-pick)
3. Collect bot reviews (CodeRabbit, Gemini, Greptile, CodeQL, Qodo)
4. **Merge locally and run full test suite** (MANDATORY for ALL tiers)
   4b. **Combined integration test** (after batch reviews — merge all PRs together)
5. Analyze diff + synthesize bot findings + test results
6. Compose review (Comment 1: machine-parseable) + journal (Comment 2: human narrative)
7. Validate fixes if changes requested
8. Quality gate (tone lint, metadata check, test evidence)
9. Human approves
10. Submit to upstream with links to fork evidence + test results

**CORE PRINCIPLE**: Every PR gets merged on our fork and tested. No review
is complete without proof that we ran the code. This is what separates
a real review from a drive-by "LGTM".

## Directory Convention

Forked repos follow the standard convention from the bounty skill:

```
~/000-projects/99-forked/<owner>/<repo>/       # Local clone of fork
~/000-projects/99-forked/<owner>/<repo>/.reviews/  # Review artifacts live IN the fork
```

Example:

```
~/000-projects/99-forked/Kilo-Org/kilocode/
~/000-projects/99-forked/Kilo-Org/kilocode/.reviews/
~/000-projects/99-forked/Kilo-Org/kilocode/.reviews/config.json
~/000-projects/99-forked/Kilo-Org/kilocode/.reviews/priority-queue.json
~/000-projects/99-forked/Kilo-Org/kilocode/.reviews/METHODOLOGY.md
~/000-projects/99-forked/Kilo-Org/kilocode/.reviews/PROGRESS.md
~/000-projects/99-forked/Kilo-Org/kilocode/.reviews/PR-5667/
~/000-projects/99-forked/Kilo-Org/kilocode/.reviews/PR-5667/kilocode-5667-review.md
~/000-projects/99-forked/Kilo-Org/kilocode/.reviews/PR-5667/kilocode-5667-journal.md
~/000-projects/99-forked/Kilo-Org/kilocode/.reviews/PR-5667/status.json
```

NOT every repo gets its own project directory. Forked repos are centralized in `000-forked`.

## Prerequisites

### Required

- `gh` CLI authenticated with `codespace` scope
- Fork of the target repo with bots installed:
  - CodeRabbit (GitHub App, free for public repos)
  - Gemini Code Assist (GitHub App, free)
  - Greptile (GitHub App, $20/mo)
  - CodeQL (GitHub Action on fork, free)
  - Qodo PR-Agent (GitHub Action on fork, free, needs OPENAI_API_KEY)
- GitHub Codespace on fork (for build/test/push with proper hooks)
- SSHD feature added to fork's devcontainer.json

### Project Config File

Each deployment needs a `.reviews/config.json` in the fork:

```json
{
  "upstream": "Kilo-Org/kilocode",
  "fork": "jeremylongshore/kilocode",
  "repo_short": "kilocode",
  "codespace_machine": "premiumLinux",
  "codespace_name": "kilo-review-pipeline",
  "reviews_dir": ".reviews",
  "bots": ["coderabbit", "gemini", "greptile", "codeql", "qodo"],
  "checklist": [
    "correctness",
    "conventions",
    "changeset",
    "tests",
    "i18n",
    "types",
    "security",
    "scope"
  ],
  "methodology_url": "https://github.com/jeremylongshore/ai-pr-review-methodology"
}
```

### Review Tracking Database (SQLite)

Every review is tracked in `{reviewsDir}/db/reviews.db`. Initialize if missing:

```bash
sqlite3 {reviewsDir}/db/reviews.db << 'SQL'
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pr_number INTEGER NOT NULL,
  repo TEXT NOT NULL,
  title TEXT, author TEXT, category TEXT, tier INTEGER,
  total_lines INTEGER, files INTEGER,
  verdict TEXT,  -- APPROVE, COMMENT, REQUEST_CHANGES
  confidence INTEGER, fork_pr_url TEXT,
  upstream_review_comment_id TEXT, upstream_journal_comment_id TEXT,
  phase TEXT DEFAULT 'ready',  -- ready, submitted, posted
  started_at TEXT, completed_at TEXT, submitted_at TEXT,
  lessons TEXT, created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  review_id INTEGER REFERENCES reviews(id),
  pr_number INTEGER NOT NULL,
  comment_type TEXT NOT NULL, github_comment_id TEXT,
  posted_at TEXT, link_verified INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS bot_findings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  review_id INTEGER REFERENCES reviews(id),
  pr_number INTEGER NOT NULL,
  bot_name TEXT NOT NULL, status TEXT, finding_count INTEGER DEFAULT 0,
  summary TEXT, created_at TEXT DEFAULT (datetime('now'))
);
SQL
```

After each review, insert a row:

```bash
sqlite3 {reviewsDir}/db/reviews.db "INSERT INTO reviews (pr_number, repo, title, author, category, tier, total_lines, files, verdict, confidence, fork_pr_url, phase, completed_at) VALUES ({NUM}, '{UPSTREAM}', '{TITLE}', '{AUTHOR}', '{CATEGORY}', {TIER}, {LINES}, {FILES}, '{VERDICT}', {CONFIDENCE}, '{FORK_PR}', 'ready', datetime('now'));"
```

After posting to upstream, update:

```bash
sqlite3 {reviewsDir}/db/reviews.db "UPDATE reviews SET phase='submitted', upstream_review_comment_id='{REVIEW_ID}', upstream_journal_comment_id='{JOURNAL_ID}', submitted_at=datetime('now') WHERE pr_number={NUM};"
```

Dashboard query:

```bash
sqlite3 -header -column {reviewsDir}/db/reviews.db "SELECT verdict, COUNT(*) as count FROM reviews GROUP BY verdict;"
sqlite3 -header -column {reviewsDir}/db/reviews.db "SELECT phase, COUNT(*) as count FROM reviews GROUP BY phase;"
```

### Link Verification

**CRITICAL: No 404s in anything we post.**

- Methodology link MUST point to fork: `https://github.com/{FORK}/tree/main/.reviews`
- NEVER link to upstream `.reviews` — it doesn't exist there
- All fork PR links must be verified before posting
- After posting, verify every link resolves

### Cross-References

- Fork management patterns: see `/bounty` skill (same `000-projects/99-forked` convention)
- Evidence gates: see `/bounty` skill (gates-and-checks reference)
- Slack notifications: see `/slack` skill

## Instructions

### Invocation

When user says `/pr-review`, present the command menu:

```
PR REVIEW PIPELINE
===================================================================

What would you like to do?

1. Review next PR      - Pick next from priority queue
2. Review PR #N        - Review a specific PR
3. Check bot status    - See bot reviews on current fork PR
4. Submit review       - Post review + journal to upstream
5. Validate fix        - Test a fix after review comments
6. Pipeline status     - Show progress across all PRs
```

Use AskUserQuestion to let the user choose.

---

### PHASE 1: SELECT PR

#### Option A: Next from queue

```bash
# Read priority queue
cat {reviewsDir}/priority-queue.json | jq '[.[] | select(.status == "pending")] | sort_by(.tier) | .[0]'
```

#### Option B: Specific PR number

User provides PR number directly.

#### For both:

```bash
# Fetch upstream metadata
gh pr view {NUM} --repo {UPSTREAM} \
  --json number,title,body,author,files,commits,comments,reviews,additions,deletions,changedFiles,createdAt,mergeable,reviewDecision,labels

# Fetch diff
gh pr diff {NUM} --repo {UPSTREAM}

# Fetch CI status
gh pr checks {NUM} --repo {UPSTREAM}

# CRITICAL: Read ALL existing comments and reviews on the PR
gh pr view {NUM} --repo {UPSTREAM} --json comments --jq '.comments[] | "[\(.author.login)] \(.body)"'
gh pr view {NUM} --repo {UPSTREAM} --json reviews --jq '.reviews[] | "[\(.author.login)] [\(.state)] \(.body)"'
```

**MANDATORY**: Read and understand ALL existing comments before writing your review.
This includes maintainer feedback, contributor responses, bot reviews, and any
unresolved discussions. Your review must acknowledge and build on existing context,
not duplicate or contradict it.

Save to `{reviewsDir}/PR-{NUM}/metadata.json`.

#### Tier Classification

| Tier | Category     | Verification Level                              |
| ---- | ------------ | ----------------------------------------------- |
| 1    | Docs only    | CI only                                         |
| 2    | Config/deps  | CI + changelog                                  |
| 3    | Bug fix      | CI + targeted tests + blast radius              |
| 4    | Feature      | CI + full tests + architecture review           |
| 5    | Provider/API | CI + full build + security + pattern compliance |
| 6    | Refactor     | CI + full build + regression tests              |

Update `{reviewsDir}/PR-{NUM}/status.json`:

```json
{
  "pr": {NUM},
  "phase": "in_progress",
  "started_at": "{ISO_TIMESTAMP}"
}
```

---

### PHASE 2: MIRROR ON FORK

This phase uses GitHub Codespaces for proper builds and hooks.

#### Step 2.1: Ensure Codespace exists

```bash
# Check for existing codespace
CS=$(gh codespace list --json name,state -q '.[] | select(.name | startswith("{CODESPACE_NAME}")) | .name')

if [ -z "$CS" ]; then
  # Create new codespace
  CS=$(gh codespace create --repo {FORK} --branch main --machine {MACHINE} --display-name "{CODESPACE_NAME}")
  # Wait for it to be available
  while [ "$(gh codespace view -c $CS --json state -q '.state')" != "Available" ]; do
    sleep 10
  done
  # Install deps and auth
  TOKEN=$(gh auth token)
  gh codespace ssh -c $CS -- "echo '$TOKEN' | gh auth login --with-token && gh auth setup-git && cd /workspaces/{REPO} && pnpm install"
fi

# Start if stopped
STATE=$(gh codespace view -c $CS --json state -q '.state')
if [ "$STATE" = "Shutdown" ]; then
  gh codespace ssh -c $CS -- "echo 'Starting...'"
fi
```

#### Step 2.2: Cherry-pick PR commits

```bash
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  git remote add upstream https://github.com/{UPSTREAM}.git 2>/dev/null || true &&
  git fetch upstream pull/{NUM}/head:review/PR-{NUM} &&
  git checkout review/PR-{NUM} &&
  git push origin review/PR-{NUM}
"
```

**CRITICAL**: Always use `git fetch upstream pull/{NUM}/head` to get exact commits.
Never use GitHub Contents API (creates wrong diffs - full file replacement instead of incremental).

#### Step 2.3: Create fork PR

```bash
gh pr create --repo {FORK} \
  --head review/PR-{NUM} \
  --base main \
  --title "Mirror: {TITLE} (#{NUM})" \
  --body "$(cat <<EOF
## Mirror of {UPSTREAM}#{NUM}

| Field | Value |
|-------|-------|
| Upstream PR | [#{NUM}](https://github.com/{UPSTREAM}/pull/{NUM}) |
| Author | @{AUTHOR} |
| Category | {CATEGORY} |
| Tier | {TIER} |
| Size | {LINES} lines, {FILES} files |

This PR mirrors the upstream change for multi-AI review analysis.

### Bot Review Tracker
- [ ] CodeRabbit
- [ ] Gemini Code Assist
- [ ] Greptile
- [ ] CodeQL
- [ ] Qodo PR-Agent

### Links
- Upstream PR: https://github.com/{UPSTREAM}/pull/{NUM}
EOF
)"
```

#### Step 2.4: Verify diff accuracy

```bash
# Compare fork diff to upstream diff - they must match
gh pr diff {FORK_PR_NUM} --repo {FORK}
```

#### Step 2.5: Stop codespace (save costs)

```bash
gh codespace stop -c $CS
```

Update `status.json`: `"phase": "waiting_for_bots"`, `"fork_pr": "{FORK_PR_URL}"`

---

### PHASE 3: COLLECT BOT REVIEWS

Wait 2-5 minutes for bots to comment on the fork PR.

```bash
# Poll for bot reviews
while true; do
  COMMENTS=$(gh pr view {FORK_PR_NUM} --repo {FORK} --json comments -q '.comments | length')
  REVIEWS=$(gh api repos/{FORK}/pulls/{FORK_PR_NUM}/reviews -q 'length')
  echo "Comments: $COMMENTS, Reviews: $REVIEWS"

  # Check which bots have responded
  gh pr view {FORK_PR_NUM} --repo {FORK} --json comments -q '.comments[] | .author.login' | sort -u

  if [ $COMMENTS -ge 3 ]; then
    echo "Sufficient bot reviews collected"
    break
  fi
  sleep 30
done
```

Read each bot's review:

```bash
# CodeRabbit
gh pr view {FORK_PR_NUM} --repo {FORK} --json comments -q '.comments[] | select(.author.login == "coderabbitai") | .body'

# Gemini
gh pr view {FORK_PR_NUM} --repo {FORK} --json comments -q '.comments[] | select(.author.login == "gemini-code-assist") | .body'
gh api repos/{FORK}/pulls/{FORK_PR_NUM}/reviews -q '.[] | select(.user.login == "gemini-code-assist[bot]") | .body'

# Greptile
gh api repos/{FORK}/pulls/{FORK_PR_NUM}/reviews -q '.[] | select(.user.login == "greptile[bot]") | .body'

# Qodo
gh pr view {FORK_PR_NUM} --repo {FORK} --json comments -q '.comments[] | select(.author.login == "github-actions") | .body'
```

Update `status.json` with `bot_findings` for each bot.

---

### PHASE 4: ANALYZE

Read the following in parallel:

1. Upstream diff (`gh pr diff {NUM} --repo {UPSTREAM}`)
2. Files the PR touches on main branch
3. Surrounding code, tests, related files
4. Bot review findings from Phase 3
5. Linked issues (`gh issue view {ISSUE_NUM} --repo {UPSTREAM}`)

For Tier 3+: 6. Sourcegraph blast radius: search callers of modified functions
`https://sourcegraph.com/search?q=repo:{UPSTREAM}+{FUNCTION_NAME}`

Work through the diff line by line. Cross-reference bot findings.
Note agreements, disagreements, false positives.

---

### PHASE 5: COMPOSE ARTIFACTS

#### Comment 1: Review (machine-parseable)

Write `{reviewsDir}/PR-{NUM}/{REPO_SHORT}-{NUM}-review.md`:

```markdown
<!-- PR-REVIEW-META
repo: {UPSTREAM}
pr: {NUM}
title: "{TITLE}"
author: {AUTHOR}
category: {CATEGORY}
tier: {TIER}
lines: {LINES}
files: {FILES}
verdict: {VERDICT}
confidence: {CONFIDENCE}
reviewed_at: {DATE}
linked_issue: {ISSUE}
fork_pr: {FORK_PR_URL}
-->

# Review: {REPO_SHORT} #{NUM}

> **{TITLE}** by @{AUTHOR}
> Multi-AI analysis: [Fork PR]({FORK_PR_URL}) -- reviewed by CodeRabbit, Gemini, Greptile, CodeQL, Qodo

## Checklist

| Check | Result | Notes |
| ----- | ------ | ----- |

[Fill each check from config.checklist]

## Findings

[Structured findings with severity, file:line, description]
[Include bot consensus]

## CI Status

| Check | Result |
| ----- | ------ |

[From gh pr checks]

## Local Verification

We merged this PR on our fork and ran the full test suite.

| Test       | Command                    | Result      | Details                       |
| ---------- | -------------------------- | ----------- | ----------------------------- |
| TypeScript | `pnpm check-types`         | {PASS/FAIL} | {X}/{Y} packages              |
| Lint       | `pnpm lint`                | {PASS/FAIL} | {X}/{Y} packages              |
| Unit Tests | `pnpm test`                | {PASS/FAIL} | {N} tests, {F} failures       |
| Targeted   | `pnpm test --filter {pkg}` | {PASS/FAIL} | {N} tests in affected package |

Raw logs: [`check-types`](https://github.com/{FORK}/blob/review/PR-{NUM}/.reviews/logs/PR-{NUM}-check-types.log) | [`lint`](https://github.com/{FORK}/blob/review/PR-{NUM}/.reviews/logs/PR-{NUM}-lint.log) | [`test`](https://github.com/{FORK}/blob/review/PR-{NUM}/.reviews/logs/PR-{NUM}-test.log)

> Tested on fork branch [`review/PR-{NUM}`](https://github.com/{FORK}/tree/review/PR-{NUM})

## Code Snippets

[Key changes with context]

## Verdict

[APPROVE / REQUEST_CHANGES / COMMENT with rationale]
```

#### Comment 2: Journal (human narrative)

Write `{reviewsDir}/PR-{NUM}/{REPO_SHORT}-{NUM}-journal.md`:

```markdown
<!-- PR-JOURNAL-META
repo: {UPSTREAM}
pr: {NUM}
title: "{TITLE}"
author: {AUTHOR}
category: {CATEGORY}
tier: {TIER}
lines: {LINES}
files: {FILES}
review_number: {REVIEW_NUM}
fork_pr: {FORK_PR_URL}
-->

# Review Journal: {REPO_SHORT} #{NUM}

> **PR**: [#{NUM}](https://github.com/{UPSTREAM}/pull/{NUM}) |
> **Title**: {TITLE} |
> **Author**: @{AUTHOR} |
> **Category**: {CATEGORY} | **Tier**: {TIER} | **Size**: {LINES} lines, {FILES} files

## Summary

## First Impressions

## What I Looked At

## Analysis

## Verification

## Diagrams

## Bot Review Synthesis

| Bot | Verdict | Key Finding | Useful? |
| --- | ------- | ----------- | ------- |

## Lessons Learned

---

<sub>Review #{REVIEW_NUM} | [Multi-AI analysis]({FORK_PR_URL}) | Reviewed with Claude Code + 5 AI reviewers</sub>
```

---

### PHASE 6: LOCAL VERIFICATION (MANDATORY — ALL TIERS)

**Every PR gets merged on our fork and tested. No exceptions.**

This is the proof of work. Without test results, the review is incomplete.
We're not just reading the diff — we're running the code.

#### Step 6.1: Merge PR on fork branch

```bash
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  git checkout review/PR-{NUM} &&
  git pull origin review/PR-{NUM}
"
```

#### Step 6.2: Run full test suite with log capture

**CRITICAL**: Capture raw output to log files on the codespace. These get committed
to the review branch as public evidence — anyone can click the link and verify.

**IMPORTANT**: Do NOT use `run_in_background` for codespace SSH commands. Tests run
remotely on the codespace, not locally. We need the results before continuing, and
background mode just causes timeouts and duplicate work.

```bash
# Create logs directory on codespace
gh codespace ssh -c $CS -- "mkdir -p /workspaces/{REPO}/.reviews/logs"

# Run each step separately, capturing to individual log files
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  git checkout review/PR-{NUM} &&
  pnpm run check-types 2>&1 | tee .reviews/logs/PR-{NUM}-check-types.log
"

gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  pnpm run lint 2>&1 | tee .reviews/logs/PR-{NUM}-lint.log
"

gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  pnpm test --continue 2>&1 | tee .reviews/logs/PR-{NUM}-test.log
"
# NOTE: --continue is essential — some packages (e.g. core-schemas) may have
# pre-existing no-test-files errors that halt the suite without it.
```

#### Step 6.3: Commit and push log files as evidence

```bash
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  git add .reviews/logs/PR-{NUM}-*.log &&
  git commit -m 'evidence: test logs for PR #{NUM}' &&
  git push origin review/PR-{NUM}
"
```

Log files become publicly visible at:

- `https://github.com/{FORK}/blob/review/PR-{NUM}/.reviews/logs/PR-{NUM}-check-types.log`
- `https://github.com/{FORK}/blob/review/PR-{NUM}/.reviews/logs/PR-{NUM}-lint.log`
- `https://github.com/{FORK}/blob/review/PR-{NUM}/.reviews/logs/PR-{NUM}-test.log`

#### Step 6.3b: Terminal recordings (optional, tier 3+)

For high-value reviews, capture terminal recordings as visual proof:

```bash
# Install asciinema on codespace (one-time)
gh codespace ssh -c $CS -- "pip install asciinema"

# Record test run as .cast file
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  asciinema rec .reviews/logs/PR-{NUM}-test.cast \
    --command 'pnpm test --continue' \
    --title 'PR #{NUM} test suite' \
    --idle-time-limit 2
"

# Upload to asciinema.org for embeddable player (optional)
gh codespace ssh -c $CS -- "
  asciinema upload .reviews/logs/PR-{NUM}-test.cast
"
```

The `.cast` file can be played locally with `asciinema play` or embedded in
review comments via asciinema.org. Commit it alongside the log files.

Alternative: Use `script` for zero-install recording:

```bash
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  script -q .reviews/logs/PR-{NUM}-test.script -c 'pnpm test --continue'
"
```

#### Step 6.4: Parse results from logs

```bash
# Extract pass/fail counts from log files on codespace
gh codespace ssh -c $CS -- "
  echo '=== CHECK-TYPES ===' &&
  tail -5 /workspaces/{REPO}/.reviews/logs/PR-{NUM}-check-types.log &&
  echo '=== LINT ===' &&
  tail -5 /workspaces/{REPO}/.reviews/logs/PR-{NUM}-lint.log &&
  echo '=== TEST ===' &&
  tail -10 /workspaces/{REPO}/.reviews/logs/PR-{NUM}-test.log
"
```

#### Step 6.5: Additional verification scaled by tier

| Tier | Extra Verification                                                 |
| ---- | ------------------------------------------------------------------ |
| 1-2  | check-types + lint + test (baseline)                               |
| 3-4  | + targeted tests for affected packages + Sourcegraph blast radius  |
| 5-6  | + full build (`pnpm build`) + security review + pattern compliance |

```bash
# Tier 3+: Targeted tests
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  pnpm test --filter {AFFECTED_PACKAGE} 2>&1
"

# Tier 3+: Sourcegraph blast radius
# Search: repo:{UPSTREAM} {MODIFIED_FUNCTION}

# Tier 5+: Full build
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  pnpm install &&
  pnpm run build 2>&1
"
```

#### Step 6.6: Write targeted behavioral tests

**CRITICAL**: Existing tests prove "nothing broke." Targeted tests prove "the fix works."

For every code PR (tier 2+), write tests that exercise the SPECIFIC behavior the PR changes:

```bash
# Write test to the fork branch
gh codespace ssh -c $CS -- "cat > /workspaces/{REPO}/path/to/__tests__/pr-{NUM}-test.spec.ts << 'EOF'
// Test: PR #{NUM} - {TITLE}
// Proves: the specific behavior change works as intended
...
EOF"

# Run it
gh codespace ssh -c $CS -- "cd /workspaces/{REPO} && npx vitest run path/to/__tests__/pr-{NUM}-test.spec.ts"

# Push as evidence
gh codespace ssh -c $CS -- "cd /workspaces/{REPO} && git add -A && git commit -m 'test: behavioral tests for PR #{NUM}' && git push"
```

#### Step 6.7: Document results in review

**MANDATORY**: Every review MUST include BOTH tables:

```markdown
## Local Verification

### Regression (existing tests)

| Test       | Command                | Result | Details                 |
| ---------- | ---------------------- | ------ | ----------------------- |
| TypeScript | `pnpm check-types`     | PASS   | 22/22 packages          |
| Lint       | `pnpm lint`            | PASS   | 18/18 packages          |
| Unit Tests | `pnpm test --continue` | PASS   | 7,831 tests, 0 failures |

### Behavioral (targeted tests)

| Test Case             | Expected            | Result |
| --------------------- | ------------------- | ------ |
| {specific scenario A} | {expected behavior} | PASS   |
| {specific scenario B} | {expected behavior} | PASS   |

Test file: [link to test on fork branch]

Raw logs: [`check-types`](https://github.com/{FORK}/blob/review/PR-{NUM}/.reviews/logs/PR-{NUM}-check-types.log) | [`lint`](https://github.com/{FORK}/blob/review/PR-{NUM}/.reviews/logs/PR-{NUM}-lint.log) | [`test`](https://github.com/{FORK}/blob/review/PR-{NUM}/.reviews/logs/PR-{NUM}-test.log)

> Tested on fork branch `review/PR-{NUM}` — [view branch](https://github.com/{FORK}/tree/review/PR-{NUM})
```

If any test FAILS:

1. Document the failure
2. Determine if failure is pre-existing or caused by the PR
3. If caused by PR → REQUEST_CHANGES with evidence
4. If pre-existing → note in review, don't block the PR for it

Record all verification results in the review's Verification table.

---

### PHASE 6B: COMBINED INTEGRATION TEST (After Batch Reviews)

**When multiple PRs are reviewed in the same batch, merge them all together
and run the full test suite to prove they don't conflict.**

This is what separates a thorough review from drive-by individual checks.

#### Step 6B.1: Create combined branch

```bash
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  export HUSKY=0 &&
  git checkout -B review/combined-batch-{N} upstream/main
"
```

#### Step 6B.2: Merge PRs (easiest first)

```bash
# Merge in order of least likely to conflict
for PR in {LIST_OF_PRS_SORTED_BY_RISK}; do
  gh codespace ssh -c $CS -- "
    cd /workspaces/{REPO} &&
    export HUSKY=0 &&
    git merge review/PR-$PR --no-edit 2>&1 || echo 'CONFLICT on PR-$PR'
  "
done
```

**Conflict resolution**: When merges conflict, resolve manually:

1. Check which side is correct (usually both — merge both changes)
2. Verify no conflict markers remain: `grep -c '<<<<' {FILE}`
3. Commit with descriptive message explaining what was kept from each side

#### Step 6B.3: Run full test suite on combined branch

```bash
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  export HUSKY=0 &&
  pnpm run check-types 2>&1 &&
  pnpm run lint 2>&1 &&
  pnpm test --continue 2>&1
"
```

#### Step 6B.4: Fix pre-existing test failures

If pre-existing test failures are found (not from any reviewed PR):

1. Create a separate `fix/test-maintenance` branch from upstream main
2. Fix the issue with minimal changes
3. Verify the fix passes on clean main
4. Create a PR on the fork (and optionally submit upstream)
5. Cherry-pick the fix into the combined branch

#### Step 6B.5: Push combined branch and create evidence PR

```bash
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  export HUSKY=0 &&
  git push origin review/combined-batch-{N}
"

gh pr create --repo {FORK} \
  --head review/combined-batch-{N} \
  --base main \
  --title "Integration test: PRs #{A} + #{B} + #{C} merged together" \
  --body "Combined test results..."
```

#### Step 6B.6: Document in reviews

Add to each PR's review:

```markdown
## Combined Integration Test

Merged with {N} other PRs on branch `review/combined-batch-{N}`:
| PR | Result |
|----|--------|
| #{A} | Clean merge |
| #{B} | Conflict resolved (file.ts — kept both changes) |

Combined test results: {X} passed, {Y} failed
[Evidence: fork PR #{COMBINED_PR}]({URL})
```

---

### PHASE 7: VALIDATE FIXES (Post-Review)

When a review requests changes and the author pushes fixes:

#### Step 7.1: Detect new commits

```bash
# Check for new commits since review
gh pr view {NUM} --repo {UPSTREAM} --json commits -q '.commits | length'
gh pr view {NUM} --repo {UPSTREAM} --json commits -q '.commits[-1] | "\(.oid) \(.messageHeadline) \(.committedDate)"'
```

#### Step 7.2: Update fork mirror

```bash
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  git checkout review/PR-{NUM} &&
  git fetch upstream pull/{NUM}/head &&
  git reset --hard FETCH_HEAD &&
  git push --force origin review/PR-{NUM}
"
```

#### Step 7.3: Re-run bot analysis

Bots auto-review on new push. Wait for fresh reviews (Phase 3 again).

#### Step 7.4: Targeted re-verification

```bash
# Only re-test what changed since our review
gh pr diff {NUM} --repo {UPSTREAM}  # Check new commits

# Re-run affected tests in codespace
gh codespace ssh -c $CS -- "
  cd /workspaces/{REPO} &&
  git checkout review/PR-{NUM} &&
  pnpm test --filter {AFFECTED_PACKAGE}
"
```

#### Step 7.5: Update review artifacts

- Update `status.json` with new bot findings
- Append to journal: "## Fix Validation" section
- Update verdict if fix resolves findings
- Track rounds: `"review_rounds": 2`

#### Step 7.6: Regression checklist

| Check                  | Command                             | Pass? |
| ---------------------- | ----------------------------------- | ----- |
| Original issue fixed   | Verify against linked issue         |       |
| No new type errors     | `pnpm check-types`                  |       |
| Tests pass             | `pnpm test --filter {pkg}`          |       |
| Bot consensus improved | Compare fork PR before/after        |       |
| No scope creep         | Diff only addresses review comments |       |

---

### PHASE 8: QUALITY GATE

Before submitting, verify:

1. **Test results included**: Local Verification table present with pass/fail for check-types, lint, test
2. **Log files committed**: Raw log files pushed to fork branch at `.reviews/logs/PR-{NUM}-*.log`
3. **Fork branch linked**: URL to `review/PR-{NUM}` branch on fork resolves
4. **Metadata complete**: All fields in PR-REVIEW-META and PR-JOURNAL-META populated
5. **Fork PR linked**: URL valid, bot comments present
6. **Verdict justified**: Rationale matches findings
7. **No AI slop**: No filler phrases ("I'd be happy to", "Great question", etc.)
8. **Tone professional**: Constructive, specific, evidence-based
9. **Links valid**: All URLs resolve (no 404s)

```bash
# Quick metadata check
grep -c "TODO\|{.*}" {reviewsDir}/PR-{NUM}/{REPO_SHORT}-{NUM}-review.md
# Should be 0 - no unfilled placeholders

# Check fork PR exists and has reviews
gh pr view {FORK_PR_NUM} --repo {FORK} --json state,comments -q '"\(.state) - \(.comments | length) comments"'
```

Present artifacts to human for final approval.

---

### PHASE 9: SUBMIT TO UPSTREAM

**CRITICAL: NEVER post to upstream without explicit human approval.**

Reviews are written locally with phase set to "ready". The human (Jeremy) must
review the review.md and journal.md files and explicitly say to submit before
ANY comments are posted to the upstream PR. This is a hard gate — no exceptions.

When presenting for approval, show:

- The review verdict and key findings
- The journal summary
- Ask: "Ready to post these to upstream PR #{NUM}?"

After human approval:

```bash
# Comment 1: Review (for agents/maintainers)
gh pr comment {NUM} --repo {UPSTREAM} \
  --body-file {reviewsDir}/PR-{NUM}/{REPO_SHORT}-{NUM}-review.md

# Comment 2: Journal (for humans/learning)
gh pr comment {NUM} --repo {UPSTREAM} \
  --body-file {reviewsDir}/PR-{NUM}/{REPO_SHORT}-{NUM}-journal.md
```

Update `status.json`:

```json
{
  "phase": "submitted",
  "submitted_at": "{ISO_TIMESTAMP}"
}
```

Update `PROGRESS.md` with the completed review.

---

### PHASE 10: POST-SUBMIT

After submission:

1. Promote patterns to `METHODOLOGY.md` if new pattern discovered
2. Track bot accuracy: did bots catch real issues? false positives?
3. Monitor upstream response: did maintainer merge? request more changes?
4. Update `priority-queue.json`: mark PR as reviewed
5. Stop codespace if no more PRs queued

---

## Codespace Management

### Cost Optimization

```bash
# Always stop after use
gh codespace stop -c $CS

# Delete when done with a batch of reviews
gh codespace delete -c $CS --force

# Free tier: 60 core-hours/month
# premiumLinux (8-core): 60/8 = 7.5 hours = ~30 PRs at 15 min each
```

### Machine Selection

| Machine           | RAM  | Use Case                                     |
| ----------------- | ---- | -------------------------------------------- |
| basicLinux32gb    | 8GB  | Docs-only PRs (no type checking)             |
| standardLinux32gb | 16GB | Small PRs                                    |
| premiumLinux      | 32GB | Most PRs (handles full monorepo check-types) |
| largePremiumLinux | 64GB | Massive PRs with full build                  |

---

## Setting Up a New Repo

To deploy this pipeline on a new repository:

### Step 1: Fork and clone the target repo

```bash
gh repo fork {UPSTREAM} --clone=false
mkdir -p ~/000-projects/99-forked/{OWNER}
gh repo clone {YOUR_USER}/{REPO} ~/000-projects/99-forked/{OWNER}/{REPO}
cd ~/000-projects/99-forked/{OWNER}/{REPO}
git remote add upstream https://github.com/{UPSTREAM}.git
```

### Step 2: Install bots on fork

- CodeRabbit: https://github.com/apps/coderabbitai (install on fork)
- Gemini Code Assist: https://github.com/apps/gemini-code-assist (install on fork)
- Greptile: https://app.greptile.com (connect fork repo)

### Step 3: Add GitHub Actions to fork

Add `.github/workflows/codeql.yml` and `.github/workflows/pr-agent.yml`

### Step 4: Create reviews directory

```bash
mkdir -p .reviews/{templates,PR-*}
```

### Step 5: Create config.json

```bash
cat > .reviews/config.json << EOF
{
  "upstream": "{ORG}/{REPO}",
  "fork": "{YOUR_USER}/{REPO}",
  "repo_short": "{REPO}",
  "codespace_machine": "premiumLinux",
  "codespace_name": "{repo}-review-pipeline",
  "reviews_dir": ".reviews",
  "bots": ["coderabbit", "gemini", "greptile", "codeql", "qodo"],
  "checklist": ["correctness", "conventions", "changeset", "tests", "i18n", "types", "security", "scope"],
  "methodology_url": "https://github.com/{YOUR_USER}/ai-pr-review-methodology"
}
EOF
```

### Step 6: Add devcontainer SSHD feature

If the repo has a devcontainer, add:

```json
"features": {
  "ghcr.io/devcontainers/features/sshd:1": { "version": "latest" }
}
```

### Step 7: Create Codespace

```bash
gh codespace create --repo {FORK} --branch main --machine premiumLinux --display-name "{repo}-review-pipeline"
```

### Step 8: Build priority queue

```bash
gh pr list --repo {UPSTREAM} --state open --limit 200 --json number,title,author,additions,deletions,changedFiles,labels,mergeable,reviewDecision > .reviews/all-prs.json
```

---

## Error Handling

| Error                            | Cause                                   | Solution                                        |
| -------------------------------- | --------------------------------------- | ----------------------------------------------- |
| Codespace SSH fails              | No SSHD feature                         | Add sshd:1 to devcontainer.json, rebuild        |
| check-types OOM                  | Machine too small                       | Use premiumLinux (32GB RAM)                     |
| Push rejected (non-fast-forward) | Branch exists from previous attempt     | `git push --force` on fork branch               |
| Push rejected (main)             | Husky checks current branch             | `git checkout review/PR-{NUM}` first            |
| Bot not reviewing                | Bot not installed on fork               | Check GitHub App installations                  |
| Wrong diff (full file replace)   | Used API commits instead of cherry-pick | Always use `git fetch upstream pull/{NUM}/head` |
| gh auth fails in codespace       | Token not set                           | `echo $TOKEN \| gh auth login --with-token`     |

## Examples

### Example 1: Review next docs PR

```
User: /pr-review
> Review next PR
[Picks tier 1 docs PR #5667, mirrors on fork, collects 3 bot reviews,
 composes review + journal, submits]
```

### Example 2: Review specific PR

```
User: /pr-review 5869
[Fetches PR #5869, classifies tier, mirrors, reviews, submits]
```

### Example 3: Validate a fix

```
User: /pr-review validate 5667
[Checks for new commits since review, updates fork mirror,
 re-runs bot analysis, targeted re-verification, updates artifacts]
```

### Example 4: Check pipeline status

```
User: /pr-review status
[Shows: 1 submitted, 0 in progress, 74 pending, bot accuracy stats]
```
