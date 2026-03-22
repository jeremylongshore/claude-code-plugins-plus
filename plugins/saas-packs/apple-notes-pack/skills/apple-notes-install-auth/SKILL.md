---
name: apple-notes-install-auth
description: |
  Set up macOS automation access for Apple Notes via AppleScript, JXA, and Shortcuts.
  Use when configuring accessibility permissions, setting up osascript access,
  or initializing Apple Notes automation on macOS.
  Trigger: "setup apple notes", "apple notes automation", "apple notes permissions".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Bash(defaults:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation, applescript]
compatible-with: claude-code
---

# Apple Notes Install & Auth

## Overview

Apple Notes has no REST API. Automation uses macOS scripting technologies: AppleScript, JavaScript for Automation (JXA), Shortcuts, and the `osascript` command-line tool. No SDK to install — but you need macOS accessibility permissions.

## Prerequisites

- macOS 13+ (Ventura or later recommended)
- Terminal app or iTerm2
- System Preferences > Privacy & Security > Automation permissions

## Instructions

### Step 1: Grant Automation Permissions

```bash
# macOS requires explicit permission for scripts to control Notes.app
# The first time you run an osascript command targeting Notes, macOS will prompt.
# You can also pre-grant in: System Preferences > Privacy & Security > Automation

# Test basic Notes access (will trigger permission prompt)
osascript -e 'tell application "Notes" to get name of every note in default account'
```

### Step 2: Verify JXA (JavaScript for Automation) Access

```bash
# JXA is the modern alternative to AppleScript
# Run JavaScript via osascript with -l JavaScript flag

osascript -l JavaScript -e '
  const Notes = Application("Notes");
  Notes.includeStandardAdditions = true;
  const noteCount = Notes.defaultAccount.notes.length;
  `Apple Notes accessible: ${noteCount} notes found`;
'
```

### Step 3: Create a Wrapper Script

```bash
#!/bin/bash
# scripts/notes-cli.sh — Wrapper for common Apple Notes operations

case "$1" in
  count)
    osascript -l JavaScript -e '
      const Notes = Application("Notes");
      Notes.defaultAccount.notes.length;
    '
    ;;
  list)
    osascript -l JavaScript -e '
      const Notes = Application("Notes");
      const notes = Notes.defaultAccount.notes();
      notes.slice(0, 20).map(n => `${n.id()} | ${n.name()}`).join("\n");
    '
    ;;
  folders)
    osascript -l JavaScript -e '
      const Notes = Application("Notes");
      Notes.defaultAccount.folders().map(f => f.name()).join("\n");
    '
    ;;
  *)
    echo "Usage: notes-cli.sh {count|list|folders}"
    ;;
esac
```

### Step 4: Verify Shortcuts Integration

```bash
# Apple Shortcuts can also interact with Notes
# Check available shortcuts
shortcuts list | grep -i note

# Run a shortcut that creates a note
shortcuts run "Create Note" --input-path /dev/stdin <<< "Test content"
```

## Automation Technologies

| Technology | Language | Best For | Docs |
|-----------|----------|----------|------|
| AppleScript | AppleScript | Simple operations | Apple Scripting Guide |
| JXA | JavaScript | Complex logic, JSON handling | Apple JXA Reference |
| osascript | CLI wrapper | Scripts, CI/CD | `man osascript` |
| Shortcuts | Visual | Non-developer workflows | Shortcuts app |
| PyXA | Python | Python automation | pyxa.dev |

## Output

- macOS automation permissions granted for Notes.app
- JXA access verified with note count
- CLI wrapper script for common operations
- Shortcuts integration confirmed

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Not authorized to send Apple events` | Missing automation permission | Grant in System Preferences > Privacy > Automation |
| `Notes got an error: AppleEvent timed out` | Notes.app not running | Launch Notes first or add `activate` |
| `-1743 errAEAppNotAllowed` | Denied by TCC | Reset TCC: `tccutil reset AppleEvents` |
| `execution error: Notes is not running` | Notes.app closed | Add `tell app "Notes" to activate` |

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Reference](https://developer.apple.com/library/archive/releasenotes/InterapplicationCommunication/RN-JavaScriptForAutomation/)
- [AppleScript Notes Dictionary](https://www.macosxautomation.com/applescript/notes/)

## Next Steps

Proceed to `apple-notes-hello-world` for your first note creation.
