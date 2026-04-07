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

## Overview

Apple Notes automation errors fall into three categories: TCC permission denials from macOS security, AppleEvent communication failures between your script and Notes.app, and iCloud sync issues that cause data inconsistency. Unlike REST APIs that return HTTP status codes, Apple Events use negative OSStatus codes. This guide covers every error you are likely to encounter when automating Notes via JXA or `osascript`, with tested fixes for each.

## Error Reference

| Error | Code | Root Cause | Fix |
|-------|------|-----------|-----|
| Not authorized to send Apple events | -1743 | TCC denied automation permission | System Settings > Privacy > Automation > enable your app |
| AppleEvent timed out | -1712 | Notes.app busy, hung, or not running | `Application("Notes").activate()`; increase timeout with `delay` |
| Can't get application "Notes" | -2700 | Notes.app not installed or renamed | Verify with `mdfind "kMDItemCFBundleIdentifier == com.apple.Notes"` |
| Can't get folder | -1728 | Folder name mismatch (case-sensitive) | List folders first: `Notes.defaultAccount.folders().map(f => f.name())` |
| Connection is invalid | -609 | Notes.app crashed mid-operation | `killall Notes; sleep 2; open -a Notes; sleep 3` |
| User canceled | -128 | Security dialog dismissed or timed out | Re-run and click Allow; or pre-grant via MDM profile |
| Can't make Note | -10000 | Invalid HTML in note body | Validate HTML; strip unsupported tags before creating |
| Application isn't running | -600 | App quit between calls | Wrap in retry with `Application("Notes").activate()` first |

## Diagnostic Script

```bash
#!/bin/bash
echo "=== Apple Notes Diagnostics ==="
echo -n "macOS version: "; sw_vers -productVersion
echo -n "Notes.app running: "; pgrep -x Notes > /dev/null && echo "Yes" || echo "No"
echo -n "Notes.app path: "; mdfind "kMDItemCFBundleIdentifier == com.apple.Notes" 2>/dev/null | head -1
echo -n "Note count: "
osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length' 2>/dev/null || echo "ERROR — check TCC"
echo -n "Folder count: "
osascript -l JavaScript -e 'Application("Notes").defaultAccount.folders.length' 2>/dev/null || echo "ERROR"
echo -n "Accounts: "
osascript -l JavaScript -e 'Application("Notes").accounts().map(a => a.name()).join(", ")' 2>/dev/null || echo "ERROR"
echo -n "iCloud status: "
defaults read MobileMeAccounts Accounts 2>/dev/null | grep -c AccountID || echo "No iCloud"
echo "=== TCC Automation Entries ==="
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT client, allowed FROM access WHERE service='kTCCServiceAppleEvents';" 2>/dev/null || echo "Cannot read TCC.db (SIP)"
echo "=== Done ==="
```

## Common Fixes

```bash
# Reset TCC automation permissions (triggers fresh prompts)
tccutil reset AppleEvents

# Force quit and restart Notes with delay for launch
killall Notes 2>/dev/null; sleep 2; open -a Notes; sleep 3

# Verify Notes is responsive after restart
osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length'

# Force iCloud sync restart
killall bird 2>/dev/null; killall cloudd 2>/dev/null; sleep 5

# Check for stuck iCloud sync
brctl status com.apple.Notes 2>/dev/null || echo "brctl not available"
```

## Retry Wrapper for Transient Failures

```javascript
// Retry pattern for -609, -600, -1712 errors
function withRetry(fn, maxAttempts = 3) {
  for (let i = 0; i < maxAttempts; i++) {
    try { return fn(); }
    catch (e) {
      if (i === maxAttempts - 1) throw e;
      Application("Notes").activate();
      delay(2);
    }
  }
}

// Usage
const count = withRetry(() => Application("Notes").defaultAccount.notes.length);
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Errors persist after TCC reset | App-specific permission cached | Restart Terminal/IDE after `tccutil reset` |
| iCloud notes show stale data | Sync daemon paused | `killall bird && killall cloudd` to force resync |
| Sandbox prevents database read | SIP protects TCC.db | Use `osascript` to test access instead of direct DB query |
| Script works manually, fails from cron | Cron has no TCC context | Use launchd with `AssociatedBundleIdentifiers` instead |

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [Apple TCC Overview](https://support.apple.com/guide/security/controlling-app-access-to-files-secddd1d86a6/web)
- [OSStatus Error Codes](https://www.osstatus.com/)

## Next Steps

For incident response when errors cascade, see `apple-notes-incident-runbook`. For TCC and security hardening, see `apple-notes-security-basics`.
