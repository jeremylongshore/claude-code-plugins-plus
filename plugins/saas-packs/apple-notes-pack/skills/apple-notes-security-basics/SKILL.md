---
name: apple-notes-security-basics
description: |
  Apply security best practices for Apple Notes automation scripts.
  Trigger: "apple notes security".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Security Basics

## Overview

Apple Notes security involves three layers: macOS TCC (Transparency, Consent, and Control) which gates which apps can send Apple Events to Notes.app, the macOS sandbox that prevents direct database access, and iCloud encryption that protects notes in transit and at rest. For automation scripts, the primary security concerns are: preventing unauthorized Apple Events access, securing exported note data, avoiding credential leakage in scripts, and understanding the difference between standard and end-to-end encrypted (locked) notes.

## Security Checklist

- [ ] Scripts run only locally (never expose osascript to network input)
- [ ] No note content written to log files (may contain PII or secrets)
- [ ] TCC permissions scoped to specific apps only (not blanket approval)
- [ ] Exported notes stored with restrictive permissions (`chmod 600`)
- [ ] iCloud account uses two-factor authentication
- [ ] Automation scripts do not hardcode note content or search terms
- [ ] Temporary files cleaned up after processing (`trap` on exit)
- [ ] Locked (encrypted) notes handled separately (cannot be read via JXA)

## TCC Permission Management

```bash
# Check current TCC grants for Apple Events
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT client, allowed, auth_reason FROM access WHERE service='kTCCServiceAppleEvents';" \
  2>/dev/null || echo "Cannot read TCC.db — SIP is active (this is expected)"

# Reset all Apple Events permissions (forces re-prompt)
tccutil reset AppleEvents

# View which apps have automation access in System Settings:
# System Settings > Privacy & Security > Automation
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation"
```

## Safe Data Export Pattern

```bash
#!/bin/bash
# Secure export with cleanup on exit
EXPORT_FILE=$(mktemp /tmp/notes-export-XXXXXX.json)
trap 'rm -f "$EXPORT_FILE"' EXIT

# Export with restricted permissions from the start
umask 077
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  JSON.stringify(Notes.defaultAccount.notes().map(n => ({
    title: n.name(),
    body: n.plaintext(),
    folder: n.container().name()
  })));
' > "$EXPORT_FILE"

echo "Exported to $EXPORT_FILE ($(wc -c < "$EXPORT_FILE") bytes)"
# Process the file...
# File is automatically deleted on exit via trap
```

## Locked Notes and Encryption

```javascript
// Locked notes (end-to-end encrypted) cannot be read via JXA
// Attempting to access a locked note's body() returns an error
const Notes = Application("Notes");

const allNotes = Notes.defaultAccount.notes();
allNotes.forEach(n => {
  try {
    const body = n.body();
    // Note is unlocked — process normally
  } catch (e) {
    // Note is likely locked (encrypted)
    console.log(`Skipping locked note: ${n.name()}`);
  }
});

// Note: There is no JXA API to unlock notes programmatically.
// Locked notes require the user's password/biometrics in Notes.app UI.
```

## Keychain Integration for Scripts

```bash
# Store automation credentials in macOS Keychain (not in script files)
# Add a credential
security add-generic-password -a "notes-automation" -s "notes-export-key" \
  -w "your-encryption-key" -T /usr/bin/osascript

# Retrieve in scripts
KEY=$(security find-generic-password -a "notes-automation" -s "notes-export-key" -w 2>/dev/null)
[ -z "$KEY" ] && echo "ERROR: Keychain credential not found" && exit 1
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| TCC prompt never appears | App already denied; macOS won't re-prompt | `tccutil reset AppleEvents`; retry |
| Cannot read locked notes | End-to-end encrypted; no JXA access | Skip locked notes; document limitation for users |
| Export file readable by other users | Default umask too permissive | Set `umask 077` before writing; `chmod 600` after |
| Script exposes note content in process list | Note content passed as CLI argument | Pipe content via stdin or temp file instead of `-e` argument |
| Automation works after upgrade but TCC reset | macOS upgrade clears some TCC entries | Re-approve automation permissions after every OS update |

## Resources

- [Apple Platform Security Guide](https://support.apple.com/guide/security/welcome/web)
- [TCC Deep Dive](https://www.rainforestqa.com/blog/macos-tcc-db-deep-dive)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [macOS Keychain Services](https://developer.apple.com/documentation/security/keychain_services)

## Next Steps

For enterprise access control and MDM integration, see `apple-notes-enterprise-rbac`. For production security validation, see `apple-notes-prod-checklist`.
