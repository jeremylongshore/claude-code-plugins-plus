---
name: generating-smart-commits
description: |
  This skill generates conventional commit messages using AI analysis of staged Git changes. It automatically determines the commit type (feat, fix, docs, etc.), identifies breaking changes, and formats the message according to conventional commit standards. Use this when asked to create a commit message, write a Git commit, or when the user uses the `/commit-smart` or `/gc` command. It is especially useful after changes have been staged with `git add`.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill empowers Claude to create well-formatted, informative commit messages automatically. By analyzing staged changes, it generates messages that adhere to conventional commit standards, saving developers time and ensuring consistency.

## How It Works

1. **Analyzing Staged Changes**: The skill examines the changes currently staged in the Git repository.
2. **Generating Commit Message**: Based on the analysis, it constructs a conventional commit message, including type, scope, and description.
3. **Presenting for Confirmation**: The generated message is displayed to the user for review and approval.

## When to Use This Skill

This skill activates when you need to:
- Create a commit message from staged changes.
- Generate a conventional commit message.
- Use the `/commit-smart` or `/gc` command.
- Automate the commit message writing process.

## Examples

### Example 1: Adding a New Feature

User request: "Generate a commit message for adding user authentication"

The skill will:
1. Analyze the staged changes related to user authentication.
2. Generate a commit message like: `feat(auth): Implement user authentication module`.
3. Present the message to the user for confirmation.

### Example 2: Fixing a Bug

User request: "/gc fix for login issue"

The skill will:
1. Analyze the staged changes related to the login issue.
2. Generate a commit message like: `fix(login): Resolve issue with incorrect password validation`.
3. Present the message to the user for confirmation.

## Best Practices

- **Stage Related Changes**: Ensure that only related changes are staged before generating the commit message.
- **Review Carefully**: Always review the generated commit message before committing to ensure accuracy and clarity.
- **Provide Context**: If necessary, provide additional context in the request to guide the AI analysis (e.g., `/gc - emphasize that this fixes a security vulnerability`).

## Integration

This skill integrates directly with the Git repository through Claude Code. It complements other Git-related skills by providing a streamlined way to create informative and standardized commit messages.