---
name: apple-notes-incident-runbook
description: |
  Incident response runbook for Apple Notes automation failures.
  Trigger: "apple notes incident".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Incident Runbook

## Common Incidents

### Notes.app Crash During Automation
```bash
# 1. Check if Notes is running
pgrep -x Notes || echo "Notes not running"

# 2. Restart Notes
killall Notes 2>/dev/null; sleep 2; open -a Notes; sleep 3

# 3. Verify access
osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.notes.length"

# 4. Resume automation
```

### iCloud Sync Stuck
```bash
# Check iCloud status
defaults read MobileMeAccounts
# Force sync
killall bird; sleep 5; killall cloudd; sleep 5

# Verify notes are syncing
osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.notes.length"
```

### Permissions Revoked
```bash
# Reset automation permissions
tccutil reset AppleEvents
# Re-run script to trigger permission prompt
osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.notes.length"
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
