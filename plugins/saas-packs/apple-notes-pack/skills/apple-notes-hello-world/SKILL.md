---
name: apple-notes-hello-world
description: |
  Create, read, and list Apple Notes using JXA and AppleScript.
  Use when learning Notes automation, creating your first automated note,
  or testing read/write access to Apple Notes from scripts.
  Trigger: "apple notes hello world", "create apple note", "read apple notes",
  "apple notes example", "osascript notes".
allowed-tools: Read, Write, Edit, Bash(osascript:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation, jxa]
compatible-with: claude-code
---

# Apple Notes Hello World

## Overview

Create, read, search, and delete Apple Notes using JXA (JavaScript for Automation) via `osascript`. All examples work from the command line on macOS.

## Prerequisites

- Completed `apple-notes-install-auth` (permissions granted)
- macOS with Notes.app

## Instructions

### Step 1: Create a Note

```bash
# JXA: Create a note in the default folder
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const defaultFolder = Notes.defaultAccount.folders[0];
  const newNote = Notes.Note({
    name: "Hello from Automation",
    body: "<h1>Hello World</h1><p>This note was created via JXA at " + new Date().toISOString() + "</p>"
  });
  defaultFolder.notes.push(newNote);
  newNote.id();
'

# AppleScript equivalent:
osascript -e '
  tell application "Notes"
    tell account "iCloud"
      make new note at folder "Notes" with properties {name:"Hello AppleScript", body:"<p>Created via AppleScript</p>"}
    end tell
  end tell
'
```

### Step 2: List All Notes

```bash
# List notes with title and creation date
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const notes = Notes.defaultAccount.notes();
  notes.slice(0, 10).map(n =>
    `${n.name()} | Created: ${n.creationDate().toISOString().split("T")[0]}`
  ).join("\n");
'
```

### Step 3: Read a Note's Content

```bash
# Read note body (returns HTML)
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const notes = Notes.defaultAccount.notes();
  const target = notes.find(n => n.name() === "Hello from Automation");
  if (target) {
    `Title: ${target.name()}\nBody: ${target.body()}\nModified: ${target.modificationDate()}`;
  } else {
    "Note not found";
  }
'
```

### Step 4: Search Notes

```bash
# Search by keyword in note name
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const query = "Hello";
  const results = Notes.defaultAccount.notes().filter(n =>
    n.name().toLowerCase().includes(query.toLowerCase())
  );
  results.map(n => n.name()).join("\n") || "No results";
'
```

### Step 5: Create Note in Specific Folder

```bash
# Create a folder and add a note to it
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const account = Notes.defaultAccount;

  // Create folder if it does not exist
  let folder = account.folders().find(f => f.name() === "Automation");
  if (!folder) {
    folder = Notes.Folder({ name: "Automation" });
    account.folders.push(folder);
  }

  // Add note to folder
  const note = Notes.Note({
    name: "Organized Note",
    body: "<p>This note lives in the Automation folder.</p>"
  });
  folder.notes.push(note);
  `Created in folder: ${folder.name()}`;
'
```

### Step 6: Delete a Note

```bash
# Delete by name (moves to Recently Deleted)
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const notes = Notes.defaultAccount.notes();
  const target = notes.find(n => n.name() === "Hello from Automation");
  if (target) {
    Notes.delete(target);
    "Note deleted";
  } else {
    "Note not found";
  }
'
```

## Note Properties

| Property | Type | Writable | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Note title (first line) |
| `body` | string (HTML) | Yes | Full note content as HTML |
| `id` | string | No | Unique identifier |
| `creationDate` | Date | No | When note was created |
| `modificationDate` | Date | No | Last modification |
| `container` | Folder | No | Parent folder |

## Output

- Created a note via JXA and AppleScript
- Listed, searched, and read note content
- Organized note into a folder
- Deleted a note

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Notes got an error` | Notes.app not running | Add `Notes.activate()` first |
| Empty body | Note has no text content | Check note is not just an image |
| `Can't make folder` | Folder already exists | Check before creating |
| Slow response | iCloud sync in progress | Wait for sync; use local account |

## Resources

- [AppleScript Notes Dictionary](https://www.macosxautomation.com/applescript/notes/)
- [JXA Examples](https://jxa-examples.akjems.com/)
- [osascript Manual](https://ss64.com/mac/osascript.html)

## Next Steps

Proceed to `apple-notes-local-dev-loop` for development workflow setup.
