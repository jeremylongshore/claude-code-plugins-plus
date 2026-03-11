---
name: obsidian-core-workflow-b
description: |
  Execute Obsidian secondary workflow: UI components and user interaction.
  Use when building modals, views, suggestions, or custom UI elements.
  Trigger with phrases like "obsidian modal", "obsidian UI",
  "obsidian view", "obsidian custom interface".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Core Workflow B: UI Components

## Overview
Secondary workflow for Obsidian: building modals, views, suggestion popups, and custom UI elements.

## Prerequisites
- Completed `obsidian-install-auth` setup
- Familiarity with `obsidian-core-workflow-a`
- Understanding of DOM manipulation

## Instructions

### Step 1: Modal Dialogs

### Step 2: Suggestion Popups (FuzzySuggestModal)

### Step 3: Custom Views (Leaf Views)

### Step 4: Editor Extensions (CodeMirror 6)

### Step 5: Context Menus

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Modal dialogs for user input
- Suggestion popups with fuzzy search
- Custom sidebar views
- Editor decorations
- Context menus

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| View not showing | Not registered | Call `registerView` in `onload` |
| Modal closes immediately | Event propagation | Stop event propagation |
| Decorations not updating | Missing update handler | Implement `update` method |
| Menu item missing | Wrong event | Verify event type |

## Resources
- [Obsidian Modal Reference](https://docs.obsidian.md/Reference/TypeScript+API/Modal)
- [Obsidian View Reference](https://docs.obsidian.md/Reference/TypeScript+API/ItemView)
- [CodeMirror 6 Documentation](https://codemirror.net/docs/)

## Next Steps
For common errors, see `obsidian-common-errors`.

## Examples

**Basic usage**: Apply obsidian core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize obsidian core workflow b for production environments with multiple constraints and team-specific requirements.