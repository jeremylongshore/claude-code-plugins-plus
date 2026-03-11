---
name: "cursor-keybindings"
description: |
  Manage master Cursor keyboard shortcuts and customize keybindings. Triggers on "cursor shortcuts",
  "cursor keybindings", "cursor keyboard", "cursor hotkeys", "cursor commands". Use when working with cursor keybindings functionality. Trigger with phrases like "cursor keybindings", "cursor keybindings", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Keybindings

## Overview

This skill helps you master Cursor keyboard shortcuts and customize keybindings. It provides a complete reference for AI-specific shortcuts, standard editor commands, and guidance on resolving conflicts with Vim mode or other extensions.

## Prerequisites

- Cursor IDE installed
- Access to Keyboard Shortcuts editor
- Understanding of modifier keys (Cmd/Ctrl, Alt/Option, Shift)
- Optional: Vim mode extension if using Vim bindings

## Instructions

1. Open Keyboard Shortcuts (Cmd+K Cmd+S)
2. Search for the command to rebind
3. Click the pencil icon to edit
4. Press your new key combination
5. Resolve any conflicts shown
6. Save and test the new binding

## Output

- Customized keyboard shortcuts
- Resolved keybinding conflicts
- Vim mode compatibility (if configured)
- Personalized workflow efficiency

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [VS Code Key Bindings](https://code.visualstudio.com/docs/getstarted/keybindings)
- [Cursor Keyboard Shortcuts](https://cursor.com/docs/shortcuts)
- [Vim Extension Configuration](https://marketplace.visualstudio.com/items?itemName=vscodevim.vim)