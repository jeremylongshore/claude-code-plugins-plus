---
name: obsidian-debug-bundle
description: |
  Collect Obsidian plugin debug evidence for support and troubleshooting.
  Use when encountering persistent issues, preparing bug reports,
  or collecting diagnostic information for plugin problems.
  Trigger with phrases like "obsidian debug", "obsidian diagnostic",
  "collect obsidian logs", "obsidian support bundle".
allowed-tools: Read, Bash(grep:*), Bash(tar:*), Grep, Write
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect comprehensive diagnostics from an Obsidian vault: app version, installed plugins, active theme, vault stats, console errors, and CSS conflicts. Package everything into a markdown debug report.

## Prerequisites
- Access to the Obsidian vault's filesystem (the vault directory)
- Terminal access to run collection commands
- Developer Console access in Obsidian (Ctrl+Shift+I / Cmd+Option+I)

## Instructions

### Step 1: Identify the Vault Path

Obsidian stores vault data in the vault root under `.obsidian/`. Locate it:

```bash
# macOS
VAULT_PATH=~/Documents/MyVault

# Linux
VAULT_PATH=~/Obsidian/MyVault

# Windows (Git Bash)
VAULT_PATH="/c/Users/$USER/Documents/MyVault"

# Verify it's a valid vault
ls "$VAULT_PATH/.obsidian/app.json" && echo "Valid vault" || echo "Not a vault"
```

### Step 2: Collect Obsidian Version and App Settings

```bash
# Obsidian version is in the installer log or app settings
cat "$VAULT_PATH/.obsidian/app.json" 2>/dev/null | python3 -m json.tool

# Check installer version (macOS)
mdls -name kMDItemVersion /Applications/Obsidian.app 2>/dev/null

# Check installer version (Linux, snap)
snap info obsidian 2>/dev/null | grep installed
```

### Step 3: List Installed Plugins and Their Versions

```bash
# Active community plugins
echo "=== Active Plugins ==="
cat "$VAULT_PATH/.obsidian/community-plugins.json" 2>/dev/null | python3 -m json.tool

# Plugin details (name, version, minAppVersion)
echo "=== Plugin Manifests ==="
for dir in "$VAULT_PATH/.obsidian/plugins"/*/; do
  if [ -f "$dir/manifest.json" ]; then
    echo "--- $(basename "$dir") ---"
    python3 -c "
import json
m = json.load(open('$dir/manifest.json'))
print(f\"  version: {m.get('version', 'unknown')}\")
print(f\"  minAppVersion: {m.get('minAppVersion', 'unknown')}\")
print(f\"  author: {m.get('author', 'unknown')}\")
"
  fi
done
```

### Step 4: Collect Theme and Appearance Info

```bash
echo "=== Appearance ==="
cat "$VAULT_PATH/.obsidian/appearance.json" 2>/dev/null | python3 -m json.tool

# Check for custom CSS snippets
echo "=== CSS Snippets ==="
ls "$VAULT_PATH/.obsidian/snippets/" 2>/dev/null || echo "No snippets directory"

# Check active theme
THEME=$(python3 -c "
import json
try:
    a = json.load(open('$VAULT_PATH/.obsidian/appearance.json'))
    print(a.get('cssTheme', 'Default'))
except: print('Default')
")
echo "Active theme: $THEME"
```

### Step 5: Gather Vault Statistics

```bash
echo "=== Vault Stats ==="
# File counts by type
echo "Markdown files: $(find "$VAULT_PATH" -name '*.md' -not -path '*/.obsidian/*' -not -path '*/.trash/*' | wc -l)"
echo "Attachments: $(find "$VAULT_PATH" \( -name '*.png' -o -name '*.jpg' -o -name '*.pdf' -o -name '*.mp3' \) -not -path '*/.obsidian/*' | wc -l)"
echo "Total files: $(find "$VAULT_PATH" -type f -not -path '*/.obsidian/*' -not -path '*/.trash/*' | wc -l)"

# Vault size
echo "Vault size: $(du -sh "$VAULT_PATH" 2>/dev/null | cut -f1)"
echo ".obsidian size: $(du -sh "$VAULT_PATH/.obsidian" 2>/dev/null | cut -f1)"
```

### Step 6: Capture Console Errors

Open Obsidian's Developer Console (Ctrl+Shift+I / Cmd+Option+I), then run this in the Console tab to export errors:

```javascript
// Paste in Obsidian's Developer Console
(() => {
  const errors = [];
  const originalError = console.error;
  console.error = (...args) => {
    errors.push({ time: new Date().toISOString(), message: args.map(String).join(' ') });
    originalError.apply(console, args);
  };

  // After reproducing the issue, run:
  // copy(JSON.stringify(errors, null, 2))
  // This copies the error log to clipboard

  console.log(`Error capture active. Reproduce your issue, then run:
    copy(JSON.stringify(errors, null, 2))`);
})();
```

Alternatively, check for existing errors:

