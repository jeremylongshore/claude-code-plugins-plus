---
name: apple-notes-deploy-integration
description: 'Deploy Apple Notes automation as a local macOS service.

  Trigger: "apple notes deploy".

  '
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- macos
- apple-notes
- automation
compatibility: Designed for Claude Code
---
# Apple Notes Deploy Integration

## Overview

Apple Notes automation runs exclusively on macOS — there is no cloud deployment path because Notes.app depends on the local Apple Events subsystem and TCC permissions. Deployment means packaging your JXA/osascript automation as a persistent local service. The three deployment models are: launchd agents for scheduled/recurring tasks, Automator workflows for user-triggered actions, and Apple Shortcuts for cross-app automation. Each has different permission requirements and lifecycle management.

## launchd Agent (Recommended for Background Tasks)

```xml
<!-- ~/Library/LaunchAgents/com.yourorg.notes-automation.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yourorg.notes-automation</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/node</string>
        <string>/Users/you/scripts/notes-sync.js</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>StandardOutPath</key>
    <string>/tmp/notes-automation.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/notes-automation-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

```bash
# Deploy and manage the launchd agent
cp com.yourorg.notes-automation.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.yourorg.notes-automation.plist
launchctl list | grep notes-automation
# View logs
tail -f /tmp/notes-automation.log

# Unload for updates
launchctl unload ~/Library/LaunchAgents/com.yourorg.notes-automation.plist
```

## Shortcuts Deployment (User-Triggered)

```bash
# Create a Shortcut that runs your JXA script
# 1. Open Shortcuts.app > New Shortcut
# 2. Add "Run Shell Script" action with:
osascript -l JavaScript /Users/you/scripts/notes-export.js

# Trigger shortcuts from CLI or other automations:
shortcuts run "Export Notes to Markdown"
shortcuts run "Daily Note Creator" --input-type text --input "$(date +%Y-%m-%d)"

# List available shortcuts
shortcuts list | grep -i note
```

## Installer Script

```bash
#!/bin/bash
# scripts/install.sh — Deploy Notes automation to a macOS machine
set -euo pipefail

INSTALL_DIR="$HOME/.notes-automation"
PLIST_DIR="$HOME/Library/LaunchAgents"
LABEL="com.yourorg.notes-automation"

echo "Installing Apple Notes automation..."
mkdir -p "$INSTALL_DIR"
cp scripts/*.js "$INSTALL_DIR/"
cp config/*.json "$INSTALL_DIR/"

# Install launchd plist
envsubst < templates/launchd.plist.template > "$PLIST_DIR/$LABEL.plist"
launchctl load "$PLIST_DIR/$LABEL.plist"

# Verify
echo -n "Service status: "
launchctl list "$LABEL" 2>/dev/null && echo "Running" || echo "Failed to start"

# Test Notes access (will trigger TCC prompt on first run)
echo -n "Notes access: "
osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length' && echo "OK" || echo "DENIED — approve in System Settings"
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| launchd job starts but osascript fails | TCC not granted for launchd context | Run script manually first to trigger TCC prompt; approve in System Settings |
| Job runs but Notes.app not open | `RunAtLoad` fires before login complete | Add `open -a Notes` before osascript calls in your script |
| Logs show "connection invalid" | Screen locked or user switched | Add `LimitLoadToSessionType: Aqua` to plist for GUI session only |
| Shortcut not found from CLI | Shortcut name mismatch or not saved | `shortcuts list` to verify exact name |
| Agent runs twice | Both `StartInterval` and `StartCalendarInterval` set | Use only one scheduling mechanism per plist |

## Resources

- [launchd.plist man page](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [Apple Shortcuts User Guide](https://support.apple.com/guide/shortcuts-mac/intro-to-shortcuts-apdf22b0444c/mac)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)

## Next Steps

For production readiness validation, see `apple-notes-prod-checklist`. For monitoring deployed services, see `apple-notes-observability`.
