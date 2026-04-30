---
name: apple-notes-incident-runbook
description: 'Incident response runbook for Apple Notes automation failures.

  Trigger: "apple notes incident".

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
# Apple Notes Incident Runbook

## Overview

This runbook covers the most common Apple Notes automation failures and their resolution procedures. Unlike cloud SaaS incidents that involve API endpoints and status pages, Apple Notes incidents are local to the macOS machine: app crashes, TCC permission revocations, iCloud sync failures, and database corruption. Each incident section follows a detect-diagnose-fix-verify structure. Keep this runbook accessible on any machine running Notes automation.

## Severity Levels

| Severity | Description | Example | Response Time |
|----------|-------------|---------|---------------|
| P1 | All automation blocked | TCC permissions revoked, Notes.app won't launch | Immediate |
| P2 | Data inconsistency | iCloud sync stuck, notes missing | Within 1 hour |
| P3 | Degraded performance | Slow operations, intermittent timeouts | Within 4 hours |
| P4 | Cosmetic/minor | Log warnings, non-critical script errors | Next business day |

## Incident 1: Notes.app Crash During Automation

```bash
# DETECT: Check if Notes is running
pgrep -x Notes > /dev/null && echo "Notes: running" || echo "Notes: NOT RUNNING"

# DIAGNOSE: Check crash logs
ls -lt ~/Library/Logs/DiagnosticReports/Notes* 2>/dev/null | head -3

# FIX: Restart Notes with stabilization delay
killall Notes 2>/dev/null
sleep 3
open -a Notes
sleep 5  # Wait for full launch and iCloud handshake

# VERIFY: Confirm access is restored
osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length'
```

## Incident 2: iCloud Sync Stuck

```bash
# DETECT: Compare note count with expected (from last known good)
CURRENT=$(osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length' 2>/dev/null)
echo "Current note count: ${CURRENT:-ERROR}"

# DIAGNOSE: Check iCloud daemons
ps aux | grep -E "(bird|cloudd|nsurlsessiond)" | grep -v grep

# Check sync status
brctl status com.apple.Notes 2>/dev/null || echo "brctl unavailable"
log show --predicate 'subsystem == "com.apple.notes"' --last 5m 2>/dev/null | tail -20

# FIX: Restart iCloud sync daemons
killall bird 2>/dev/null; killall cloudd 2>/dev/null
sleep 10  # Allow daemons to restart and reconnect

# VERIFY: Check note count is increasing / stable
sleep 30
NEW_COUNT=$(osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length' 2>/dev/null)
echo "Note count after sync restart: ${NEW_COUNT:-ERROR}"
```

## Incident 3: TCC Permissions Revoked

```bash
# DETECT: Test Apple Events access
osascript -l JavaScript -e 'Application("Notes").name()' 2>&1 | grep -q "Not authorized" && echo "TCC: DENIED" || echo "TCC: OK"

# DIAGNOSE: Check TCC database (may require Full Disk Access)
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT client, allowed FROM access WHERE service='kTCCServiceAppleEvents';" 2>/dev/null

# FIX: Reset and re-prompt
tccutil reset AppleEvents
# Run a simple command to trigger the permission dialog
osascript -l JavaScript -e 'Application("Notes").name()'
# User must click "Allow" in the system dialog

# VERIFY
osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length'
```

## Incident 4: Notes Database Corruption

```bash
# DETECT: Notes.app launches but shows no notes or crashes on open
# DIAGNOSE: Check database integrity
NOTES_DB="$HOME/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"
sqlite3 "$NOTES_DB" "PRAGMA integrity_check;" 2>/dev/null || echo "Cannot access DB (sandboxed)"

# FIX: Force re-download from iCloud
# 1. Quit Notes
killall Notes 2>/dev/null
# 2. Rename local database (iCloud will re-download)
mv "$HOME/Library/Group Containers/group.com.apple.notes" \
   "$HOME/Library/Group Containers/group.com.apple.notes.backup.$(date +%s)" 2>/dev/null
# 3. Relaunch Notes — it will rebuild from iCloud
open -a Notes
# WARNING: "On My Mac" notes are NOT in iCloud and will be lost. Back up first.
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Crash loop after restart | Corrupt note triggering crash on load | Remove local DB; let iCloud rebuild |
| Sync stuck for >1 hour | Apple iCloud service outage | Check apple.com/systemstatus; wait for resolution |
| Permissions reset after macOS update | OS upgrade resets TCC database | Re-approve automation permissions post-update |
| Script hangs indefinitely | Notes.app showing modal dialog | Dismiss dialog manually; add `activate()` before operations |
| Automation works for user A but not B | Per-user TCC grants | Each macOS user must approve automation separately |

## Resources

- [Apple System Status](https://www.apple.com/support/systemstatus/)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [macOS Unified Logging](https://developer.apple.com/documentation/os/logging)

## Next Steps

For root cause analysis of specific errors, see `apple-notes-common-errors`. For monitoring to detect incidents early, see `apple-notes-observability`.
