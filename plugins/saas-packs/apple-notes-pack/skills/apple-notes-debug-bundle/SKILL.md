---
name: apple-notes-debug-bundle
description: |
  Collect Apple Notes automation debug evidence for troubleshooting.
  Trigger: "apple notes debug".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Debug Bundle

## Diagnostic Script
```bash
#!/bin/bash
echo "=== Apple Notes Debug Bundle $(date -Iseconds) ==="
echo "macOS: $(sw_vers -productVersion)"
echo "Notes.app running: $(pgrep -x Notes > /dev/null && echo Yes || echo No)"
echo "Accounts: $(osascript -l JavaScript -e "Application(\"Notes\").accounts().map(a => a.name()).join(\", \")" 2>/dev/null || echo "ERROR")"
echo "Note count: $(osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.notes.length" 2>/dev/null || echo "ERROR")"
echo "Folder count: $(osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.folders.length" 2>/dev/null || echo "ERROR")"
echo "TCC status: $(sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db "SELECT client,allowed FROM access WHERE service='kTCCServiceAppleEvents'" 2>/dev/null || echo "Cannot read TCC")"
echo "=== Done ==="
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
