# Performance Optimization

## Performance Optimization

### Reducing Extension Overhead

```
Disable when not needed:
- Project-specific extensions
- Heavy language servers
- Visual decorations

Check extension impact:
- Help > Process Explorer
- Look for high CPU extensions
```

### Workspace-Specific Extensions

```json
// .vscode/settings.json
{
  // Enable only for this workspace
  "extensions.autoUpdate": "onlyEnabledExtensions",
  "extensions.ignoreRecommendations": true
}
```

### Remote/SSH Considerations

```
When using remote development:
- Install extensions on remote
- Minimize local extensions
- Use extension packs
```
