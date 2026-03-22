---
name: "cursor-keybindings"
description: |
  Master Cursor keyboard shortcuts and customize keybindings for AI features and editor commands.
  Triggers on "cursor shortcuts", "cursor keybindings", "cursor keyboard", "cursor hotkeys",
  "cursor commands", "Cmd+K", "Cmd+L", "Cmd+I".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
tags: [saas, cursor, cursor-keybindings]

---
# Cursor Keybindings

Complete keyboard shortcut reference for Cursor IDE. Covers AI-specific shortcuts, standard editor commands, and customization. All shortcuts shown as macOS / Windows-Linux.

## AI Feature Shortcuts

### Primary AI Shortcuts

| Action | macOS | Windows/Linux | Notes |
|--------|-------|---------------|-------|
| **Chat panel** | `Cmd+L` | `Ctrl+L` | Open/focus AI chat sidebar |
| **Inline Edit** | `Cmd+K` | `Ctrl+K` | Edit selected code with AI |
| **Composer** | `Cmd+I` | `Ctrl+I` | Multi-file AI editing |
| **Full Composer** | `Cmd+Shift+I` | `Ctrl+Shift+I` | Expanded composer view |

### Context & Suggestions

| Action | macOS | Windows/Linux | Notes |
|--------|-------|---------------|-------|
| **Add to Chat context** | `Cmd+Shift+L` | `Ctrl+Shift+L` | Add selected code to existing chat |
| **Accept Tab suggestion** | `Tab` | `Tab` | Accept full ghost text |
| **Accept word-by-word** | `Cmd+→` | `Ctrl+→` | Partial Tab acceptance |
| **Dismiss suggestion** | `Esc` | `Esc` | Reject ghost text |
| **Force trigger completion** | `Ctrl+Space` | `Ctrl+Space` | Manually trigger Tab |
| **Accept inline edit** | `Cmd+Y` | `Ctrl+Y` | Accept Cmd+K changes |
| **Reject inline edit** | `Esc` | `Esc` | Dismiss Cmd+K changes |

### Chat Management

| Action | macOS | Windows/Linux | Notes |
|--------|-------|---------------|-------|
| **New chat** | `Cmd+N` (in chat) | `Ctrl+N` | Start fresh conversation |
| **Toggle chat panel** | `Cmd+L` | `Ctrl+L` | Show/hide chat sidebar |

## Essential Editor Shortcuts

### Navigation

| Action | macOS | Windows/Linux |
|--------|-------|---------------|
| Command Palette | `Cmd+Shift+P` | `Ctrl+Shift+P` |
| Quick Open file | `Cmd+P` | `Ctrl+P` |
| Go to Symbol | `Cmd+Shift+O` | `Ctrl+Shift+O` |
| Go to Line | `Cmd+G` | `Ctrl+G` |
| Go to Definition | `F12` | `F12` |
| Peek Definition | `Option+F12` | `Alt+F12` |
| Go Back | `Cmd+-` | `Ctrl+-` |
| Go Forward | `Cmd+Shift+-` | `Ctrl+Shift+-` |

### Editing

| Action | macOS | Windows/Linux |
|--------|-------|---------------|
| Multi-cursor (add) | `Option+Click` | `Alt+Click` |
| Select all occurrences | `Cmd+Shift+L` | `Ctrl+Shift+L` |
| Move line up/down | `Option+↑/↓` | `Alt+↑/↓` |
| Duplicate line | `Shift+Option+↑/↓` | `Shift+Alt+↑/↓` |
| Delete line | `Cmd+Shift+K` | `Ctrl+Shift+K` |
| Toggle comment | `Cmd+/` | `Ctrl+/` |
| Format document | `Shift+Option+F` | `Shift+Alt+F` |
| Rename symbol | `F2` | `F2` |
| Quick Fix | `Cmd+.` | `Ctrl+.` |

### Panels & Views

| Action | macOS | Windows/Linux |
|--------|-------|---------------|
| Toggle terminal | `` Cmd+` `` | `` Ctrl+` `` |
| Toggle sidebar | `Cmd+B` | `Ctrl+B` |
| Source Control | `Cmd+Shift+G` | `Ctrl+Shift+G` |
| Extensions | `Cmd+Shift+X` | `Ctrl+Shift+X` |
| Explorer | `Cmd+Shift+E` | `Ctrl+Shift+E` |
| Search across files | `Cmd+Shift+F` | `Ctrl+Shift+F` |
| Keyboard shortcuts editor | `Cmd+K Cmd+S` | `Ctrl+K Ctrl+S` |

## Customizing Keybindings

### Via UI

1. `Cmd+K Cmd+S` to open Keyboard Shortcuts editor
2. Search for the command (e.g., "accept cursor tab")
3. Click the pencil icon next to the keybinding
4. Press your desired key combination
5. If conflict detected, choose to override or cancel

### Via JSON

Open `keybindings.json`: `Cmd+Shift+P` > `Open Keyboard Shortcuts (JSON)`

```json
[
  {
    "key": "cmd+enter",
    "command": "editor.action.inlineSuggest.commit",
    "when": "inlineSuggestionVisible"
  },
  {
    "key": "ctrl+shift+k",
    "command": "aichat.newchat",
    "when": "editorFocus"
  },
  {
    "key": "cmd+k cmd+a",
    "command": "editor.action.selectAll",
    "when": "editorTextFocus && !editorReadonly"
  }
]
```

### Vim Mode Compatibility

If using the Vim extension with Cursor:

```json
// keybindings.json -- resolve Vim conflicts
[
  {
    "key": "ctrl+l",
    "command": "aichat.focus",
    "when": "!vim.active || vim.mode == 'Normal'"
  },
  {
    "key": "ctrl+k",
    "command": "cursor.edit",
    "when": "editorTextFocus && !vim.active"
  }
]
```

Common Vim conflicts:
- `Ctrl+K` conflicts with Vim's digraph mode
- `Ctrl+L` conflicts with Vim's clear/redraw
- `Ctrl+I` conflicts with Vim's jump forward

Solution: Remap Cursor AI shortcuts to avoid Vim's control sequences, or use `when` clauses to scope by Vim mode.

## Cheat Sheet (Print-Friendly)

```
╔══════════════════════════════════════════════╗
║  CURSOR AI SHORTCUTS (macOS)                 ║
╠══════════════════════════════════════════════╣
║  Cmd+L       Chat panel                     ║
║  Cmd+K       Inline edit (select first)     ║
║  Cmd+I       Composer (multi-file)          ║
║  Cmd+Shift+L Add selection to chat          ║
║  Tab         Accept Tab suggestion          ║
║  Cmd+→       Accept suggestion word-by-word ║
║  Esc         Dismiss suggestion             ║
║  Cmd+Y       Accept inline edit             ║
║  Cmd+Shift+P Command Palette               ║
║  Cmd+P       Quick Open file                ║
╚══════════════════════════════════════════════╝
```

## Enterprise Considerations

- **Keybinding policies**: Teams can share a `keybindings.json` in the project repo (`.vscode/keybindings.json`)
- **Accessibility**: Cursor supports screen readers and keyboard-only navigation via standard VS Code accessibility features
- **Corporate keyboards**: International keyboard layouts may require different mappings for Cmd+K/L/I

## Resources

- [Cursor Keyboard Shortcuts](https://docs.cursor.com/kbd)
- [VS Code Keybindings](https://code.visualstudio.com/docs/getstarted/keybindings)
- [Vim Extension](https://marketplace.visualstudio.com/items?itemName=vscodevim.vim)
