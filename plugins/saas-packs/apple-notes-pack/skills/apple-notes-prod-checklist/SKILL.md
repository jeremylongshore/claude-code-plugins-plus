---
name: apple-notes-prod-checklist
description: |
  Production checklist for Apple Notes automation deployments.
  Trigger: "apple notes production checklist".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Production Checklist

## Overview

Before deploying Apple Notes automation to a production macOS machine, validate every dependency: TCC permissions, iCloud sync health, Notes.app availability, error handling robustness, and data security. Unlike cloud services where deployment is a push, Apple Notes automation requires physical or remote access to a Mac with a logged-in user session. This checklist ensures nothing is missed before going live.

## Pre-Deployment Checklist

### Permissions and Access
- [ ] TCC automation permission granted (System Settings > Privacy > Automation)
- [ ] Permission tested from the exact context that will run in production (Terminal, launchd, etc.)
- [ ] Full Disk Access granted if reading Notes database directly (not recommended)
- [ ] Script runs without interactive prompts (no "Allow" dialogs left)

### Application Configuration
- [ ] Notes.app configured to launch at login (System Settings > General > Login Items)
- [ ] Target Apple ID / iCloud account signed in and syncing
- [ ] "On My Mac" account enabled if local storage is needed
- [ ] Correct default account set for automation scripts

### Data and Sync
- [ ] iCloud sync verified working (create note on Mac, verify on iPhone)
- [ ] Backup strategy documented (JSON export on schedule)
- [ ] Exported data files have restricted permissions (`chmod 600`)
- [ ] No sensitive data written to logs or temp files

### Reliability
- [ ] Error handling for all AppleEvent failure codes (-1743, -1712, -609, -1728)
- [ ] Retry logic with exponential backoff for transient failures
- [ ] Write operations throttled (max 1 per second for iCloud sync)
- [ ] Health check script deployed and running on schedule
- [ ] Alerting configured for automation failures (macOS notification or webhook)

### Compatibility
- [ ] Script tested on target macOS version (`sw_vers`)
- [ ] JXA API compatibility verified for target OS (Ventura/Sonoma/Sequoia)
- [ ] Node.js version matches production (if using child_process for osascript)

## Validation Script

```bash
#!/bin/bash
echo "=== Apple Notes Production Readiness ==="
PASS=0; FAIL=0; WARN=0

check() {
  local label=$1 result=$2
  if [ "$result" = "PASS" ]; then echo "[PASS] $label"; PASS=$((PASS+1))
  elif [ "$result" = "WARN" ]; then echo "[WARN] $label"; WARN=$((WARN+1))
  else echo "[FAIL] $label"; FAIL=$((FAIL+1)); fi
}

# macOS version
VER=$(sw_vers -productVersion)
check "macOS version ($VER)" "$(echo "$VER" | grep -qE '^1[3-9]|^[2-9]' && echo PASS || echo WARN)"

# Notes.app running
check "Notes.app running" "$(pgrep -x Notes > /dev/null && echo PASS || echo FAIL)"

# JXA access
NOTE_COUNT=$(osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length' 2>/dev/null)
check "JXA access (${NOTE_COUNT:-0} notes)" "$([ -n "$NOTE_COUNT" ] && echo PASS || echo FAIL)"

# iCloud sync daemon
check "iCloud sync daemon (bird)" "$(pgrep -x bird > /dev/null && echo PASS || echo WARN)"

# Write test (create and delete a test note)
TEST_ID=$(osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const n = Notes.Note({name: "__prod_check_" + Date.now(), body: "test"});
  Notes.defaultAccount.folders[0].notes.push(n);
  n.id();
' 2>/dev/null)
check "Write permission test" "$([ -n "$TEST_ID" ] && echo PASS || echo FAIL)"
# Clean up test note
[ -n "$TEST_ID" ] && osascript -l JavaScript -e "Application('Notes').notes.byId('$TEST_ID').delete()" 2>/dev/null

echo ""
echo "=== Results: $PASS passed, $WARN warnings, $FAIL failed ==="
[ "$FAIL" -gt 0 ] && echo "BLOCKED: Fix failures before deploying" && exit 1
[ "$WARN" -gt 0 ] && echo "READY with warnings" && exit 0
echo "READY for production" && exit 0
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Validation passes locally, fails on target Mac | Different macOS version or Apple ID | Run validation script on the exact production machine |
| Write test fails | Account is read-only (Gmail IMAP) | Switch to iCloud or "On My Mac" account |
| Notes.app not at login items | Removed after macOS update | Re-add via System Settings > General > Login Items |
| Health check does not alert | Notification permissions denied for Terminal | Grant notification permission in System Settings |
| iCloud sync lag in production | Large attachment uploads | Monitor with `brctl status`; set expectations for sync delay |

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [macOS Login Items](https://support.apple.com/guide/mac-help/open-items-automatically-when-you-log-in-mh15189/mac)
- [Apple System Status](https://www.apple.com/support/systemstatus/)

## Next Steps

For deploying as a launchd service, see `apple-notes-deploy-integration`. For ongoing monitoring, see `apple-notes-observability`.
