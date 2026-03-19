---
name: generating-smart-commits
description: |
  Execute use when generating conventional commit messages from staged git changes. Trigger with phrases like "create commit message", "generate smart commit", "/commit-smart", or "/gc". Automatically analyzes changes to determine commit type (feat, fix, docs), identifies breaking changes, and formats according to conventional commit standards.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Generating Smart Commits

## Current State
!`git diff --cached --stat`
!`git log --oneline -5`
!`git status --short`

## Overview

Analyze staged git changes and generate Conventional Commits messages with accurate type classification, scope detection, and breaking change identification. Supports `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, and `build` types following the Conventional Commits 1.0.0 specification.

## Prerequisites

- Git repository initialized in the working directory
- Changes staged via `git add` (at least one staged file)
- Git user name and email configured (`git config user.name`, `git config user.email`)
- Understanding of the project's commit message conventions (check recent history)

## Instructions

1. Run `git diff --cached --stat` to get an overview of staged files and change volume
2. Run `git diff --cached` to examine the actual code changes in detail
3. Classify the commit type based on the nature of changes:
   - `feat`: new functionality visible to users
   - `fix`: bug correction
   - `refactor`: code restructuring without behavior change
   - `docs`: documentation only
   - `test`: adding or updating tests
   - `chore`: build process, dependencies, or tooling
   - `perf`: performance improvement
   - `ci`: CI/CD configuration changes
4. Determine scope from the primary directory or module affected (e.g., `auth`, `api`, `cli`, `db`)
5. Check for breaking changes: removed public APIs, changed function signatures, renamed exports, schema migrations
6. Check recent commit history with `git log --oneline -10` to match the project's style conventions
7. Construct the commit message: `type(scope): imperative description under 72 characters`
8. Add a body with bullet points explaining the "why" behind the change if the diff is non-trivial
9. Append `BREAKING CHANGE:` footer if applicable

## Output

Conventional commit message following this format:

```
type(scope): imperative description

- Explanation of what changed and why
- Impact on existing functionality

BREAKING CHANGE: description (if applicable)
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `No changes staged for commit` | Nothing added to staging area | Run `git add <files>` to stage changes before generating the message |
| `Not a git repository` | Working directory is not inside a git repo | Run `git init` or navigate to the repository root |
| `Ambiguous commit type` | Changes span multiple categories (feature + fix) | Split into separate commits or use the primary intent as the type |
| `Scope unclear from file paths` | Changes touch many unrelated directories | Use the most significant module or omit scope entirely |
| `Commit message exceeds 72 characters` | Description too verbose | Shorten to the essential action; move details to the commit body |

## Examples

- "Analyze my staged changes and generate a conventional commit message with the right type and scope."
- "Create a commit message for these changes, checking if there are any breaking changes in the API."
- "Generate a smart commit following this project's existing commit style (check the last 10 commits)."

## Resources

- Conventional Commits specification: https://www.conventionalcommits.org/en/v1.0.0/
- Angular commit guidelines: https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit
- Git commit best practices: https://cbea.ms/git-commit/