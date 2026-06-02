---
name: flush
description: |
  Use when the user wants to manually flush a deferred-commit queue from a prior or interrupted chain. Reads .hyperflow/commits-queue/manifest.json, fast-forwards the staging branch onto the user's branch, deletes staging, clears the queue. Recovery interface when a chain crashed before its Step 4 auto-flush ran.
  Trigger with /hyperflow:flush, "flush pending commits", "flush queue", "apply staged commits", "where are my commits".
allowed-tools: Read, Bash(git:*), Bash(ls:*), Bash(cat:*), Bash(rm:*)
argument-hint: "[--dry-run]"
version: 4.12.6
license: MIT
compatibility: Designed for Claude Code
tags: [git, deferred-commits, recovery, lifecycle]
---

# Flush

Manually flush the deferred-commit queue from a chain that ran with `commit-when=end`. Normally `/hyperflow:dispatch` calls `scripts/flush-commits.sh` at its Step 4 wrap-up; this skill exists for the case where the chain was interrupted (crash, kill, context loss) before the auto-flush ran.

## Subcommands

| Subcommand | Description |
|---|---|
| (no arg) | Run `scripts/flush-commits.sh <project-root>` — fast-forward staging onto user's branch, delete staging, clear queue |
| `--dry-run` | Show what would be flushed without doing it. Lists the queued commits in order. |

## What gets flushed

`.hyperflow/commits-queue/manifest.json` tracks the chain's `user_branch`, `staging_branch` (always `hyperflow/staging-<chain-id>`), and the list of queued commits with SHAs and messages. Flush replays them via `git merge --ff-only` so:

- All N commits land on the user's branch with original SHAs preserved
- Order is chronological (queue-time order)
- Original commit messages are preserved
- Original file-to-message mapping is preserved (each commit touched exactly the files its sub-task touched)

## What happens if fast-forward isn't possible

If the user's branch diverged from staging (e.g. the user committed manually mid-chain on the same branch), `git merge --ff-only` refuses. The skill surfaces the error with two recovery options:

1. `git rebase hyperflow/staging-<chain-id>` — replay staging commits on top of user's new commits
2. `git cherry-pick <staging-base>..hyperflow/staging-<chain-id>` — selectively pick commits

The staging branch is preserved for the user to act on manually. The queue manifest stays in place so a future `/hyperflow:flush` retry can attempt again after the user resolves divergence.

## Flow

1. Check `.hyperflow/commits-queue/manifest.json` exists. If not, print `No queue to flush.` and stop.
2. Run `bash $PLUGIN_ROOT/scripts/flush-commits.sh $PROJECT_ROOT [--dry-run]`.
3. Print the script's output verbatim.

## Overview

`/hyperflow:flush` is the user-facing handle for the deferred-commit flush mechanism. Most users never call it explicitly — `/hyperflow:dispatch` Step 4 wrap-up runs the same script automatically. This skill exists for recovery: if a chain ran with `commit-when=end` and crashed before wrap-up, the queue persists on disk and the user can flush it later.

## Prerequisites

- `.hyperflow/commits-queue/manifest.json` exists from a prior chain run with `commit-when=end`.
- Git repository, on a branch the manifest's `user_branch` field can be checked out into.
- `scripts/flush-commits.sh` available in the plugin install.

## Error Handling

| Failure | Behavior |
|---|---|
| No manifest file present | Print `No queue to flush.` Exit 0. |
| Staging branch missing (manual deletion or rename) | Print warning; clear stale manifest. Exit 0. |
| Fast-forward not possible (user branch diverged) | Surface git error + recovery suggestions (rebase / cherry-pick). Leave staging branch + manifest intact for manual handling. Exit non-zero. |
| User on a branch other than manifest's user_branch | Check out manifest's user_branch automatically; if checkout fails, surface error. |

## Examples

### Dry-run before flushing

```
/hyperflow:flush --dry-run

flush-commits (DRY RUN): would fast-forward 7 commits from hyperflow/staging-2026-05-17-1430 onto feat/auth-refactor
abc1234 feat(auth): T7 wire login handler
def5678 feat(auth): T6 add session middleware
…
```

### Recovery after crash

```
You: /hyperflow:flush

flush-commits: flushed 7 commits onto feat/auth-refactor
abc1234 feat(auth): T7 wire login handler
…
```

## Resources

- [`scripts/flush-commits.sh`](../../scripts/flush-commits.sh) — the actual flush mechanism.
- [`scripts/queue-commit.sh`](../../scripts/queue-commit.sh) — the queue-write side called by dispatch during the chain.
- [DOCTRINE.md Layer 8](../hyperflow/DOCTRINE.md#layer-8-git-workflow) — `commit-when` timing rules.
