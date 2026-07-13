# Error Recovery Playbook

Step-by-step recovery procedures for common git and GitHub problems. Each section includes procedures adapted by skill level.

## Merge Conflicts

### Detection

```bash
# Check for conflicted files via git
git diff --name-only --diff-filter=U 2>/dev/null
```

### Recovery

**Step 1: Identify conflicted files**

```bash
git status  # Shows "both modified" files
```

**Step 2: Open each conflicted file and resolve**

The conflict markers look like this:

```
<<<<<<< HEAD
Your changes (current branch)
=======
Their changes (incoming branch)
>>>>>>> feature-branch
```

**Beginner guidance:** "Two versions of the same code exist. Everything between `<<<<<<<` and `=======` is YOUR version. Everything between `=======` and `>>>>>>>` is the OTHER version. You need to pick one, combine them, or write something new — then delete the marker lines."

**Advanced guidance:** Show `git diff` for each conflicted file. Let them resolve in their editor. Offer to handle specific files if asked.

**Step 3: After resolving all conflicts**

```bash
git add <resolved-files>
git commit  # Completes the merge
```

### Prevention Tips

- Pull/rebase frequently to reduce divergence
- Communicate with teammates about who's editing what
- Keep commits small and focused

## Authentication Errors

### Symptoms

- `fatal: Authentication failed`
- `Permission denied (publickey)`
- `gh: error: HTTP 401`
- `remote: Repository not found` (can be auth-related)

### Recovery

**Step 1: Check current auth status**

```bash
gh auth status
git remote -v  # Check if using HTTPS or SSH
```

**Step 2: Re-authenticate**

```bash
# For gh CLI (recommended)
gh auth login

# For git over HTTPS
gh auth setup-git  # Configures git to use gh as credential helper

# For SSH issues
ssh -T git@github.com  # Test SSH connection
```

**Step 3: Fix remote URL if needed**

```bash
# Switch from SSH to HTTPS (or vice versa)
git remote set-url origin https://github.com/USER/REPO.git
# or
git remote set-url origin git@github.com:USER/REPO.git
```

**Beginner guidance:** "Your terminal lost its connection to GitHub. We need to log in again. This is like re-entering your password when a website logs you out."

## Detached HEAD

### Symptoms

- `git status` shows "HEAD detached at <hash>"
- User checked out a specific commit, tag, or remote branch directly

### Recovery

**Step 1: Check if there are unsaved changes**

```bash
git status
git log --oneline -5  # See where HEAD is
```

**Step 2: Save work if needed**

```bash
# If there are commits you want to keep:
git branch recovery-branch  # Creates a branch at current position

# Then go back to a known branch:
git checkout main
```

**Step 3: If no work to save**

```bash
git checkout main  # Just go back
```

**Beginner guidance:** "You've accidentally wandered off the path into the project's history. Don't worry — your changes are still here. I'm going to create a safe branch to hold your work, then we'll get back on track."

## Rebase Gone Wrong

### Symptoms

- Conflicts during rebase
- History looks wrong
- User is confused about current state

### Recovery

**Step 1: Check current state first**

```bash
git status  # Always check before any recovery action
```

**Step 2: If rebase is still in progress**

```bash
# Abort and go back to pre-rebase state
git rebase --abort
```

**Step 3: If rebase completed but history is wrong**

```bash
# Find the pre-rebase state in reflog
git reflog
# Reset to the commit before rebase started — REQUIRES USER CONFIRMATION
git reset --hard REFLOG_HASH
```

**Step 3: Offer merge as alternative**

```bash
# If rebase is too complex, merge is safer
git merge main  # Instead of rebase
```

**Beginner guidance:** "The operation we tried got complicated. I'm going to undo it completely — no harm done. We'll use a simpler approach instead."

## Accidental Commit to Main

### Recovery

**Step 1: Check state and move the commit to a new branch**

```bash
git status  # Verify clean working tree before destructive operation
git branch feature-branch  # Creates branch at current position (with the commit)
git reset --hard HEAD~1     # REQUIRES USER CONFIRMATION - moves main back one commit
git switch feature-branch
```

