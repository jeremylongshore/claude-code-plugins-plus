---
name: "cursor-git-integration"
description: |
  Manage integrate Git workflows with Cursor IDE. Triggers on "cursor git",
  "git in cursor", "cursor version control", "cursor commit", "cursor branch". Use when working with cursor git integration functionality. Trigger with phrases like "cursor git integration", "cursor integration", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Git Integration

## Overview

This skill covers integrating Git workflows with Cursor IDE. It provides guidance on AI-powered commit messages, code review assistance, conflict resolution, and branch management to streamline your version control workflow.

## Prerequisites

- Git installed and configured
- Project initialized as git repository
- Cursor IDE with Git extension enabled
- Basic understanding of Git workflows

## Instructions

1. Open your git repository in Cursor
2. Access Source Control panel (Cmd+Shift+G)
3. Stage changes by clicking + on files
4. Use AI to generate commit messages
5. Push changes to remote repository
6. Use @git in chat for AI-assisted reviews

## Output

- Integrated Git workflow in Cursor
- AI-generated commit messages
- AI-assisted code review
- Streamlined branch management
- Conflict resolution assistance

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Git Documentation](https://git-scm.com/doc)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitLens Extension](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens)