---
name: windsurf-upgrade-migration
description: |
  Upgrade Windsurf IDE, migrate settings from VS Code or Cursor, and handle breaking changes.
  Use when upgrading Windsurf versions, migrating from another editor,
  or handling configuration changes after updates.
  Trigger with phrases like "upgrade windsurf", "windsurf update",
  "migrate to windsurf", "windsurf from cursor", "windsurf from vscode".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, migration, upgrade, vscode]

---
# Windsurf Upgrade & Migration

## Current State
!`windsurf --version 2>/dev/null || echo 'Not installed'`
!`code --version 2>/dev/null | head -1 || echo 'VS Code not installed'`

## Overview
Guide for upgrading Windsurf to new versions and migrating from VS Code or Cursor. Covers settings transfer, extension compatibility, and Windsurf-specific configuration that doesn't exist in other editors.

## Prerequisites
- Current editor installation accessible
- Git for version controlling config files
- Backup of existing settings

## Instructions

### Step 1: Check Current Windsurf Version

```bash
# Current version
windsurf --version

# Check for updates
# Windsurf auto-updates by default
# Manual: Help > Check for Updates (or download from windsurf.com)
```

### Step 2: Migrate from VS Code

Windsurf is VS Code-based and supports most VS Code settings and extensions:

```bash
# Windsurf imports VS Code settings on first launch
# For manual migration:

# 1. Export VS Code extensions list
code --list-extensions > vscode-extensions.txt

# 2. Install in Windsurf
cat vscode-extensions.txt | xargs -L1 windsurf --install-extension

# 3. Copy settings
# macOS:
cp ~/Library/Application\ Support/Code/User/settings.json \
   ~/Library/Application\ Support/Windsurf/User/settings.json

# Linux:
cp ~/.config/Code/User/settings.json \
   ~/.config/Windsurf/User/settings.json
```

**Key difference:** Remove or disable GitHub Copilot -- it conflicts with Windsurf's Supercomplete.

### Step 3: Migrate from Cursor

Cursor and Windsurf both extend VS Code but have different AI config files:

```yaml
# Mapping Cursor concepts to Windsurf:
cursor_to_windsurf:
  .cursorrules:       .windsurfrules     # AI context rules
  .cursorignore:      .codeiumignore     # AI indexing exclusions
  .cursor/rules/:     .windsurf/rules/   # Workspace rules
  cursor_settings:    windsurf_settings  # IDE preferences
  Composer:           Cascade            # Agentic AI assistant
  Tab:                Supercomplete      # Inline completions
  Cmd+K:              Cmd+I              # Inline editing
  Cmd+L:              Cmd+L              # AI chat (same!)
```

**Migration script:**
```bash
#!/bin/bash
set -euo pipefail
echo "Migrating Cursor config to Windsurf..."

# Convert .cursorrules to .windsurfrules
[ -f .cursorrules ] && cp .cursorrules .windsurfrules && echo "Copied .cursorrules → .windsurfrules"

# Convert .cursorignore to .codeiumignore
[ -f .cursorignore ] && cp .cursorignore .codeiumignore && echo "Copied .cursorignore → .codeiumignore"

# Migrate workspace rules
if [ -d .cursor/rules ]; then
  mkdir -p .windsurf/rules
  cp .cursor/rules/*.md .windsurf/rules/ 2>/dev/null
  echo "Copied workspace rules to .windsurf/rules/"
  echo "NOTE: Check frontmatter -- Windsurf uses 'trigger:' field, Cursor uses different format"
fi

echo "Migration complete. Review .windsurfrules for Cursor-specific references."
```

### Step 4: Add Windsurf-Specific Configuration

After migration, add Windsurf-exclusive features:

```markdown
<!-- New Windsurf features not in VS Code or Cursor -->

1. Cascade Workflows (.windsurf/workflows/*.md)
   - Reusable multi-step automation via slash commands
   - No equivalent in VS Code or Cursor

2. Cascade Memories
   - Persistent facts across sessions
   - Partial equivalent: Cursor notepad

3. Turbo Mode
   - Auto-execute terminal commands
   - Cursor has "auto-run" but different config

4. Browser Previews
   - In-IDE preview with element selection
   - Send UI elements to Cascade for editing

5. Workspace Rules with Trigger Modes
   - glob, always_on, manual, model_decision
   - More granular than Cursor's rule system
```

### Step 5: Post-Upgrade Validation

```bash
set -euo pipefail
echo "=== Windsurf Post-Upgrade Check ==="
echo "Version: $(windsurf --version)"
echo "Extensions: $(windsurf --list-extensions | wc -l) installed"
echo "Rules: $([ -f .windsurfrules ] && wc -c < .windsurfrules || echo 'none') bytes"
echo "Ignore: $([ -f .codeiumignore ] && wc -l < .codeiumignore || echo 'none') patterns"

# Test AI features
echo ""
echo "Manual checks:"
echo "1. Open a code file -- Supercomplete should show ghost text"
echo "2. Press Cmd/Ctrl+L -- Cascade should open and respond"
echo "3. Press Cmd/Ctrl+I -- Command mode should activate"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Extensions not loading | Incompatible with Windsurf | Check Windsurf marketplace for alternative |
| Settings not applied | Wrong config directory | Verify OS-specific settings path |
| .cursorrules not working | Wrong filename | Rename to `.windsurfrules` |
| Keyboard shortcuts different | Windsurf overrides some defaults | Check Keyboard Shortcuts editor |
| Copilot still active | Not disabled | Extensions > search "copilot" > Disable |

## Examples

### Backup Before Upgrade
```bash
# Backup current Windsurf config
tar -czf windsurf-config-backup-$(date +%Y%m%d).tar.gz \
  ~/.config/Windsurf/User/ \
  ~/.codeium/ \
  .windsurfrules \
  .codeiumignore \
  .windsurf/ 2>/dev/null
```

### Check Windsurf Changelog
```
Visit: https://windsurf.com/changelog
Look for: breaking changes, deprecated settings, new features
```

## Resources
- [Windsurf Changelog](https://windsurf.com/changelog)
- [Windsurf Download](https://windsurf.com/download)
- [Migrating from Cursor](https://docs.windsurf.com)

## Next Steps
For CI integration, see `windsurf-ci-integration`.
