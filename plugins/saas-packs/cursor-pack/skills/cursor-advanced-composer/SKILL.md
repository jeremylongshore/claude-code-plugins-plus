---
name: "cursor-advanced-composer"
description: |
  Manage advanced Cursor Composer techniques for complex edits. Triggers on "advanced composer",
  "composer patterns", "multi-file generation", "composer refactoring". Use when working with cursor advanced composer functionality. Trigger with phrases like "cursor advanced composer", "cursor composer", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Advanced Composer

## Overview

This skill covers advanced Cursor Composer techniques for complex multi-file edits. It provides patterns for coordinated file creation, architecture migrations, pattern replication, and quality control workflows for large-scale code generation.

## Prerequisites

- Cursor IDE with Composer feature access
- Understanding of project structure and patterns
- Well-configured .cursorrules file
- Indexed codebase for @-mention references

## Instructions

1. Open Composer with Cmd+I (Mac) or Ctrl+I (Windows)
2. Describe the feature or changes needed
3. Reference existing patterns with @-mentions
4. Specify file structure and naming conventions
5. Review each proposed change before applying
6. Apply changes incrementally, testing between phases

## Output

- Multiple coordinated file changes
- Generated feature modules with consistent patterns
- Refactored codebase following specified patterns
- Complete test coverage for generated code

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Composer Documentation](https://cursor.com/docs/composer)
- [Multi-File Editing Best Practices](https://cursor.com/docs/best-practices)
- [Cursor Community Tips](https://forum.cursor.com/)