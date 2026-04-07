---
name: apple-notes-upgrade-migration
description: |
  Migrate Apple Notes automation scripts between macOS versions.
  Trigger: "apple notes upgrade migration".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Upgrade & Migration

## Overview

Each macOS major release can change Apple Notes capabilities, JXA API behavior, and the underlying NoteStore database schema. Automation scripts that work on Ventura may fail on Sonoma due to new properties, changed Apple Events handling, or TCC permission resets. This guide covers version-specific changes, pre-upgrade backup procedures, post-upgrade validation, and a compatibility matrix for JXA features across macOS versions.

## macOS Version Compatibility Matrix

| macOS Version | Notes Features Added | JXA Impact | Breaking Changes |
|--------------|---------------------|------------|-----------------|
| Monterey (12) | Quick Notes, #tags in body | No new JXA properties | None |
| Ventura (13) | Shared notes, smart folders | Sharing not exposed in JXA | TCC changes; re-prompt required |
| Sonoma (14) | Tags as first-class, link notes | Tag properties partially accessible | Smart folder API changed |
| Sequoia (15) | Math expressions, audio recording | New content types in body HTML | Apple Events timeout behavior changed |

## Pre-Upgrade Backup

```bash
#!/bin/bash
# Run BEFORE upgrading macOS
BACKUP_DIR="$HOME/notes-pre-upgrade-$(sw_vers -productVersion)-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "Backing up Apple Notes before macOS upgrade..."
echo "Current macOS: $(sw_vers -productVersion)"

# Full export with metadata
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const data = Notes.accounts().map(a => ({
    account: a.name(),
    notes: a.notes().map(n => ({
      id: n.id(), title: n.name(), body: n.body(),
      folder: n.container().name(),
      created: n.creationDate().toISOString(),
      modified: n.modificationDate().toISOString(),
      attachments: n.attachments().length
    }))
  }));
  JSON.stringify(data, null, 2);
' > "$BACKUP_DIR/full-backup.json"

NOTE_COUNT=$(jq '[.[].notes | length] | add' "$BACKUP_DIR/full-backup.json")
echo "Backed up $NOTE_COUNT notes to $BACKUP_DIR/full-backup.json"

# Also record current automation state
echo "macOS: $(sw_vers -productVersion)" > "$BACKUP_DIR/system-info.txt"
echo "Xcode CLT: $(xcode-select -p 2>/dev/null)" >> "$BACKUP_DIR/system-info.txt"
echo "Node: $(node -v 2>/dev/null)" >> "$BACKUP_DIR/system-info.txt"
echo "osascript: $(osascript -l JavaScript -e '"JXA OK"' 2>/dev/null)" >> "$BACKUP_DIR/system-info.txt"
```

## Post-Upgrade Validation

```bash
#!/bin/bash
# Run AFTER upgrading macOS
echo "=== Post-Upgrade Apple Notes Validation ==="
echo "New macOS: $(sw_vers -productVersion)"

PASS=0; FAIL=0

check() { if [ "$2" = "PASS" ]; then echo "[PASS] $1"; PASS=$((PASS+1)); else echo "[FAIL] $1"; FAIL=$((FAIL+1)); fi }

# Test basic JXA access (TCC may need re-approval)
NOTE_COUNT=$(osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length' 2>/dev/null)
check "JXA access (${NOTE_COUNT:-DENIED} notes)" "$([ -n "$NOTE_COUNT" ] && echo PASS || echo FAIL)"

# Compare note count with pre-upgrade backup
if [ -f "$1" ]; then
  BACKUP_COUNT=$(jq '[.[].notes | length] | add' "$1")
  check "Note count matches backup ($NOTE_COUNT vs $BACKUP_COUNT)" \
    "$([ "$NOTE_COUNT" = "$BACKUP_COUNT" ] && echo PASS || echo FAIL)"
fi

# Test folder access
FOLDER_COUNT=$(osascript -l JavaScript -e 'Application("Notes").defaultAccount.folders.length' 2>/dev/null)
check "Folder access ($FOLDER_COUNT folders)" "$([ -n "$FOLDER_COUNT" ] && echo PASS || echo FAIL)"

# Test write capability
TEST_NOTE=$(osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const n = Notes.Note({name: "__upgrade_test_" + Date.now(), body: "test"});
  Notes.defaultAccount.folders[0].notes.push(n);
  n.id();
' 2>/dev/null)
check "Write access" "$([ -n "$TEST_NOTE" ] && echo PASS || echo FAIL)"
# Cleanup
[ -n "$TEST_NOTE" ] && osascript -l JavaScript -e "Application('Notes').notes.byId('$TEST_NOTE').delete()" 2>/dev/null

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -gt 0 ] && echo "ACTION REQUIRED: Fix failures before resuming automation"
```

## Common Post-Upgrade Issues

```bash
# TCC permissions reset after upgrade — re-approve
tccutil reset AppleEvents
osascript -l JavaScript -e 'Application("Notes").name()'  # Triggers re-prompt

# launchd agents may need reload after upgrade
launchctl unload ~/Library/LaunchAgents/com.yourorg.notes-automation.plist
launchctl load ~/Library/LaunchAgents/com.yourorg.notes-automation.plist

# Command Line Tools may need reinstall
xcode-select --install
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| "Not authorized" after upgrade | TCC reset by macOS installer | `tccutil reset AppleEvents`; re-run script to trigger prompt |
| Note count mismatch post-upgrade | Notes database migration in progress | Wait 10-15 minutes for iCloud re-sync; check again |
| New JXA properties cause errors on old OS | Script uses Sonoma features on Ventura | Version-check: `sw_vers -productVersion` before using new APIs |
| launchd agent not starting | Plist schema changed in new macOS | Re-validate plist: `plutil -lint your.plist` |
| Smart folder queries return wrong results | Smart folder criteria changed between versions | Re-create smart folders after upgrade; test queries |

## Resources

- [macOS Release Notes](https://developer.apple.com/documentation/macos-release-notes)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [Apple Platform Security Updates](https://support.apple.com/en-us/100100)

## Next Steps

For full migration between platforms, see `apple-notes-migration-deep-dive`. For production readiness after upgrade, see `apple-notes-prod-checklist`.
