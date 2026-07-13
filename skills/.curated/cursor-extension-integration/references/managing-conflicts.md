# Managing Conflicts

## Managing Conflicts

### Cursor AI vs Other AI

```
Disable conflicting extensions:
1. Extensions panel (Cmd+Shift+X)
2. Find Copilot/TabNine/IntelliCode
3. Click "Disable"
4. Reload Cursor

Or via settings:
{
  "github.copilot.enable": {
    "*": false
  }
}
```

### Completion Conflicts

```
If completions behave strangely:

1. Disable other suggestion providers:
{
  "editor.suggest.showMethods": false,
  // from non-Cursor sources
}

2. Ensure Cursor completions enabled:
{
  "cursor.completion.enabled": true,
  "editor.inlineSuggest.enabled": true
}

3. Check extension interference:
- Disable extensions one by one
- Find the conflicting one
- Keep disabled or configure
```

### Keybinding Conflicts

```
Find conflicts:
1. Cmd+K Cmd+S (Keyboard Shortcuts)
2. Search for conflicting key
3. See which extensions bind it
4. Rebind as needed

Common conflicts:
- Cmd+K (Cursor inline edit)
- Cmd+L (Cursor chat)
- Tab (completions)
```
