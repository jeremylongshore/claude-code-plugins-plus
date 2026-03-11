---
name: "cursor-multi-repo"
description: |
  Manage work with multiple repositories in Cursor. Triggers on "cursor multi repo",
  "cursor multiple projects", "cursor monorepo", "cursor workspace". Use when working with cursor multi repo functionality. Trigger with phrases like "cursor multi repo", "cursor repo", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Multi Repo

## Overview

This skill guides you through working with multiple repositories in Cursor. It covers multi-root workspaces, monorepo patterns, selective indexing strategies, and cross-project context management for complex development environments.

## Prerequisites

- Multiple repositories or monorepo structure
- Understanding of workspace concepts
- Cursor IDE with workspace support
- Configured .cursorrules for each project

## Instructions

1. Decide on multi-repo strategy (separate windows, workspace, or monorepo)
2. Create workspace file or open specific packages
3. Configure .cursorrules inheritance (root + overrides)
4. Set up selective indexing with .cursorignore
5. Use full paths for @-mentions across projects
6. Test cross-project context and queries

## Output

- Functional multi-repository workspace
- Properly inherited .cursorrules
- Selective indexing per project
- Cross-project AI context awareness

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [VS Code Workspaces](https://code.visualstudio.com/docs/editor/workspaces)
- [Turborepo Documentation](https://turbo.build/repo/docs)
- [Cursor Multi-Project Guide](https://cursor.com/docs/workspaces)