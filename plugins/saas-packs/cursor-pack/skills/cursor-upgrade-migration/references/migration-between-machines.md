# Migration Between Machines

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
