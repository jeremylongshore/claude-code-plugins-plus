---
name: promote
description: Runs the full release workflow for the current project. Commits any uncommitted changes, pushes to remote, creates and merges a PR if on a feature branch, determines the next semver version from conventional commits, creates an annotated git tag and GitHub release with generated notes, cleans up merged branches, and returns to a clean main. Use when the user says promote, ship, release, commit and push, tag and release, or get back to main.
allowed-tools: Bash
disable-model-invocation: true
---

# Promote Changes

Runs the full release workflow from current working state to a tagged GitHub release on main.

Current branch: !`git branch --show-current 2>/dev/null || echo "unknown"`

Git status: !`git status --short 2>/dev/null || echo "not a git repo"`

Last tag: !`git describe --tags --abbrev=0 2>/dev/null || echo "none"`

Recent commits since last tag:

```text
!`git log $(git describe --tags --abbrev=0 2>/dev/null || echo "")..HEAD --oneline -10 2>/dev/null || git log --oneline -10`
```

Next version (calculated from commits above):

```text
!`(last=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0"); IFS='.' read -r ma mi pa <<< "${last#v}"; log=$(git log "${last}..HEAD" --format="%s" 2>/dev/null); if echo "$log" | grep -qE "^[a-z]+(\([^)]+\))?!:"; then echo "v$((ma+1)).0.0"; elif echo "$log" | grep -qE "^feat"; then echo "v${ma}.$((mi+1)).0"; else echo "v${ma}.${mi}.$((pa+1))"; fi)`
```

## Step 0: Pre-flight checks

```bash
gh auth status 2>&1 || { echo "ERROR: gh is not authenticated. Run: gh auth login"; exit 1; }
```

Check for untracked `.env` files that could be accidentally staged:

```bash
git status --short | grep -E '^\?\? .*\.env' && echo "WARNING: untracked .env files detected — review before staging"
cat .gitignore 2>/dev/null | grep -q '\.env' || echo "WARNING: .gitignore does not exclude .env files"
```

If any `.env` files would be staged:

```bash
if [ -t 0 ]; then
  # Interactive — ask for confirmation before continuing
  read -p "WARNING: .env files detected. Continue? (y/N) " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
else
  # Non-interactive — hard stop; too risky to proceed without human review
  echo "ERROR: untracked .env files detected in non-interactive mode. Aborting."
  exit 1
fi
```

## Step 1: Commit any uncommitted changes

If the git status above shows uncommitted or untracked changes:

1. Review the diff: `git diff` and `git diff --cached`
2. Stage changes selectively — prefer tracked files: `git add -u`, then review and add any
   intentional new files individually. Avoid `git add -A` unless the user explicitly confirms.
3. Draft a conventional commit message from the changes — lead with a type prefix
   (`feat:`, `fix:`, `docs:`, `chore:`, etc.) and a concise summary
4. Commit using a heredoc so multi-line messages format correctly

If there is nothing uncommitted, skip to Step 2.

## Step 2: Push

Push the current branch to remote:

```bash
git push -u origin HEAD
```

## Step 3: Merge to main (feature branch only)

Skip this step if already on `main` (or the repo's default branch).

If on a feature branch:

1. Scan commits since the last tag for issue references:

   ```bash
   git log $(git describe --tags --abbrev=0 2>/dev/null || echo "")..HEAD --format="%B"
   ```

   Look for `Closes #N`, `Fixes #N`, `Resolves #N` (case-insensitive). Collect all issue numbers
   found. If none are found:

   ```bash
   if [ -t 0 ]; then
     # Interactive — ask the user
     read -p "Any GitHub issues this resolves? (e.g. 12 15 — or enter to skip) " issues
   else
     # Non-interactive — skip silently
     issues=""
   fi
   ```

2. Create a PR targeting main, including closing keywords in the body so GitHub closes the issues
   automatically on merge:

   ```bash
   gh pr create --title "<type>: <summary>" --body "$(cat <<'EOF'
   ## Summary
   <bullet points from commits>

   Closes #N, Closes #N

   🤖 Generated with [claude-workflow-skills:promote](https://github.com/ali5ter/claude-workflow-skills) on behalf of [Alister](https://github.com/ali5ter)
   EOF
   )"
   ```

   Omit the `Closes` lines if no issues were identified.

3. Enable auto-merge (squash preferred):

   ```bash
   gh pr merge --auto --squash
   ```

4. Poll until merged:

   ```bash
   gh pr view --json state --jq '.state'
   ```

5. Switch to main and pull:

   ```bash
   git checkout main && git pull
   ```

## Step 4: Confirm next version

The next version is pre-calculated in the context block above using these semver rules:

- Commit subject with `!:` (e.g. `feat!:`, `fix!:`) → **major** bump
- Commit subject beginning with `feat` → **minor** bump
- All other commits → **patch** bump

Confirm the calculated version is correct given the commit list. If no previous tag exists, use
`v1.0.0`. Override only if the calculated version is clearly wrong (e.g. the injection returned
an error or empty output).

## Step 5: Sync plugin manifest (if present)

If `.claude-plugin/plugin.json` exists, update its `version` field to `<next-version>` (no `v`
prefix — plugin manifests use bare semver like `1.2.3`):

```bash
node -e "
const fs = require('fs');
const f = '.claude-plugin/plugin.json';
const d = JSON.parse(fs.readFileSync(f, 'utf8'));
d.version = '<next-version>';
fs.writeFileSync(f, JSON.stringify(d, null, 2) + '\n');
"
```

Then commit and push:

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: sync plugin.json version to v<next-version>"
git push
```

Skip this step entirely if `.claude-plugin/plugin.json` does not exist.

## Step 6: Tag and release

```bash
git tag -a v<next-version> -m "Release v<next-version>"
git push origin v<next-version>
gh release create v<next-version> \
  --generate-notes \
  --title "v<next-version>"
```

## Step 7: Close resolved issues (main branch only)

Skip this step if a PR was created in Step 3 — GitHub will close the issues automatically when
the PR merges via the `Closes #N` keywords in the PR body.

If the promotion was directly on `main` (no PR), close any identified issues now:

```bash
gh issue close <N> --comment "Resolved in $(gh release view v<next-version> --json url --jq '.url')"
```

## Step 8: Clean up merged feature branch

If a feature branch was merged in Step 3, delete it locally and remotely:

```bash
git branch -d <feature-branch>
git push origin --delete <feature-branch>
```

## Step 9: Confirm clean state

```bash
git status
git log --oneline -5
```

Report the GitHub release URL from `gh release view v<next-version> --json url --jq '.url'`.
