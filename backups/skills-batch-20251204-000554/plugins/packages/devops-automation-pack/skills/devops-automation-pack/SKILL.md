---
name: generating-conventional-commits
description: |
  Generates conventional commit messages using AI. It analyzes code changes and suggests a commit message adhering to the conventional commits specification. Use this skill when you need help writing clear, standardized commit messages, especially after making code changes and preparing to commit. Trigger with terms like "create commit", "generate commit message", or "write commit".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill helps you create well-formatted, informative commit messages that follow the conventional commits standard, improving collaboration and automation in your Git workflow. It saves you time and ensures consistency across your project.

## How It Works

1. **Analyze Changes**: The skill analyzes the staged changes in your Git repository.
2. **Generate Suggestion**: It uses AI to generate a commit message based on the analyzed changes, adhering to the conventional commits format (e.g., `feat: add new feature`, `fix: correct bug`).
3. **Present to User**: The generated commit message is presented to you for review and acceptance.

## When to Use This Skill

This skill activates when you need to:
- Create a commit message after making code changes.
- Ensure your commit messages follow the conventional commits standard.
- Save time writing commit messages manually.

## Examples

### Example 1: Adding a New Feature

User request: "Generate a commit message for these changes."

The skill will:
1. Analyze the staged changes related to a new feature.
2. Generate a commit message like `feat: Implement user authentication`.

### Example 2: Fixing a Bug

User request: "Create a commit for the bug fix."

The skill will:
1. Analyze the staged changes related to a bug fix.
2. Generate a commit message like `fix: Resolve issue with incorrect password reset`.

## Best Practices

- **Stage Changes**: Ensure all relevant changes are staged before using the skill.
- **Review Carefully**: Always review the generated commit message before accepting it.
- **Customize if Needed**: Feel free to customize the generated message to provide more context.

## Integration

This skill integrates with your Git workflow, providing a convenient way to generate commit messages directly within Claude Code. It complements other Git-related skills in the DevOps Automation Pack, such as `/branch-create` and `/pr-create`.