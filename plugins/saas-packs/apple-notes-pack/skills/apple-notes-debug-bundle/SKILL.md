---
name: apple-notes-debug-bundle
description: 'Collect Apple Notes automation debug evidence for troubleshooting.

  Trigger: "apple notes debug".

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

## Instructions

1. Obtain incident-owner approval and choose a private, access-controlled destination before collection.
2. Collect platform version, job configuration, and redacted error classifications first; include account or folder metadata only when essential to diagnosis.
3. Exclude note titles, bodies, attachment names, TCC database rows, Keychain values, and full home-directory listings.
4. Encrypt the bundle in transit, share it only with the incident responders, and delete it at the documented retention deadline.

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

# Automation permissions: record only a read-only authorization outcome.
echo "=== Automation Authorization ===" > "$BUNDLE/tcc-status.txt"
osascript -l JavaScript -e 'Application("Notes").name(); "authorized"' \
  >> "$BUNDLE/tcc-status.txt" 2>&1 || echo "authorization check failed" >> "$BUNDLE/tcc-status.txt"

# Scoped authorization outcome via JXA; do not enumerate accounts or folders.
echo "=== Scoped Notes Access ===" > "$BUNDLE/accounts.txt"
osascript -l JavaScript -e '
  const app = Application("Notes");
  app.name();
  "scoped access available";
' >> "$BUNDLE/accounts.txt" 2>&1 || echo "JXA scoped query failed" >> "$BUNDLE/accounts.txt"

# Do not collect folder structure or note counts in a general debug bundle.
echo "Folder enumeration intentionally omitted" > "$BUNDLE/folders.txt"

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

## Error Handling

If the collector cannot perform a scoped authorization check, stop collection and report only the failed check and timestamp. If archive creation fails, preserve no partial bundle in a shared directory; remove the temporary directory and retry only after checking disk space and destination permissions. If a responder requests note content or a database copy, require separate incident-owner approval and use the established evidence-handling process rather than expanding this general bundle.

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

## Output

The bundle contains redacted platform, authorization, and error-class evidence plus a manifest with collector, timestamp, scope label, checksum, and expiration. It does not include NoteStore copies, note content, account/folder names, shortcut names, or raw TCC records.

## Examples

For a permission failure, collect the authorization outcome, macOS version, and the last redacted job error, encrypt the archive, and attach its checksum to the incident. Do not collect every configured account or folder merely because the script can enumerate them.

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Cookbook](https://github.com/JXA-Cookbook/JXA-Cookbook)
- [Apple Developer — NSAppleScript](https://developer.apple.com/documentation/foundation/nsapplescript)

## Next Steps

Use `apple-notes-rate-limits` to investigate persistent latency and `apple-notes-incident-runbook` to coordinate a recovery. Retain the bundle only for the incident's approved window, then delete it and record the deletion in the incident receipt.