```javascript
// Quick dump of plugin load errors
app.plugins.manifests; // All registered plugins
app.plugins.enabledPlugins; // Currently enabled set
// Check if a specific plugin failed to load:
app.plugins.plugins['your-plugin']; // undefined = failed to load
```

### Step 7: Detect CSS Conflicts

```bash
# Check for snippet overrides that might conflict
for snippet in "$VAULT_PATH/.obsidian/snippets"/*.css; do
  [ -f "$snippet" ] || continue
  echo "=== $(basename "$snippet") ==="
  # Look for broad selectors that commonly cause conflicts
  grep -n 'body\b\|\.app-container\|\.workspace\|\.markdown-preview\|!important' "$snippet" | head -20
done

# Check theme CSS size (large themes are conflict-prone)
THEME_DIR="$VAULT_PATH/.obsidian/themes/$THEME"
if [ -d "$THEME_DIR" ]; then
  echo "Theme CSS size: $(wc -c < "$THEME_DIR/theme.css" 2>/dev/null) bytes"
fi
```

### Step 8: Generate the Debug Report

Combine all diagnostics into a single markdown note:

```bash
REPORT="$VAULT_PATH/debug-report-$(date +%Y%m%d-%H%M%S).md"

cat > "$REPORT" <<'HEADER'
# Obsidian Debug Report
HEADER

cat >> "$REPORT" <<EOF
Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Platform: $(uname -s) $(uname -m)
Node: $(node --version 2>/dev/null || echo 'N/A')

## App Settings
\`\`\`json
$(cat "$VAULT_PATH/.obsidian/app.json" 2>/dev/null || echo '{}')
\`\`\`

## Active Plugins
\`\`\`json
$(cat "$VAULT_PATH/.obsidian/community-plugins.json" 2>/dev/null || echo '[]')
\`\`\`

## Plugin Versions
$(for dir in "$VAULT_PATH/.obsidian/plugins"/*/; do
  [ -f "$dir/manifest.json" ] || continue
  name=$(python3 -c "import json; print(json.load(open('$dir/manifest.json')).get('name','?'))" 2>/dev/null)
  ver=$(python3 -c "import json; print(json.load(open('$dir/manifest.json')).get('version','?'))" 2>/dev/null)
  echo "- $name v$ver"
done)

## Appearance
\`\`\`json
$(cat "$VAULT_PATH/.obsidian/appearance.json" 2>/dev/null || echo '{}')
\`\`\`

## Vault Stats
- Markdown files: $(find "$VAULT_PATH" -name '*.md' -not -path '*/.obsidian/*' -not -path '*/.trash/*' 2>/dev/null | wc -l)
- Total files: $(find "$VAULT_PATH" -type f -not -path '*/.obsidian/*' -not -path '*/.trash/*' 2>/dev/null | wc -l)
- Vault size: $(du -sh "$VAULT_PATH" 2>/dev/null | cut -f1)

## CSS Snippets
$(ls "$VAULT_PATH/.obsidian/snippets/" 2>/dev/null || echo 'None')

## Notes
_Paste console errors below this line after reproducing the issue._

EOF

echo "Debug report written to: $REPORT"
```

## Output
- `debug-report-YYYYMMDD-HHMMSS.md` in the vault root containing:
  - Platform and Obsidian version
  - Complete plugin list with versions
  - Active theme and CSS snippet inventory
  - Vault statistics (file count, size)
  - Appearance configuration
  - Empty section for pasting console errors after reproducing the issue

## Error Handling
| Item | Privacy Risk | Action |
|------|-------------|--------|
| `app.json` | Contains vault path | Redact path before sharing |
| Plugin `data.json` | May contain API keys | Never include automatically |
| Console logs | May contain file names | Review before sharing |
| Vault path | Personal directory info | Replace with `<vault>` before sharing |
| CSS snippets | Generally safe | OK to share |
| `community-plugins.json` | Plugin list only | Safe to share |

## Examples

**Quick bug report**: Run Steps 2-5 from terminal, paste output into a GitHub issue. Add console errors from Step 6 if the issue involves runtime failures.

**Plugin developer diagnostics**: A user reports your plugin crashes. Ask them to run the Step 8 script and share the resulting `debug-report-*.md` file. Check their Obsidian version against your `manifest.json` `minAppVersion`, and look for plugin conflicts in the active plugins list.

**CSS debugging**: User reports broken styling. Run Step 7 to find `!important` overrides in snippets. Disable snippets one by one in Settings > Appearance > CSS snippets to isolate the conflict.

## Resources
- [Obsidian Bug Reports Forum](https://forum.obsidian.md/c/bug-reports/7)
- [Plugin Developer Help](https://forum.obsidian.md/c/developers/14)
- [Obsidian Discord #plugin-dev](https://discord.gg/obsidianmd)
- [Obsidian Developer Console](https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin#Debug+your+plugin)

## Next Steps
For systematic incident response, see `obsidian-incident-runbook`. For rate limit issues, see `obsidian-rate-limits`.
