# Extension Optimization

## Extension Optimization

### Audit Extensions

```
1. List all extensions:
   cursor --list-extensions

2. Check which are active:
   Help > Process Explorer > Extension Host

3. Disable unused:
   Extensions panel > Right-click > Disable

4. Remove unnecessary:
   cursor --uninstall-extension [id]
```

### Workspace-Specific Extensions

```json
// Only enable project-relevant extensions
// .vscode/settings.json
{
  "extensions.autoUpdate": "onlyEnabledExtensions"
}

// Disable globally, enable per-workspace
// For heavy extensions like language servers
```

### Extension Load Optimization

```json
{
  // Delay extension activation
  "extensions.autoUpdate": false,
  "extensions.autoCheckUpdates": false,

  // Disable telemetry (slight improvement)
  "telemetry.telemetryLevel": "off"
}
```
