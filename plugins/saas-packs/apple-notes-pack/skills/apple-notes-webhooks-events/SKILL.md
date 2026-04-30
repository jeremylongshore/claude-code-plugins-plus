---
name: apple-notes-webhooks-events
description: 'Monitor Apple Notes changes using file system events and Shortcuts triggers.

  Trigger: "apple notes events".

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
# Apple Notes Webhooks & Events

## Overview

Apple Notes has no webhook, pub/sub, or event streaming API. To detect changes, you must build your own event system using one of three approaches: (1) JXA polling that compares note snapshots at intervals, (2) file system events (FSEvents) on the NoteStore.sqlite database file for near-real-time change detection, or (3) Apple Shortcuts automations that trigger scripts when specific conditions are met. Each approach has different latency, reliability, and resource consumption tradeoffs.

## Approach 1: JXA Polling (Recommended)

```typescript
// src/events/notes-watcher.ts
import { execSync } from "child_process";

interface NoteSnapshot { id: string; title: string; modified: string; }

let lastSnapshot: Map<string, string> = new Map();

function detectChanges(): { added: string[]; modified: string[]; deleted: string[] } {
  const current = JSON.parse(execSync(
    `osascript -l JavaScript -e 'JSON.stringify(Application("Notes").defaultAccount.notes().map(n => ({id: n.id(), title: n.name(), modified: n.modificationDate().toISOString()})))'`,
    { encoding: "utf8", timeout: 30000 }
  )) as NoteSnapshot[];

  const currentMap = new Map(current.map(n => [n.id, n.modified]));
  const added = current.filter(n => !lastSnapshot.has(n.id)).map(n => n.title);
  const modified = current.filter(n =>
    lastSnapshot.has(n.id) && lastSnapshot.get(n.id) !== n.modified
  ).map(n => n.title);
  const deleted = [...lastSnapshot.keys()].filter(id => !currentMap.has(id));

  lastSnapshot = currentMap;
  return { added, modified, deleted };
}

// Poll every 60 seconds
setInterval(() => {
  const changes = detectChanges();
  if (changes.added.length || changes.modified.length || changes.deleted.length) {
    console.log("Changes detected:", JSON.stringify(changes));
    // Trigger downstream actions: export, sync, notify
  }
}, 60000);
```

## Approach 2: FSEvents on Notes Database

```bash
#!/bin/bash
# Watch the Notes database directory for changes (near real-time)
# This detects ANY change to the local Notes SQLite database
NOTES_DB_DIR="$HOME/Library/Group Containers/group.com.apple.notes"

# Using fswatch (install via: brew install fswatch)
fswatch -r "$NOTES_DB_DIR" | while read -r changed_file; do
  # Filter for actual database changes (ignore WAL/SHM churn)
  case "$changed_file" in
    *.sqlite)
      echo "$(date -Iseconds) Notes database changed: $changed_file"
      # Trigger your handler — but throttle to avoid rapid-fire
      # The DB changes frequently during sync; debounce by 5 seconds
      ;;
  esac
done

# Alternative: use macOS built-in log stream for Notes events
# log stream --predicate 'subsystem == "com.apple.notes"' --style compact
```

## Approach 3: Shortcuts Automation Triggers

```bash
# Apple Shortcuts can trigger automations based on:
# - Time of day (run export at midnight)
# - App opens/closes (Notes.app launched)
# - Focus mode changes (work mode → sync work notes)

# Create a Shortcut that runs your script when Notes.app opens:
# 1. Shortcuts > Automations > App > Notes > "Is Opened"
# 2. Add "Run Shell Script" action:
#    osascript -l JavaScript /Users/you/scripts/on-notes-open.js

# Trigger a Shortcut from your scripts (for cross-app events):
shortcuts run "Notes Changed" --input-type text --input "$(date -Iseconds)"
```

## Event Handler Pattern

```typescript
// src/events/handler.ts
type NoteEvent = "added" | "modified" | "deleted";
type EventHandler = (event: NoteEvent, noteTitle: string) => void;

const handlers: EventHandler[] = [];

function onNoteChange(handler: EventHandler): void {
  handlers.push(handler);
}

function emitEvent(event: NoteEvent, title: string): void {
  handlers.forEach(h => h(event, title));
}

// Register handlers
onNoteChange((event, title) => {
  console.log(`[${event.toUpperCase()}] ${title}`);
});

onNoteChange((event, title) => {
  if (event === "added") {
    // Auto-export new notes to backup directory
    execSync(`shortcuts run "Export Note" --input-type text --input "${title}"`);
  }
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Polling misses rapid changes | 60s interval too slow for burst edits | Reduce interval to 15-30s; accept higher CPU usage |
| FSEvents fires too frequently | WAL/SHM file writes during normal sync | Debounce: ignore events within 5s of each other |
| False "deleted" events | Note moved between folders, not deleted | Track folder changes separately; verify deletion before acting |
| Polling timeout on large vaults | >10,000 notes exceeds osascript timeout | Use incremental approach: only check `modificationDate` |
| Shortcut automation unreliable | macOS may delay or skip automations | Use polling as primary; Shortcuts as supplementary trigger |

## Resources

- [FSEvents Programming Guide](https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/FSEvents_ProgGuide/)
- [Apple Shortcuts Automation](https://support.apple.com/guide/shortcuts-mac/create-a-personal-automation-apd690170742/mac)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)

## Next Steps

For monitoring the health of your event system, see `apple-notes-observability`. For handling the events your watcher detects, see `apple-notes-data-handling`.
