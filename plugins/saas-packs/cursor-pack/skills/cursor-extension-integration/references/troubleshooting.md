# Troubleshooting

## Troubleshooting

### Extension Not Working

```
Steps:
1. Check compatibility (VS Code version)
2. Reload Cursor (Cmd+Shift+P > Reload)
3. Check extension output (Output panel)
4. Disable/enable extension
5. Reinstall extension
6. Check for updates
```

### Extension Causing Issues

```
Isolate the problem:
1. Disable all extensions
   cursor --disable-extensions
2. Test Cursor
3. Enable extensions one by one
4. Find problematic extension
5. Report to extension author
```

### Extension Settings Reset

```bash
# Reset extension data
rm -rf ~/.cursor/extensions/[extension-name]/

# Or reinstall
cursor --uninstall-extension [id]
cursor --install-extension [id]
```
