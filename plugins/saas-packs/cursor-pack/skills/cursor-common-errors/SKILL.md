---
name: "cursor-common-errors"
description: |
  Execute troubleshoot common Cursor IDE errors and issues. Triggers on "cursor error",
  "cursor not working", "cursor issue", "cursor problem", "fix cursor". Use when working with cursor common errors functionality. Trigger with phrases like "cursor common errors", "cursor errors", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Cursor Common Errors

## Overview

This skill helps troubleshoot common Cursor IDE errors and issues. It provides solutions for authentication problems, completion errors, indexing failures, API key issues, performance problems, and crash recovery procedures.

## Prerequisites

- Cursor IDE installed
- Understanding of common error types
- Access to logs and developer tools
- Network connectivity for support resources

## Instructions

1. Identify the error type (auth, completion, indexing, etc.)
2. Check common solutions for that error type
3. Review logs for specific error messages
4. Try basic troubleshooting (restart, clear cache)
5. Report persistent issues with full details
6. Document solutions for team reference

## Output

- Identified error cause
- Applied solution or workaround
- Documented fix for future reference
- Issue report if unresolved

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Troubleshooting Guide](https://cursor.com/docs/troubleshooting)
- [Cursor GitHub Issues](https://github.com/getcursor/cursor/issues)
- [Cursor Discord Support](https://discord.gg/cursor)
