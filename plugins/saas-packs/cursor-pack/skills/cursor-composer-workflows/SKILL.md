---
name: "cursor-composer-workflows"
description: |
  Execute master Cursor Composer for multi-file AI edits. Triggers on "cursor composer",
  "multi-file edit", "cursor generate files", "composer workflow", "cursor scaffold". Use when working with cursor composer workflows functionality. Trigger with phrases like "cursor composer workflows", "cursor workflows", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Cursor Composer Workflows

## Overview

This skill helps you master Cursor Composer for multi-file AI edits. It provides workflow patterns for feature generation, scaffolding, refactoring, and incremental building to maximize your productivity with Composer.

## Prerequisites

- Cursor IDE with Composer feature access
- Project workspace with existing code patterns
- Understanding of multi-file editing workflows
- Configured .cursorrules for project standards

## Instructions

1. Open Composer (Cmd+I or Ctrl+I)
2. Describe the files and changes needed
3. Use @-mentions to reference existing patterns
4. Specify file structure preferences
5. Review all proposed changes
6. Apply changes and test

## Output

- Multi-file code generation
- Coordinated feature implementation
- Pattern-consistent scaffolding
- Refactored codebase

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Composer Documentation](https://cursor.com/docs/composer)
- [Multi-File Workflows](https://cursor.com/docs/workflows)
- [Cursor Best Practices](https://cursor.com/docs/best-practices)
