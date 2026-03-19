---
name: gh-dash
description: |
  Provides a GitHub pull request dashboard directly in the terminal. Use when
  the user wants to view PR status, check CI/CD progress, review bot comments,
  or merge pull requests without leaving Claude Code. Trigger with phrases like
  "show PR dashboard", "PR status", "check CI progress", "merge this PR",
  or "review pull request".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
version: 1.0.0
author: Jake Kozloski <jakozloski@gmail.com>
license: MIT
compatible-with: claude-code
tags: [github, pull-request, ci-cd, dashboard, devops, merge, code-review]
---

# gh-dash

## Current State
!`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'Not in a git repo'`
!`gh auth status 2>&1 | head -1`

GitHub pull request dashboard for Claude Code with CI/CD monitoring and merge capabilities.

## Overview

This skill brings a complete GitHub pull request dashboard into your terminal workflow. Instead of switching to a browser to check PR status, review CI results, or merge branches, gh-dash consolidates all PR information into a single view. It displays real-time CI/CD progress with a visual progress bar, detects and summarizes bot comments (CodeRabbit, Cursor Bugbot, Coverage reporters), shows files changed with line-level statistics, and provides one-command merge operations with support for squash, merge commit, and rebase strategies.

The skill relies on the GitHub CLI (`gh`) for all API interactions, so it works with any GitHub repository where you have appropriate permissions. It respects branch protection rules, required reviews, and status checks, surfacing any blockers clearly before allowing merge operations.

## Instructions

1. **View PR status** for the current branch:
   - Navigate to the repository directory
   - Ask: "Show me the PR dashboard" or "What's the status of my PR?"
   - The skill runs `gh pr view` and `gh pr checks` to gather PR metadata, review status, and CI results

2. **Check CI/CD progress:**
   - Ask: "How are the CI checks doing?" or "Is CI passing?"
   - The skill displays each check with its status (pass, fail, pending), elapsed time, and a visual progress indicator
   - Failed checks include the failure reason and a link to the full log

3. **Review bot comments:**
   - Ask: "What did the bots say?" or "Show code review comments"
   - The skill filters PR comments to identify automated reviewers (CodeRabbit, Dependabot, coverage bots) and summarizes their findings separately from human reviews

4. **Merge the PR:**
   - Ask: "Merge this PR" or "Squash merge"
   - Supported strategies: `squash` (default), `merge`, `rebase`
   - The skill checks for required reviews, passing CI, and branch protection before attempting the merge
   - After merging, it optionally deletes the remote branch and checks out the default branch

5. **View file changes:**
   - Ask: "What files changed in this PR?"
   - Displays a summary of files added, modified, and deleted with line counts

## Output

The skill produces formatted terminal output covering:

- **PR Summary**: Title, description, author, branch, labels, reviewers, and age of the PR.
- **CI/CD Status Table**: Each workflow check listed with status icon, check name, elapsed time, and conclusion. A progress bar shows overall completion percentage.
- **Bot Comment Summary**: Grouped by bot type, showing the number of comments, key findings (e.g., "CodeRabbit found 3 suggestions"), and links to individual comments.
- **Files Changed**: Table of modified files with insertions/deletions counts and file type indicators.
- **Merge Result**: Confirmation of merge strategy used, resulting commit SHA, and branch cleanup status.

## Examples

### Example 1: Quick PR Status Check

**User:** "What's the status of my PR?"

The skill will:
1. Run `gh pr view --json title,state,reviews,statusCheckRollup,additions,deletions,changedFiles` to gather data.
2. Display a formatted summary showing the PR title, review approvals, and CI status.
3. Highlight any blockers: failing checks, requested changes, or missing required reviews.

### Example 2: Merge After CI Passes

**User:** "Merge this PR with squash."

The skill will:
1. Verify all required status checks are passing with `gh pr checks`.
2. Confirm the PR has sufficient approvals.
3. Execute `gh pr merge --squash --delete-branch` to squash-merge and clean up the branch.
4. Report the merge commit SHA and confirm the remote branch was deleted.

### Example 3: Review Bot Feedback

**User:** "Summarize the bot comments on this PR."

The skill will:
1. Fetch all PR comments with `gh api repos/{owner}/{repo}/pulls/{number}/comments`.
2. Identify automated comments by known bot usernames and patterns.
3. Group findings by bot: CodeRabbit suggestions, coverage report deltas, security scan results.
4. Present a concise summary with links to the full comments for follow-up.

## Prerequisites

- **GitHub CLI (`gh`)** must be installed and authenticated (`gh auth status` to verify).
- The current directory must be inside a git repository with a GitHub remote.
- Appropriate permissions for the operations requested (write access for merging).

## Error Handling

- **No PR found for current branch:** Suggests creating a PR with `gh pr create` or checking out the correct branch.
- **CI checks still running:** Reports which checks are pending and offers to wait or proceed.
- **Merge blocked:** Clearly states the blocking reason (failed checks, missing reviews, branch protection) and suggests remediation steps.
- **GitHub CLI not installed:** Detects missing `gh` command and provides installation instructions for the current platform.
