---
name: git-workflow
description: |
  When the user asks you to squash commits, rebase a branch, resolve
  merge conflicts, create conventional commits, or manage a PR workflow.

  Trigger phrases:
  - "squash these commits"
  - "rebase my branch"
  - "resolve conflicts"
  - "create a PR"
  - "clean up my git history"
  - "interactive rebase"
  - "amend last commit"
  - "cherry-pick"
  - "undo this commit"
allowed-tools: Bash, Read, Write, Edit, Glob
version: 1.0.0
author: Carl Johnson <gupsspam@users.noreply.github.com>
license: MIT
compatibility: agentskills.io/specification
tags: [git, workflow, version-control, productivity, developer-tools]
---

# Git Workflow

## Overview

This skill teaches Claude Code how to execute common multi-step Git workflows safely
and correctly: feature branch creation with conventional commits, interactive rebase
(squash, reword, reorder, fixup), commit management (amend, unstage, undo, stash),
merge conflict resolution, pull request management with safe force-push, and
cherry-picking commits between branches.

The core value is that developers no longer need to remember exact flags and command
sequences for multi-step Git operations. The skill bakes in safety rules: every
destructive operation is preceded by a state inspection (`git status` + `git log`),
public history is corrected with `git revert` rather than `git reset`, and
force-pushes always use `--force-with-lease` and are always preceded by showing the
user which commits will be rewritten. Every operation favors the reversible path,
and recovery routes (reflog, `--abort`) are treated as first-class steps rather than
afterthoughts.

## Prerequisites

- **Git 2.30+** installed and on `PATH` (`git --version` to verify). `--force-with-lease`
  and `git switch` require a modern Git.
- **A Git repository**: the working directory must be inside a repo
  (`git rev-parse --is-inside-work-tree` returns `true`). If not, ask the user
  whether to `git init` — do not initialize without confirmation.
- **Identity configured**: `git config user.name` and `git config user.email` must
  return values; if not, prompt the user for them before committing.
- **For PR workflows**: a configured remote (`git remote -v`) and the GitHub CLI (`gh`)
  authenticated (`gh auth status`), or the user's stated preference for opening PRs
  via the web UI.
- **A clean starting point for history rewrites**: rebase and cherry-pick steps
  require a clean working tree; the instructions below stash uncommitted work first
  when needed.

## Instructions

1. **Establish state before anything else.** Run `git status` and `git log --oneline -5`.
   For any operation that rewrites history or discards work (rebase, reset, force-push,
   checkout over changes), this step is mandatory, not optional — report the current
   branch, upstream, and any uncommitted changes to the user before proceeding.

2. **Protect uncommitted work.** If `git status` shows modified or untracked files and
   the requested operation needs a clean tree, run `git stash push -u -m "wip before
   <operation>"`. Tell the user the stash exists and restore it with `git stash pop`
   when the operation completes.

