---
name: apple-notes-incident-runbook
description: 'Incident response runbook for Apple Notes automation failures.

  Trigger: "apple notes incident".

  '
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.6.0
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

## Prerequisites

- A named incident owner, an approved maintenance window for recovery actions, and a verified backup status.
- A redacted diagnostic location with restricted access; notes, account names, and raw unified logs can contain sensitive data.
- A documented escalation route to Apple or device management for sync, TCC, and storage failures.

## Instructions

1. Stop automated writes first and preserve the last successful cursor or operation ledger.
2. Collect minimal, redacted diagnostics and classify the incident before restarting applications or services.
3. Use supported UI, MDM, or vendor recovery paths for permissions, iCloud, and storage; do not modify TCC or Notes databases directly.
4. Validate recovery with a scoped read-only check, reconcile pending mutations, and obtain owner approval before resuming writes.

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

# FIX: Pause automation, inspect Apple System Status, and follow supported
# macOS/iCloud recovery guidance. Do not terminate iCloud daemons in a runbook.

# VERIFY: Check note count is increasing / stable
sleep 30
NEW_COUNT=$(osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length' 2>/dev/null)
echo "Note count after sync restart: ${NEW_COUNT:-ERROR}"
```

## Incident 3: TCC Permissions Revoked

```bash
# DETECT: Test Apple Events access
osascript -l JavaScript -e 'Application("Notes").name()' 2>&1 | grep -q "Not authorized" && echo "TCC: DENIED" || echo "TCC: OK"

# DIAGNOSE/FIX: Review the exact client in System Settings > Privacy & Security
# > Automation, or use an approved MDM profile. Do not reset system-wide consent.

# VERIFY
osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length'
```

## Incident 4: Notes Database Corruption

```bash
# DETECT: Notes.app launches but shows no scoped notes or crashes on open.
# Preserve the error timestamp and stop automation writes.
# DIAGNOSE/FIX: Do not inspect, move, rename, or rebuild NoteStore files.
# Escalate with the owner to supported Apple/device-management recovery after
# confirming backup status, especially where "On My Mac" notes are in scope.
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Crash loop after restart | Corrupt note triggering crash on load | Remove local DB; let iCloud rebuild |
| Sync stuck for >1 hour | Apple iCloud service outage | Check apple.com/systemstatus; wait for resolution |
| Permissions reset after macOS update | OS upgrade resets TCC database | Re-approve automation permissions post-update |
| Script hangs indefinitely | Notes.app showing modal dialog | Dismiss dialog manually; add `activate()` before operations |
| Automation works for user A but not B | Per-user TCC grants | Each macOS user must approve automation separately |

## Output

An incident record contains severity, time window, affected automation scope, redacted diagnostics, actions taken, reconciliation status, and the approval to resume. It must not contain note bodies, database copies, or unredacted account/folder names.

## Examples

For a suspected sync incident, pause writes, capture the job error and a redacted system-status check, then wait for the approved recovery path. If data divergence remains, keep the automation stopped and escalate rather than renaming local Notes storage or forcing a re-download.

## Resources

- [Apple System Status](https://www.apple.com/support/systemstatus/)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [macOS Unified Logging](https://developer.apple.com/documentation/os/logging)

## Next Steps

For root cause analysis of specific errors, see `apple-notes-common-errors`. For monitoring to detect incidents early, see `apple-notes-observability`.
