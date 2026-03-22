---
name: apple-notes-common-errors
description: |
  Diagnose and fix common Apple Notes automation errors.
  Trigger: "apple notes error".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Common Errors

## Error Reference

| Error | Code | Root Cause | Fix |
|-------|------|-----------|-----|
| Not authorized to send Apple events | -1743 | Missing automation permission | System Preferences > Privacy > Automation |
| AppleEvent timed out | -1712 | Notes.app busy or not running | Activate Notes first; increase timeout |
| Notes is not running | N/A | App closed | Add `Application("Notes").activate()` |
| Can't get folder | -1728 | Folder name mismatch | Check exact folder name including case |
| Connection is invalid | -609 | Notes crashed during operation | Restart Notes.app |
| User canceled | -128 | Security dialog dismissed | Re-run and click Allow |

## Diagnostic Script
```bash
#!/bin/bash
echo "=== Apple Notes Diagnostics ==="
echo -n "Notes.app running: "
pgrep -x Notes > /dev/null && echo "Yes" || echo "No"
echo -n "Note count: "
osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.notes.length" 2>/dev/null || echo "ERROR"
echo -n "Folder count: "
osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.folders.length" 2>/dev/null || echo "ERROR"
echo -n "Accounts: "
osascript -l JavaScript -e "Application(\"Notes\").accounts().map(a => a.name()).join(\", \")" 2>/dev/null || echo "ERROR"
echo "=== Done ==="
```

## Common Fixes
```bash
# Reset TCC permissions (if automation denied)
tccutil reset AppleEvents

# Force quit and restart Notes
killall Notes; sleep 2; open -a Notes

# Check iCloud sync status
defaults read com.apple.Notes
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
