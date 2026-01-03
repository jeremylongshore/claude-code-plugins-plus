---
name: windsurf-keyboard-shortcuts
description: |
  Configure custom keyboard shortcuts for Cascade and AI features. Activate when users mention
  "keyboard shortcuts", "keybindings", "hotkeys", "shortcut configuration",
  or "customize shortcuts". Handles keybinding setup and optimization.
allowed-tools: Read,Write,Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Keyboard Shortcuts

Configure efficient keyboard shortcuts for AI-assisted development workflows.

## Directory Structure

```
~/.windsurf/
    keybindings.json             # Custom keyboard shortcuts
        # Cascade activation shortcuts
        # AI feature quick access
        # Custom workflow bindings
        # Override default bindings

    User/
        keybindings.json         # User-level shortcuts
            # Personal preferences
            # Platform-specific bindings
            # Conflict resolutions

project-root/
    .vscode/
        keybindings.json         # Project-specific shortcuts
            # Team-standard bindings
            # Project workflow shortcuts
            # Task automation triggers

    docs/
        shortcuts-reference.md   # Team shortcut documentation
            # Quick reference card
            # Category groupings
            # Common workflows
```

## Essential Shortcuts

### Cascade AI
- `Cmd/Ctrl + K` - Open Cascade panel
- `Cmd/Ctrl + Shift + K` - Cascade with selection
- `Cmd/Ctrl + L` - Inline completion accept
- `Escape` - Dismiss Cascade suggestions

### Multi-file Operations
- `Cmd/Ctrl + Shift + E` - Apply multi-file edit
- `Cmd/Ctrl + .` - Quick fix with AI
- `F2` - AI-assisted rename

### Navigation
- `Cmd/Ctrl + P` - Quick file open
- `Cmd/Ctrl + Shift + F` - AI-enhanced search
- `Cmd/Ctrl + G` - Go to line with context

## Configuration Steps

1. **Review Default Shortcuts**
   - Document existing bindings
   - Identify conflicts
   - Plan customizations

2. **Configure AI Shortcuts**
   - Set Cascade activation keys
   - Configure completion bindings
   - Add workflow shortcuts

3. **Optimize for Ergonomics**
   - Reduce repetitive strain patterns
   - Group related actions
   - Test shortcut accessibility

## Success Criteria

- All shortcuts functional without conflicts
- Sub-100ms response times
- 25% increase in coding velocity
