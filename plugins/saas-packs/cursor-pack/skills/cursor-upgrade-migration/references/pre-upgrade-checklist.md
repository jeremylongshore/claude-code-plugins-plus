# Pre-Upgrade Checklist

## Pre-Upgrade Checklist

### Backup Current Settings

```bash
# Settings location
macOS: ~/Library/Application Support/Cursor/User/
Linux: ~/.config/Cursor/User/
Windows: %APPDATA%\Cursor\User\

# Backup command
cp -r ~/Library/Application\ Support/Cursor/User/ ~/cursor-backup/
```

### Export Key Configurations

```bash
# Export extensions list
cursor --list-extensions > my-extensions.txt

# Save important settings
cp ~/.cursor/settings.json ~/cursor-backup/
cp .cursorrules ~/cursor-backup/
```

### Document Current State

```
[ ] Note current version
[ ] List installed extensions
[ ] Screenshot custom keybindings
[ ] Note any custom configurations
[ ] Check if using custom API keys
```
