# Troubleshooting Upgrades

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