3. **Feature branch — create.** Branch from an up-to-date default branch: `git fetch
   origin`, then `git switch -c feature/<short-kebab-description> origin/main`
   (substitute the repo's actual default branch, detected via `git remote show origin
   | grep 'HEAD branch'`).

4. **Feature branch — commit conventionally.** Stage deliberately (`git add <paths>`,
   never a reflexive `git add -A`), review with `git diff --staged`, then commit using
   Conventional Commits format: `<type>(<optional-scope>): <imperative summary ≤72
   chars>` where type is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`,
   `perf`, `ci`. Add a body explaining *why* when the change isn't self-evident.

5. **Feature branch — push and open PR.** First push: `git push -u origin HEAD`. Then
   open the PR with `gh pr create --title "<conventional title>" --body "<summary>"`,
   or print the compare URL for the user to open in the browser if `gh` is unavailable.

6. **Interactive rebase — squash the last N commits.** Confirm N against `git log
   --oneline -<N+2>` so the user sees exactly which commits are included. Note the
   current HEAD SHA as a recovery point. Then run `GIT_SEQUENCE_EDITOR="sed -i
   '2,\\$s/^pick/squash/'" git rebase -i HEAD~<N>`. Since interactive editors aren't
   available in this environment, always drive the todo list via
   `GIT_SEQUENCE_EDITOR` and the commit message via `GIT_EDITOR` or
   `git commit --amend -m`.

7. **Interactive rebase — reword or reorder.** For rewording only the last commit,
   prefer `git commit --amend -m "<new message>"`. For older commits, use
   `git rebase -i HEAD~<N>` with a `GIT_SEQUENCE_EDITOR` script that changes
   `pick` to `reword`.

8. **Interactive rebase — autosquash flow.** When fixing an earlier commit, prefer
   `git commit --fixup=<sha>` followed by `git rebase -i --autosquash <sha>~1` — it
   keeps intent explicit and the todo list correct automatically.

9. **Amend the last commit.** To add forgotten changes: `git add <paths>
   && git commit --amend --no-edit`. Warn the user first if the commit is already
   pushed — amending pushed commits requires a force-push (step 15) and affects
   anyone who pulled it.

10. **Unstage and discard.** Unstage without losing changes: `git restore --staged
    <path>`. Discard working-tree changes (destructive — confirm with the user and
    show `git diff <path>` first): `git restore <path>`.

11. **Undo a commit — choose reset vs revert.** If the commit is **unpushed**:
    `git reset --soft HEAD~1` keeps the changes staged, `git reset --mixed HEAD~1`
    keeps them unstaged. If the commit is **pushed/public**: use `git revert <sha>`
    to create an inverse commit — never rewrite public history with reset.

12. **Update a branch onto latest main.** `git fetch origin`, then `git rebase
    origin/main` for an unshared feature branch, or `git merge origin/main` if the
    branch is shared. Ask which convention the repo uses if unclear.

13. **Resolve merge conflicts — inventory first.** When a merge/rebase stops, list
    conflicted files with `git diff --name-only --diff-filter=U` and report them
    to the user. Conflicts are marked by `<<<<<<<` / `=======` / `>>>>>>>` markers.

14. **Resolve merge conflicts — resolve and continue.** For each file choose: keep
    our side (`git checkout --ours <path>`), keep theirs (`git checkout --theirs
    <path>`), or edit manually. Note ours/theirs **inverts during rebase** — state
    which is which before applying. Then `git add <path>` for each resolved file
    and `git rebase --continue` (or `git merge --continue`). To back out: `git rebase
    --abort` / `git merge --abort`.

15. **Force-push safely.** After any history rewrite on a pushed branch: first show
    the user what will be replaced with `git log --oneline origin/<branch>..HEAD`
    and `git log --oneline HEAD..origin/<branch>`. Only after they've seen the
    divergence, run `git push --force-with-lease`. **Never use bare `--force`** —
    `--force-with-lease` aborts if someone else pushed in the meantime instead of
    silently destroying their work.

16. **PR management — keep it green.** After pushing, check CI with `gh pr checks`
    and view review state with `gh pr view --web` (or print the URL). To update a
    PR branch with main, use step 12 followed by step 15.

17. **Merge the PR.** Prefer merging via the web UI or `gh pr merge --squash` (or
    `--merge`/`--rebase` per repo convention) once checks pass and reviews are
    approved.

18. **Cherry-pick between branches.** Identify the commit(s) on the source branch
    with `git log --oneline <source-branch>`, switch to the target branch, verify
    clean state, then `git cherry-pick <sha>`. On conflict, follow steps 13–14.

19. **Stash management.** List with `git stash list`, inspect with `git stash show
    -p stash@{n}`, restore with `git stash pop` (removes from stash) or
    `git stash apply` (keeps a copy).

20. **Recovery safety net.** If anything goes wrong after a rewrite, `git reflog`
    shows every prior HEAD position; recover with `git reset --hard <reflog-sha>`
    or `git branch rescue/<name> <reflog-sha>` to preserve the old state without
    moving anything.

21. **Verify and report.** After every workflow, run `git status` and `git log
    --oneline -5` again and summarize for the user: branch name, resulting commits,
    what was pushed, and any stash still holding their work.

## Output

On completion of any workflow, the user receives:

- **A clean, verified repository state** — `git status` reporting a clean tree on
  the expected branch.
- **A summary of what changed**: the resulting commit history, which commits were
  created/squashed/reworded/reverted/cherry-picked, and their SHAs.
- **Remote state**: whether the branch was pushed, whether a force-push occurred,
  and the PR URL if one was created or updated.
- **Recovery pointers**: the pre-operation HEAD SHA (reachable via `git reflog`)
  after any history rewrite, and the name of any stash created.

## Error Handling

- **`fatal: not a git repository`** — The directory isn't a repo. Confirm with
  `pwd`, look for the repo root upward, or offer `git init` — never initialize
  without asking.
- **`! [rejected] ... (non-fast-forward)`** on push — The remote has commits you
  don't. Run `git fetch origin` and inspect `git log HEAD..origin/<branch>`. If
  the divergence is expected (you rewrote history), follow safe force-push
  (step 15). Otherwise rebase or merge first.
- **`stale info` / rejected `--force-with-lease`** — The lease is working as
  intended: `git fetch origin`, review the new commits, incorporate them, then
  retry. Do not escalate to `--force`.
- **Merge/rebase conflict** — Not a failure; follow steps 13–14. Use `--abort` to
  return to pre-operation state.
- **`error: cannot rebase: You have unstaged changes`** — Stash first.
- **Detached HEAD** — Usually from checking out a SHA. If work was committed
  there, preserve with `git branch rescue/detached-work` then switch.
- **Accidentally reset/deleted commits** — Use `git reflog` to find the lost
  HEAD position and restore.
- **`gh: command not found`** — Fall back to printing the PR compare URL.

## Examples

### Example 1: "Squash my last 4 commits and clean up the message"

1. `git status` (clean) and `git log --oneline -6` — show the 4 commits to the user.
2. `git log origin/feature/login..HEAD` shows all 4 are pushed — warn about force-push.
3. `GIT_SEQUENCE_EDITOR="sed -i '2,\\$s/^pick/squash/'" git rebase -i HEAD~4`
4. Set combined message: `git commit --amend -m "feat(auth): add login flow with session persistence"`
5. Show divergence: `git log --oneline origin/feature/login..HEAD`
6. `git push --force-with-lease`

### Example 2: "My PR has conflicts with main, fix them"

1. `git status`, `git fetch origin`, then `git rebase origin/main` — conflicts.
2. `git diff --name-only --diff-filter=U` — list conflicted files.
3. Resolve each file (ours/theirs/manual), `git add`, `git rebase --continue`.
4. `git push --force-with-lease`, then `gh pr checks` to confirm CI passes.

### Example 3: "Undo my last commit — it went to the wrong branch"

1. `git log --oneline -3` — identify stray commit `e4f5a6b`.
2. `git log origin/main..HEAD` shows it's unpushed — safe to rewrite.
3. Preserve: `git branch feature/payment-retry e4f5a6b`
4. Remove from main: `git reset --hard HEAD~1`
5. Switch and verify: `git switch feature/payment-retry`

## Resources

- [Pro Git book (free, official)](https://git-scm.com/book/en/v2)
- [git-rebase documentation](https://git-scm.com/docs/git-rebase)
- [git-push documentation (`--force-with-lease`)](https://git-scm.com/docs/git-push)
- [git-revert vs git-reset](https://git-scm.com/docs/git-revert)
- [git-reflog](https://git-scm.com/docs/git-reflog)
- [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/)
- [GitHub CLI manual (`gh pr`)](https://cli.github.com/manual/gh_pr)
- [Oh Shit, Git!?!](https://ohshitgit.com/)
