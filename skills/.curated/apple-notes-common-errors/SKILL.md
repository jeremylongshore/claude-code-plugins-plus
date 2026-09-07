---
name: apple-notes-common-errors
description: 'Diagnose and fix common Apple Notes automation errors.

  Trigger: "apple notes error".

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
# Apple Notes Common Errors

## Overview

Apple Notes automation errors fall into three categories: TCC permission denials from macOS security, AppleEvent communication failures between your script and Notes.app, and iCloud sync issues that cause data inconsistency. Unlike REST APIs that return HTTP status codes, Apple Events use negative OSStatus codes. This guide covers every error you are likely to encounter when automating Notes via JXA or `osascript`, with tested fixes for each.

## Prerequisites

- The failed job's timestamp, opaque operation identifier, and a scoped read-only authorization test.
- A defined owner for TCC consent and device recovery; error handling must not change system-wide privacy settings.
- A paused write queue for incidents that may have partially completed a mutation.

## Instructions

1. Identify whether the failure is authorization, application availability, or synchronization before retrying.
2. Capture only a redacted error classification and operation identifier; avoid dumping accounts, folders, or note content.
3. Re-run a bounded read-only check after a supported UI or MDM recovery action.
4. Reconcile a timed-out write against the operation ledger before retrying, then resume the queue only after owner approval.

## Error Reference

| Error | Code | Root Cause | Fix |
|-------|------|-----------|-----|
| Not authorized to send Apple events | -1743 | TCC denied automation permission | System Settings > Privacy > Automation > enable your app |
| AppleEvent timed out | -1712 | Notes.app busy, hung, or not running | `Application("Notes").activate()`; increase timeout with `delay` |
| Can't get application "Notes" | -2700 | Notes.app not installed or renamed | Verify with `mdfind "kMDItemCFBundleIdentifier == com.apple.Notes"` |
| Can't get folder | -1728 | Folder name mismatch (case-sensitive) | List folders first: `Notes.defaultAccount.folders().map(f => f.name())` |
| Connection is invalid | -609 | Notes.app crashed mid-operation | Pause writes, relaunch through the supported user workflow, then run a read-only check |
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
echo "Account names and TCC database entries intentionally omitted"
echo "=== Done ==="
```

## Common Fixes

```bash
# Verify Notes is responsive after an approved relaunch
osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length'

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
| Errors persist after consent review | Client not approved for the invoking user | Review the exact client in System Settings or approved MDM policy |
| iCloud notes show stale data | Sync unavailable | Pause writes and follow supported iCloud recovery guidance |
| Sandbox prevents database read | SIP protects TCC.db | Use `osascript` to test access instead of direct DB query |
| Script works manually, fails from cron | Cron has no TCC context | Use launchd with `AssociatedBundleIdentifiers` instead |

## Output

Troubleshooting produces a redacted failure classification, a scoped verification outcome, and the next owner action. It must not include account names, full note/folder listings, TCC rows, or raw job input.

## Examples

For `-1712`, pause the affected write, run a read-only availability check after the app is ready, then compare the operation identifier with the ledger before deciding whether to retry. For `-1743`, stop and request consent for the exact client rather than resetting all Apple Events permissions.

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [Apple TCC Overview](https://support.apple.com/guide/security/controlling-app-access-to-files-secddd1d86a6/web)
- [OSStatus Error Codes](https://www.osstatus.com/)

## Next Steps

For incident response when errors cascade, see `apple-notes-incident-runbook`. For TCC and security hardening, see `apple-notes-security-basics`.
