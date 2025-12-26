---
name: generating-smart-commits
description: |
  Use when generating conventional commit messages from staged git changes. Trigger with phrases like "create commit message", "generate smart commit", "/commit-smart", or "/gc". Automatically analyzes changes to determine commit type (feat, fix, docs), identifies breaking changes, and formats according to conventional commit standards.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure:
- Git repository is initialized in {baseDir}
- Changes are staged using `git add`
- User has permission to create commits
- Git user name and email are configured

## Instructions

1. **Analyze Staged Changes**: Examine git diff output to understand modifications
2. **Determine Commit Type**: Classify changes as feat, fix, docs, style, refactor, test, or chore
3. **Identify Scope**: Extract affected module or component from file paths
4. **Detect Breaking Changes**: Look for API changes, removed features, or incompatible modifications
5. **Format Message**: Construct message following pattern: `type(scope): description`
6. **Present for Review**: Show generated message and ask for confirmation before committing

## Output

Generates conventional commit messages in this format:

```
type(scope): brief description

- Detailed explanation of changes
- Why the change was necessary
- Impact on existing functionality

BREAKING CHANGE: description if applicable
```

Examples:
- `feat(auth): implement JWT authentication middleware`
- `fix(api): resolve null pointer exception in user endpoint`
- `docs(readme): update installation instructions`

## Error Handling

Common issues and solutions:

**No Staged Changes**
- Error: "No changes staged for commit"
- Solution: Stage files using `git add <files>` before generating commit message

**Git Not Initialized**
- Error: "Not a git repository"
- Solution: Initialize git with `git init` or navigate to repository root

**Uncommitted Changes**
- Warning: "Unstaged changes detected"
- Solution: Stage relevant changes or use `git stash` for unrelated modifications

**Invalid Commit Format**
- Error: "Generated message doesn't follow conventional format"
- Solution: Review and manually adjust type, scope, or description

## Resources

- Conventional Commits specification: https://www.conventionalcommits.org/
- Git commit best practices documentation
- Repository commit history for style consistency
- Project-specific commit guidelines in {baseDir}/CONTRIBUTING.md

## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.