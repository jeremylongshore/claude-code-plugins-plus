---
name: apple-notes-deploy-integration
description: |
  Deploy Apple Notes automation as a local macOS service.
  Trigger: "apple notes deploy".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Deploy Integration

## Overview
Apple Notes automation runs locally on macOS only — no cloud deployment possible. Deploy as a launchd service or Automator workflow.

## launchd Service
```xml
<!-- ~/Library/LaunchAgents/com.yourorg.notes-automation.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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
</dict>
</plist>
```

```bash
# Load the service
launchctl load ~/Library/LaunchAgents/com.yourorg.notes-automation.plist
# Check status
launchctl list | grep notes
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
