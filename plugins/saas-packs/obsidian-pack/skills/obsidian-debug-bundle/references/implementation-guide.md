# Obsidian Debug Bundle - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash

BUNDLE_DIR="obsidian-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Obsidian Plugin Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect System Information
```bash
echo "--- System Information ---" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -s)" >> "$BUNDLE_DIR/summary.txt"
echo "OS Version: $(uname -r)" >> "$BUNDLE_DIR/summary.txt"
echo "Node.js: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Collect Plugin Information
```bash
PLUGIN_DIR="/path/to/your/plugin"

echo "--- Plugin Information ---" >> "$BUNDLE_DIR/summary.txt"
if [ -f "$PLUGIN_DIR/manifest.json" ]; then
  echo "Manifest:" >> "$BUNDLE_DIR/summary.txt"
  cat "$PLUGIN_DIR/manifest.json" >> "$BUNDLE_DIR/summary.txt"
  cp "$PLUGIN_DIR/manifest.json" "$BUNDLE_DIR/"
fi
echo "" >> "$BUNDLE_DIR/summary.txt"

if [ -f "$PLUGIN_DIR/package.json" ]; then
  echo "--- Dependencies ---" >> "$BUNDLE_DIR/summary.txt"
  cat "$PLUGIN_DIR/package.json" | grep -A 50 '"dependencies"' | head -60 >> "$BUNDLE_DIR/summary.txt"
  echo "" >> "$BUNDLE_DIR/summary.txt"
fi

if [ -f "$PLUGIN_DIR/tsconfig.json" ]; then
  cp "$PLUGIN_DIR/tsconfig.json" "$BUNDLE_DIR/"
fi
```

### Step 4: Collect Vault Information
```bash
VAULT_DIR="$HOME/ObsidianVault"

echo "--- Vault Information ---" >> "$BUNDLE_DIR/summary.txt"
if [ -d "$VAULT_DIR/.obsidian" ]; then
  echo "Vault exists: YES" >> "$BUNDLE_DIR/summary.txt"

  # Installed plugins (names only, no sensitive data)
  echo "Installed plugins:" >> "$BUNDLE_DIR/summary.txt"
  ls "$VAULT_DIR/.obsidian/plugins/" 2>/dev/null >> "$BUNDLE_DIR/summary.txt"

  # Enabled plugins
  if [ -f "$VAULT_DIR/.obsidian/community-plugins.json" ]; then
    echo "Enabled plugins:" >> "$BUNDLE_DIR/summary.txt"
    cat "$VAULT_DIR/.obsidian/community-plugins.json" >> "$BUNDLE_DIR/summary.txt"
  fi
fi
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 5: Collect Error Logs (from Console)
```markdown


## Complete Examples

### Automated Debug Command
```typescript
// Add debug export command to plugin
this.addCommand({
  id: 'export-debug-data',
  name: 'Export Debug Data',
  callback: async () => {
    const debugData = {
      manifest: this.manifest,
      settings: this.sanitizeSettings(),
      obsidianVersion: this.app.version,
      plugins: Object.keys((this.app as any).plugins.plugins),
    };

    const blob = new Blob([JSON.stringify(debugData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `${this.manifest.id}-debug.json`;
    a.click();

    URL.revokeObjectURL(url);
    new Notice('Debug data exported');
  },
});

private sanitizeSettings(): any {
  const settings = { ...this.settings };
  // Redact sensitive values
  for (const key of Object.keys(settings)) {
    if (key.toLowerCase().includes('key') ||
        key.toLowerCase().includes('token') ||
        key.toLowerCase().includes('secret')) {
      settings[key] = '[REDACTED]';
    }
  }
  return settings;
}
```

### Minimal Bug Report Template
```markdown


## Manual Console Log Collection

1. Open Obsidian
2. Press Ctrl/Cmd+Shift+I to open Developer Tools
3. Go to Console tab
4. Right-click in console area
5. Select "Save as..." → save to debug bundle directory
6. Name it "console-log.txt"
```

### Step 6: Collect Plugin Data (Sanitized)
```typescript
// Add to your plugin for debug export
export function exportDebugData(plugin: Plugin): object {
  return {
    pluginId: plugin.manifest.id,
    pluginVersion: plugin.manifest.version,
    obsidianVersion: process.versions?.electron ? 'desktop' : 'mobile',
    settings: sanitizeSettings(plugin.settings),
    timestamp: new Date().toISOString(),
  };
}

function sanitizeSettings(settings: any): any {
  const sanitized = { ...settings };
  // Remove sensitive fields
  const sensitiveKeys = ['apiKey', 'token', 'password', 'secret'];
  for (const key of sensitiveKeys) {
    if (key in sanitized) {
      sanitized[key] = '[REDACTED]';
    }
  }
  return sanitized;
}
```

### Step 7: Package Bundle
```bash
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"

sha256sum "$BUNDLE_DIR.tar.gz" > "$BUNDLE_DIR.tar.gz.sha256"
```


## Bug Report

**Plugin:** [Name] v[Version]
**Obsidian:** v[Version]
**OS:** [Windows/macOS/Linux]

### Steps to Reproduce
1.
2.
3.

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Console Errors
```
[Paste errors here]
```

### Debug Bundle
[Attach obsidian-debug-*.tar.gz]
```

### Privacy Checklist Before Sharing
- [ ] API keys removed
- [ ] Personal paths sanitized
- [ ] Note content not included
- [ ] Vault name generic or removed
- [ ] No personal identifiers