**Step 2: Push the feature branch**

```bash
git push -u origin feature-branch
```

**Beginner guidance:** "You saved your changes directly to the main version instead of a separate branch. I'm going to move those changes to their own branch so we can review them properly."

## Accidental File Deletion

### Recovery

**If the file was committed:**

```bash
git restore path/to/file  # Restore from last commit (Git 2.23+)
# Legacy: git checkout HEAD -- path/to/file
```

**If the file was staged but not committed:**

```bash
git restore --staged path/to/file  # Unstage, then restore
# Legacy: git checkout -- path/to/file
```

**If the file was never tracked:**

- Check trash/recycle bin
- Cannot be recovered via git

## Large File Accidentally Committed

### Symptoms

- `git push` fails with size limit error
- Repository grew unexpectedly large

### Recovery

**Step 1: Remove from current commit (if last commit)**

```bash
git reset HEAD~1           # Undo last commit, keep changes — do NOT re-add the large file
# Add file to .gitignore (check for duplicates first)
grep -qF "large-file.zip" .gitignore 2>/dev/null || echo "large-file.zip" >> .gitignore
git add .gitignore
git add <other-files>      # Re-add everything except the large file
git commit -m "Add changes without large file"
```

**Step 2: If pushed or multiple commits deep**

- Consider `git filter-branch` or BFG Repo Cleaner (advanced — explain risks)
- For beginners: walk through the simpler reset approach, or start fresh if the repo is small

## Push Rejected (Non-Fast-Forward)

### Symptoms

- `! [rejected] main -> main (non-fast-forward)`
- `Updates were rejected because the tip of your current branch is behind`

### Recovery

**For intermediate+ users:**

```bash
git pull --rebase origin BRANCH  # Rebase local changes on top of remote
git push
```

**For beginners (simpler merge-based approach):**

```bash
git pull origin BRANCH  # Merge remote changes in
git push
```

**If conflicts arise during pull:**

- Resolve conflicts (see Merge Conflicts section above)
- If rebasing: `git rebase --continue` then `git push`
- If merging: `git commit` then `git push`

**NEVER suggest `git push --force`** unless the user is an expert AND explicitly asks for it AND understands the consequences.

## Stash Recovery

### Symptoms

- `git stash pop` caused conflicts
- Lost track of stashed changes
- Stash accidentally dropped

### Recovery

**Step 1: List all stashes**

```bash
git stash list  # Shows all saved stashes
```

**Step 2: View stash contents without applying**

```bash
git stash show -p stash@{0}  # Show diff of most recent stash
```

**Step 3: If `git stash pop` caused conflicts**
The stash is NOT dropped when pop causes conflicts. Resolve the conflicts normally (see Merge Conflicts section), then drop the stash manually:

```bash
git stash drop stash@{0}
```

**Step 4: If stash was dropped accidentally**
Stashes can sometimes be recovered from the reflog within a few weeks:

```bash
git fsck --unreachable | grep commit  # Find orphaned commits
```

**Beginner guidance:** "Think of stash as a drawer where git temporarily stores changes. Sometimes when pulling those changes back out, they conflict with new work. The changes are still in the drawer until the conflict is resolved."

## Common Error Messages Translated

| Error | Plain English | What to Do |
|-------|-------------|------------|
| `fatal: not a git repository` | This folder isn't tracked by git yet | Run `git init` or navigate to the right folder |
| `error: failed to push some refs` | Someone else pushed changes before you | Pull first, then push |
| `fatal: refusing to merge unrelated histories` | Two repos with no common ancestor | Check `git remote -v` for wrong remote; if intentional, use `--allow-unrelated-histories` |
| `error: Your local changes would be overwritten` | You have unsaved changes that conflict | Commit or stash your changes first |
| `warning: LF will be replaced by CRLF` | Line ending difference (Windows vs Mac/Linux) | Usually safe to ignore; set `git config --global core.autocrlf input` on Mac/Linux or `true` on Windows |
| `Permission denied (publickey)` | SSH key not set up or not recognized | Re-authenticate with `gh auth login` |
