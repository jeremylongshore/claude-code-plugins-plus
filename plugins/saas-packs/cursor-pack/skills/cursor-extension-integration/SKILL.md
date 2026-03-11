---
name: "cursor-extension-integration"
description: |
  Manage integrate VS Code extensions with Cursor. Triggers on "cursor extensions",
  "cursor vscode extensions", "cursor plugins", "cursor marketplace". Use when working with cursor extension integration functionality. Trigger with phrases like "cursor extension integration", "cursor integration", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Cursor Extension Integration

## Overview

This skill helps integrate VS Code extensions with Cursor IDE. It covers extension compatibility, conflict resolution, essential extensions for development, and performance optimization to enhance your Cursor environment.

## Prerequisites

- Cursor IDE installed
- VS Code marketplace access
- Understanding of extension compatibility
- Awareness of potential conflicts with AI features

## Instructions

1. Open Extensions panel (Cmd+Shift+X)
2. Search for desired extension
3. Check compatibility and conflict warnings
4. Install and reload if prompted
5. Configure extension settings
6. Disable conflicting AI extensions (Copilot, TabNine)

## Output

- Enhanced Cursor functionality with extensions
- Configured extension settings
- Resolved keybinding conflicts
- Optimized extension performance

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [VS Code Marketplace](https://marketplace.visualstudio.com/)
- [Cursor Extension Compatibility](https://cursor.com/docs/extensions)
- [Extension Development Guide](https://code.visualstudio.com/api)
