---
name: "cursor-debug-bundle"
description: |
  Debug AI suggestions and code generation in Cursor. Triggers on "debug cursor ai",
  "cursor suggestions wrong", "bad cursor completion", "cursor ai debug". Use when debugging issues or troubleshooting. Trigger with phrases like "cursor debug bundle", "cursor bundle", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview

This skill helps debug AI suggestions and code generation issues in Cursor. It covers understanding why AI gives wrong suggestions, debugging completions, chat context issues, and diagnostic tools for troubleshooting AI behavior.

## Prerequisites

- Cursor IDE with AI features active
- Understanding of AI behavior factors
- Access to settings and developer tools
- Ability to view and export logs

## Instructions

1. Identify the type of AI issue (completion, chat, composer)
2. Check common causes (context, rules, model)
3. Use debugging tools (dev tools, verbose logging)
4. Test with different models and settings
5. Apply fix and verify improvement
6. Document solution for future reference

## Output

- Identified root cause of AI issues
- Improved AI suggestion quality
- Updated configuration if needed
- Documented debugging process

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Debug Guide](https://cursor.com/docs/debugging)
- [AI Troubleshooting](https://cursor.com/docs/troubleshooting)
- [Cursor GitHub Issues](https://github.com/getcursor/cursor/issues)