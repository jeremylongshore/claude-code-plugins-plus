# Safety Rules

Non-negotiable safety rules for all git and GitHub operations. These apply at every skill level.

## Branch Protection

### Rule: NEVER push directly to `main` or `master`

**Why:** The main branch is the source of truth. Direct pushes bypass code review, skip CI checks, and risk breaking the project for everyone.

**What to do instead:**

1. Create a feature branch: `git checkout -b feature/description`
2. Make changes and commit on the feature branch
3. Push the feature branch: `git push -u origin feature/description`
4. Create a pull request for review

**If the user says "just push to main":**

- Explain why branching is safer (calibrated to their level)
- Create a branch anyway
- Advanced users get the explanation once; beginners get it reinforced

**Exception:** Solo projects with no collaborators AND the user explicitly understands the risk. Even then, recommend branching as a good habit.

## Force Push Prevention

### Rule: NEVER use `--force` or `--force-with-lease` without explicit confirmation

**Why:** Force push overwrites remote history. If anyone else has pulled from the branch, their work becomes incompatible. Data can be permanently lost.

**What to do instead:**

- Pull and merge/rebase before pushing
- If push is rejected, resolve the divergence properly

**If force push is truly needed (rare):**

1. Explain exactly what will happen
2. Confirm the branch is not shared with others
3. Prefer `--force-with-lease` over `--force` (checks for upstream changes)
4. Get explicit user confirmation before executing

## Destructive Operation Guards

### Rule: ALWAYS run `git status` before any destructive operation

Destructive operations include:

- `git reset --hard`
- `git checkout -- <file>` (discards changes)
- `git clean -fd`
- `git stash drop`
- `git branch -D`

**Before any of these:**

1. Run `git status` to show the user what will be affected
2. Explain what will be lost (calibrated to level)
3. Ask for explicit confirmation
4. Suggest safer alternatives when possible

### Safer Alternatives

| Destructive | Safer Alternative |
|------------|------------------|
| `git reset --hard` | `git stash` (saves changes for later) |
| `git restore FILE` | `git diff FILE` first to review what will be lost |
| `git clean -fd` | `git clean -fdn` (dry run first) |
| `git branch -D` | `git branch -d` (fails if unmerged — that's the point) |
| `git push origin --delete BRANCH` | Verify branch is fully merged first with `git branch --merged` |

## Secret Protection

### Rule: NEVER commit files that contain secrets

**Check before staging:**

- `.env` and `.env.*` files
- Files named `credentials`, `secrets`, `tokens`, `keys`
- Files containing strings that look like API keys, passwords, or tokens
- `*.pem`, `*.key`, `*.p12`, `*.pfx` files
- `config.local.*` files
- Service account JSON files

**What to do:**

1. Add these patterns to `.gitignore` BEFORE committing
2. If accidentally committed, help the user remove from history and rotate the secret
3. Warn the user that once pushed, a secret should be considered compromised

**Important:** Adding a file to `.gitignore` does NOT untrack already-tracked files. To stop tracking a file already committed, run `git rm --cached FILE` first.

**Auto-generate `.gitignore` patterns:**

```
# Secrets and credentials
.env
.env.*
*.pem
*.key
*.p12
*.pfx
credentials.*
secrets.*
tokens.*
*-service-account.json
```

## Commit Hygiene

### Rule: Never blindly `git add .` or `git add -A`

**Why:** These commands stage EVERYTHING, including:

- Files the user doesn't realize exist
- Temporary files, build artifacts
- Secrets and credentials
- IDE configuration files
- OS-specific files (`.DS_Store`, `Thumbs.db`)

**What to do instead:**

1. Run `git status` to review changes
2. Stage specific files: `git add <file1> <file2>`
3. Or use `git add -p` for partial staging (intermediate+)
4. Check for suspicious files before committing

## History Rewriting

### Rule: NEVER rewrite history that has been pushed

**Operations that rewrite history:**

- `git rebase` (on pushed branches)
- `git commit --amend` (on pushed commits)
- `git reset` (past pushed commits)
- `git filter-branch` / BFG Repo Cleaner

**Why:** Others may have based work on the existing history. Rewriting it creates divergence that's hard to resolve.

**Exception:** Personal feature branches that only you work on. Even then, confirm before rewriting.

## Communication During Risky Operations

For any operation that could cause data loss:

1. **Explain what's about to happen** in the user's language
2. **Show what will be affected** (files, commits, branches)
3. **State what can't be undone** if applicable
4. **Ask for confirmation** before proceeding
5. **Verify success** after completing

This applies at all skill levels, but the depth of explanation adapts:

- Beginner: Full explanation with analogies
- Intermediate: Clear statement of impact
- Advanced: Brief heads-up
- Expert: Quick confirmation prompt
