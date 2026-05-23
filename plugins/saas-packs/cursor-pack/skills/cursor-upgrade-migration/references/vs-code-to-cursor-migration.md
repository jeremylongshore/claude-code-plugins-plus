# Vs Code To Cursor Migration

## VS Code to Cursor Migration

### Automatic Import

```
First launch of Cursor:
- Detects VS Code installation
- Offers to import settings
- Imports: settings, keybindings, extensions
```

### Manual Import

```bash
# VS Code settings location
macOS: ~/Library/Application Support/Code/User/
Linux: ~/.config/Code/User/
Windows: %APPDATA%\Code\User\

# Copy to Cursor
cp ~/Library/Application\ Support/Code/User/settings.json \
   ~/Library/Application\ Support/Cursor/User/
```

### Extension Compatibility

```
Most VS Code extensions work in Cursor:
- Language extensions ✓
- Themes ✓
- Formatters ✓
- Git extensions ✓

May conflict:
- AI/Copilot extensions (disable to avoid conflict)
- Other code completion tools
```
