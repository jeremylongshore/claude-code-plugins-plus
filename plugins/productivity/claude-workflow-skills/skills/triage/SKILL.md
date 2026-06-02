---
name: triage
description: Validates all open GitHub issues, closes invalid ones with documentation, flags complex ones for planning discussion, then fixes and promotes remaining issues. Use when the user says triage issues, validate issues, fix issues, or work through the backlog.
allowed-tools: Read Glob Grep Bash Edit Write
disable-model-invocation: true
---

# Triage

Project: !`basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null || basename $PWD`
Branch: !`git branch --show-current 2>/dev/null || echo "unknown"`
Open issues: !`gh issue list --state open --json number,title --jq '.[] | "#\(.number) \(.title)"' 2>/dev/null || echo "none"`
Last tag: !`git describe --tags --abbrev=0 2>/dev/null || echo "none"`
Recent commits: !`git log --oneline -5 2>/dev/null || echo "none"`

Validates every open GitHub issue, closes those that are invalid, surfaces complex ones
for planning discussion, then fixes and promotes all remaining actionable issues.

## Step 0: Pre-flight check

```bash
gh auth status 2>&1 || { echo "ERROR: gh is not authenticated. Run: gh auth login"; exit 1; }
```

## Step 1: Fetch all open issues

```bash
gh issue list --state open --limit 100 --json number,title,body,labels,createdAt \
  --jq '.[] | {number, title, labels: [.labels[].name], createdAt, body}'
```

Read the full body of any issues where context is needed:

```bash
gh issue view <number> --json number,title,body,labels,comments
```

Also read the project files to understand current state before assessing anything:

- `README.md` — stated purpose and feature set
- `CLAUDE.md` — current status, known decisions, next steps

## Step 2: Classify each issue

For every open issue, classify it as one of:

- **Invalid** — already fixed, a duplicate, not reproducible, out of scope, or based on a
  misunderstanding. Evidence must be clear.
- **Complex** — valid but requires significant design decisions, breaking changes, or
  multi-step implementation that warrants planning discussion before proceeding.
- **Actionable** — valid, well-scoped, and fixable now without further input.

Build a classification table before taking any action:

| # | Title | Classification | Reason |
|---|-------|----------------|--------|
| N | ...   | Invalid/Complex/Actionable | ... |

## Step 3: Close invalid issues

For each invalid issue, post a closing comment that explains why it is being closed, then close it:

```bash
gh issue comment <number> --body "$(cat <<'EOF'
Closing as invalid: <specific reason — already fixed in <commit/PR>, duplicate of #N,
not reproducible because <evidence>, or out of scope because <reason>>.

<If already fixed: reference the commit or PR that resolved it.>
<If duplicate: reference the canonical issue.>
EOF
)"

gh issue close <number> --reason "not planned"
```

Use `--reason "completed"` if the issue was already resolved in code.

## Step 4: Surface complex issues for planning

Stop and present complex issues to the user before proceeding. Format clearly:

---

**Complex issues — planning needed before proceeding:**

For each complex issue:

- **#N: <title>**
  - Why it's complex: <design decision, breaking change, or scope concern>
  - Options to consider: <brief list of approaches>
  - Suggested next step: defer to backlog / spike / discuss now

---

Wait for the user's direction on each complex issue before moving to Step 5.
If running non-interactively (no terminal), stop here and output the complex issues report.

```bash
if [ ! -t 0 ]; then
  echo "Non-interactive mode: stopping after complex issue report. Review and re-run interactively."
  exit 0
fi
```

## Step 5: Fix actionable issues

Work through each actionable issue. For each one:

1. Read the relevant source files before making any changes.
2. Implement the fix — prefer the minimal correct change; don't refactor beyond the scope of
   the issue.
3. Verify the fix with any available linting or syntax checks:

   ```bash
   bash -n <script.sh>        # syntax check for shell scripts
   markdownlint '**/*.md'     # markdown linting
   ```

4. Stage the change:

   ```bash
   git add -u
   ```

Record each fix with its issue number so the commit and PR can reference them.

## Step 6: Promote

Once all actionable issues are fixed, run:

```text
/promote
```

The promote skill will commit, push, create and merge a PR (referencing fixed issue numbers
via `Closes #N` in the commit message), tag a release, and clean up.

When composing the commit message for the promote step, include `Closes #N` for every
issue fixed in Step 5.
