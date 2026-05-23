# Customizing Keybindings

## Customizing Keybindings

### Access Keybindings

```
Cmd+K Cmd+S (Mac)
Ctrl+K Ctrl+S (Windows/Linux)

Or: Command Palette > "Preferences: Open Keyboard Shortcuts"
```

### Custom Keybinding Example

```json
// keybindings.json
[
  {
    "key": "cmd+shift+c",
    "command": "cursor.newChat",
    "when": "editorTextFocus"
  },
  {
    "key": "cmd+shift+g",
    "command": "cursor.generateCode",
    "when": "editorTextFocus"
  }
]
```

### Cursor-Specific Commands

```json
// Available cursor.* commands
"cursor.newChat"
"cursor.toggleChat"
"cursor.acceptCompletion"
"cursor.rejectCompletion"
"cursor.triggerCompletion"
"cursor.openComposer"
"cursor.inlineEdit"
```
