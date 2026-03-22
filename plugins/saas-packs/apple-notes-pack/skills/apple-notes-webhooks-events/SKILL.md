---
name: apple-notes-webhooks-events
description: |
  Monitor Apple Notes changes using file system events and Shortcuts triggers.
  Trigger: "apple notes events".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Webhooks & Events

## Overview
Apple Notes has no webhook API. Monitor changes using: (1) File system watching on the Notes database, (2) Apple Shortcuts automation triggers, or (3) Periodic polling via JXA.

## Polling-Based Change Detection
```typescript
// src/events/notes-watcher.ts
import { execSync } from "child_process";

interface NoteSnapshot { id: string; title: string; modified: string; }

let lastSnapshot: Map<string, string> = new Map();

function detectChanges(): { added: string[]; modified: string[]; deleted: string[] } {
  const current = JSON.parse(execSync(
    `osascript -l JavaScript -e 'JSON.stringify(Application("Notes").defaultAccount.notes().map(n => ({id: n.id(), title: n.name(), modified: n.modificationDate().toISOString()})))'`,
    { encoding: "utf8" }
  )) as NoteSnapshot[];

  const currentMap = new Map(current.map(n => [n.id, n.modified]));
  const added = current.filter(n => !lastSnapshot.has(n.id)).map(n => n.title);
  const modified = current.filter(n => lastSnapshot.has(n.id) && lastSnapshot.get(n.id) !== n.modified).map(n => n.title);
  const deleted = [...lastSnapshot.keys()].filter(id => !currentMap.has(id));

  lastSnapshot = currentMap;
  return { added, modified, deleted };
}

// Poll every 60 seconds
setInterval(() => {
  const changes = detectChanges();
  if (changes.added.length || changes.modified.length || changes.deleted.length) {
    console.log("Changes detected:", changes);
  }
}, 60000);
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
