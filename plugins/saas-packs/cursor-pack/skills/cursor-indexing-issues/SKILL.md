---
name: "cursor-indexing-issues"
description: |
  Manage troubleshoot Cursor codebase indexing problems. Triggers on "cursor indexing",
  "cursor index", "cursor codebase", "@codebase not working", "cursor search broken". Use when working with cursor indexing issues functionality. Trigger with phrases like "cursor indexing issues", "cursor issues", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Cursor Indexing Issues

## Overview

This skill helps troubleshoot Cursor codebase indexing problems. It provides solutions for stuck indexing, empty search results, performance issues, and configuration optimization to ensure your codebase is properly indexed for AI features.

## Prerequisites

- Cursor IDE with indexing enabled
- Access to Cursor settings
- Command line access for cache clearing
- Understanding of project file structure

## Instructions

1. Check indexing status in status bar
2. Identify the specific issue (stuck, empty results, performance)
3. Review and update `.cursorignore` configuration
4. Try manual refresh via Command Palette
5. Clear index cache if issues persist
6. Restart Cursor and allow re-indexing

## Output

- Functional codebase indexing
- Working `@codebase` search queries
- Optimized indexing performance
- Properly configured exclusion patterns

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Indexing Documentation](https://cursor.com/docs/indexing)
- [File Watcher Configuration](https://code.visualstudio.com/docs/setup/linux#_visual-studio-code-is-unable-to-watch-for-file-changes-in-this-large-workspace-error-enospc)
- [Cursor GitHub Issues](https://github.com/getcursor/cursor/issues)
