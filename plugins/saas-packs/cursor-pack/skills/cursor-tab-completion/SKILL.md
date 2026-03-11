---
name: "cursor-tab-completion"
description: |
  Manage master Cursor tab completion and AI code suggestions. Triggers on "cursor completion",
  "cursor tab", "cursor suggestions", "cursor autocomplete", "cursor ghost text". Use when working with cursor tab completion functionality. Trigger with phrases like "cursor tab completion", "cursor completion", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Tab Completion

## Overview

This skill helps you master Cursor tab completion and AI code suggestions. It covers how completions work, acceptance techniques, context awareness, and configuration settings to optimize your coding flow with AI assistance.

## Prerequisites

- Cursor IDE with completions enabled
- Project with indexed codebase
- Understanding of ghost text interface
- Configured .cursorrules for project patterns

## Instructions

1. Start typing code in a file
2. Wait for ghost text to appear (gray suggestion)
3. Press Tab to accept full suggestion
4. Press Ctrl+Right to accept word by word
5. Press Esc to dismiss unwanted suggestions
6. Use Ctrl+Space to force trigger completion

## Output

- AI-generated code completions
- Pattern-aware suggestions
- Context-sensitive function bodies
- Consistent code style matching project

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Tab Completion Guide](https://cursor.com/docs/completions)
- [Completion Settings](https://cursor.com/docs/settings)
- [Context for Better Completions](https://cursor.com/docs/context)