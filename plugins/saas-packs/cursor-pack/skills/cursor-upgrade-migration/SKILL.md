---
name: cursor-upgrade-migration
description: |
  Upgrade Cursor versions and migrate settings. Triggers on "upgrade cursor",
  "update cursor", "cursor migration", "cursor new version", "cursor changelog".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Upgrade & Migration Guide

## Checking Current Version

### Version Information
```bash
# In terminal
cursor --version

# In Cursor
Help > About
# or
Cmd+Shift+P > "About"
```

### Release Notes
```
Check for updates:
- Help > Check for Updates
- https://cursor.com/changelog
- https://github.com/getcursor/cursor/releases
```

## Upgrade Methods

### Auto-Update (Recommended)
```
Cursor auto-updates by default:
1. Notification appears when update ready
2. Click "Restart to Update"
3. Cursor restarts with new version
4. Settings preserved automatically
```

### Manual Update

#### macOS
```bash
# Download latest from cursor.com
# Or via Homebrew
brew upgrade --cask cursor
```

#### Linux
```bash
# Download new AppImage from cursor.com
chmod +x cursor-new-version.AppImage

# Replace old version
mv cursor-new-version.AppImage /opt/cursor/cursor.AppImage
```

#### Windows
```powershell
# Download installer from cursor.com
# Run installer - updates in place

# Or via winget
winget upgrade Cursor.Cursor
```

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

## Migration Between Machines

### Using Settings Sync
```
1. Enable Settings Sync (Gear icon > Turn on Settings Sync)
2. Sign in with GitHub/Microsoft
3. Choose what to sync:
   - Settings
   - Keybindings
   - Extensions
   - UI State
4. On new machine, sign in and sync downloads
```

### Manual Migration
```bash
# On old machine - export
cursor --list-extensions > extensions.txt
cp -r ~/Library/Application\ Support/Cursor/User/ ./cursor-config/

# On new machine - import
cat extensions.txt | xargs -L 1 cursor --install-extension
cp -r ./cursor-config/* ~/Library/Application\ Support/Cursor/User/
```

### Critical Files to Transfer
```
Priority files:
- settings.json (all preferences)
- keybindings.json (custom shortcuts)
- .cursorrules (project rules - in repo)
- snippets/ (custom snippets)
- extensions.txt (extension list)
```

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

## Post-Upgrade Verification

### Verification Checklist
```
[ ] Cursor launches successfully
[ ] Sign in working
[ ] AI features functional
[ ] Completions appearing
[ ] Chat responding
[ ] Extensions loaded
[ ] Keybindings working
[ ] Projects open correctly
[ ] Indexing works
```

### Test AI Features
```
1. Open a project
2. Test completion: Type code, expect suggestions
3. Test chat: Cmd+L, ask question
4. Test composer: Cmd+I, request multi-file edit
5. Test @codebase: Search for function
```

## Troubleshooting Upgrades

### Settings Not Preserved
```
Recovery:
1. Check backup location
2. Restore from backup:
   cp ~/cursor-backup/* ~/Library/Application\ Support/Cursor/User/
3. Restart Cursor
```

### Extensions Missing
```
Re-install from list:
cat my-extensions.txt | xargs -L 1 cursor --install-extension

Or manually:
Cmd+Shift+X > Search > Install
```

### Performance Issues After Upgrade
```
Fixes:
1. Clear cache:
   rm -rf ~/Library/Application\ Support/Cursor/Cache/
   rm -rf ~/Library/Application\ Support/Cursor/CachedData/

2. Disable extensions, test, re-enable one by one

3. Reset settings to default, then reconfigure
```

### Rollback to Previous Version
```bash
# If needed, download specific version
# From GitHub releases or Cursor archive

# Remove current
brew uninstall cursor

# Install specific version
brew install --cask cursor@X.Y.Z
```

## Breaking Changes Log

### Major Version Changes
```
Keep track of breaking changes:

v0.x → v1.x:
- New settings schema
- Updated keybindings
- Changed model names

Always read changelog before major upgrades
```

### .cursorrules Format Changes
```
If format changes between versions:
1. Check documentation
2. Update to new format
3. Test with simple rules first
4. Migrate complex rules gradually
```

## Upgrade Best Practices

### Timing
```
- Don't upgrade mid-project deadline
- Upgrade in test environment first
- Allow time for adjustment
- Keep backup of working config
```

### Team Coordination
```
- Agree on upgrade schedule
- Share migration notes
- Update shared .cursorrules
- Document any issues/fixes
```
