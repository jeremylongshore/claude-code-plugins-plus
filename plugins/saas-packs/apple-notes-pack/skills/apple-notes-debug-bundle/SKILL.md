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

## Overview

This debug bundle collects diagnostic information from Apple Notes automation integrations
for troubleshooting AppleScript and JXA (JavaScript for Automation) workflows. It captures
macOS version compatibility, Notes.app account configuration, folder and note counts,
TCC (Transparency, Consent, and Control) permission status, and Shortcuts automation
entitlements. The resulting tarball helps diagnose permission denials, sandbox restrictions,
iCloud sync failures, and scripting bridge errors that commonly block Notes automation.

## Prerequisites

- macOS 12+ with Notes.app configured
- `osascript`, `tar` available (built into macOS)
- Terminal granted Automation permission for Notes.app in System Preferences > Privacy & Security

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-apple-notes-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Environment ===" > "$BUNDLE/environment.txt"
echo "macOS: $(sw_vers -productVersion 2>/dev/null || echo 'not macOS')" >> "$BUNDLE/environment.txt"
echo "Notes.app running: $(pgrep -x Notes > /dev/null && echo Yes || echo No)" >> "$BUNDLE/environment.txt"
echo "Shell: $SHELL ($TERM)" >> "$BUNDLE/environment.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/environment.txt"

# Automation permissions (TCC database)
echo "=== TCC Permissions ===" > "$BUNDLE/tcc-status.txt"
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT client, auth_value, auth_reason FROM access WHERE service='kTCCServiceAppleEvents'" \
  >> "$BUNDLE/tcc-status.txt" 2>/dev/null || echo "Cannot read TCC database (SIP may block)" >> "$BUNDLE/tcc-status.txt"

# Account enumeration via JXA
echo "=== Accounts ===" > "$BUNDLE/accounts.txt"
osascript -l JavaScript -e '
  const app = Application("Notes");
  const accts = app.accounts();
  accts.forEach(a => {
    const notes = a.notes().length;
    const folders = a.folders().length;
    ObjC.import("stdlib"); // ensure stdio
    $.system(`echo "${a.name()}: ${notes} notes, ${folders} folders" >> /dev/stdout`);
  });
' >> "$BUNDLE/accounts.txt" 2>&1 || echo "JXA account query failed" >> "$BUNDLE/accounts.txt"

# Note count and folder structure
echo "=== Folder Structure ===" > "$BUNDLE/folders.txt"
osascript -l JavaScript -e '
  const app = Application("Notes");
  app.defaultAccount.folders().forEach(f => {
    $.system(`echo "  ${f.name()}: ${f.notes().length} notes" >> /dev/stdout`);
  });
' >> "$BUNDLE/folders.txt" 2>&1 || echo "Folder query failed" >> "$BUNDLE/folders.txt"

# Shortcuts integration check
echo "=== Shortcuts ===" > "$BUNDLE/shortcuts.txt"
shortcuts list 2>/dev/null | grep -i note >> "$BUNDLE/shortcuts.txt" || echo "No note-related Shortcuts found" >> "$BUNDLE/shortcuts.txt"

# iCloud sync status
echo "=== iCloud Sync ===" > "$BUNDLE/icloud-sync.txt"
brctl status com.apple.Notes 2>/dev/null >> "$BUNDLE/icloud-sync.txt" || echo "brctl not available or Notes not using iCloud Drive" >> "$BUNDLE/icloud-sync.txt"
ls -la ~/Library/Group\ Containers/group.com.apple.notes/ >> "$BUNDLE/icloud-sync.txt" 2>/dev/null || echo "Notes container not found" >> "$BUNDLE/icloud-sync.txt"

# Recent console errors
echo "=== Recent Errors ===" > "$BUNDLE/console-errors.txt"
log show --predicate 'subsystem == "com.apple.notes"' --last 30m --style compact 2>/dev/null \
  | tail -50 >> "$BUNDLE/console-errors.txt" || echo "Cannot read system log" >> "$BUNDLE/console-errors.txt"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-apple-notes-*.tar.gz
cat debug-apple-notes-*/environment.txt     # Confirm macOS version
cat debug-apple-notes-*/tcc-status.txt      # Check automation permissions
cat debug-apple-notes-*/accounts.txt        # Verify note counts per account
cat debug-apple-notes-*/console-errors.txt  # Look for sandbox or sync errors
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| `-1743` error (not permitted) | `tcc-status.txt` shows no entry for Terminal | Grant Automation permission: System Settings > Privacy > Automation > Terminal > Notes |
| JXA returns empty arrays | `accounts.txt` shows 0 notes | Notes.app must be open at least once; launch Notes and wait for iCloud sync |
| `execution error: Notes got an error: AppleEvent timed out` | `console-errors.txt` shows timeout | Notes.app is busy syncing; wait for iCloud sync to finish, then retry |
| Folder query fails on shared accounts | `folders.txt` shows error on non-default account | Specify account explicitly: `app.accounts.byName("iCloud")` |
| Shortcuts integration returns empty | `shortcuts.txt` shows no matches | Create a Notes shortcut manually in Shortcuts.app, then re-run |
| `brctl` reports conflict | `icloud-sync.txt` shows conflict state | Open Notes.app, resolve duplicate notes, then force sync via iCloud preferences |

## Automated Health Check

```typescript
import { execSync } from "child_process";

function checkAppleNotesHealth(): {
  status: string;
  macosVersion: string;
  notesRunning: boolean;
  accountCount: number;
  tccGranted: boolean;
} {
  const macosVersion = execSync("sw_vers -productVersion").toString().trim();
  const notesRunning = execSync("pgrep -x Notes || true").toString().trim() !== "";
  let accountCount = 0;
  try {
    const raw = execSync(
      'osascript -l JavaScript -e \'Application("Notes").accounts().length\''
    ).toString().trim();
    accountCount = parseInt(raw, 10);
  } catch { /* Notes not accessible */ }
  const tccGranted = accountCount > 0;
  return {
    status: tccGranted && notesRunning ? "healthy" : "degraded",
    macosVersion,
    notesRunning,
    accountCount,
    tccGranted,
  };
}
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Cookbook](https://github.com/JXA-Cookbook/JXA-Cookbook)
- [Apple Developer — NSAppleScript](https://developer.apple.com/documentation/foundation/nsapplescript)

## Next Steps

See `apple-notes-rate-limits`.
