---
name: apple-notes-sdk-patterns
description: |
  Apply production-ready patterns for Apple Notes JXA/AppleScript automation.
  Trigger: "apple notes patterns".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes SDK Patterns

## Overview
Production patterns for Apple Notes automation: JXA wrapper class, error handling, batch operations, and cross-account support.

## Instructions

### Step 1: JXA Client Wrapper (Node.js)
```typescript
// src/notes-client.ts
import { execSync } from "child_process";

class AppleNotesClient {
  private runJxa(script: string): string {
    const escaped = script.replace(/'/g, "\\'");
    return execSync(`osascript -l JavaScript -e '${escaped}'`, {
      encoding: "utf8",
      timeout: 30000,
    }).trim();
  }

  listNotes(folder?: string, limit: number = 50): Array<{ id: string; title: string; modified: string }> {
    const script = folder
      ? `const Notes = Application("Notes"); const f = Notes.defaultAccount.folders().find(f => f.name() === "${folder}"); (f ? f.notes() : []).slice(0, ${limit}).map(n => JSON.stringify({id: n.id(), title: n.name(), modified: n.modificationDate().toISOString()})).join("\\n")`
      : `const Notes = Application("Notes"); Notes.defaultAccount.notes().slice(0, ${limit}).map(n => JSON.stringify({id: n.id(), title: n.name(), modified: n.modificationDate().toISOString()})).join("\\n")`;
    return this.runJxa(script).split("\n").filter(Boolean).map(l => JSON.parse(l));
  }

  createNote(title: string, body: string, folder?: string): string {
    const folderPart = folder
      ? `let f = account.folders().find(f => f.name() === "${folder}"); if (!f) { f = Notes.Folder({name: "${folder}"}); account.folders.push(f); }`
      : "let f = account.folders[0];";
    return this.runJxa(`
      const Notes = Application("Notes");
      const account = Notes.defaultAccount;
      ${folderPart}
      const note = Notes.Note({name: ${JSON.stringify(title)}, body: ${JSON.stringify(body)}});
      f.notes.push(note);
      note.id();
    `);
  }

  searchNotes(query: string): Array<{ title: string; folder: string }> {
    const result = this.runJxa(`
      const Notes = Application("Notes");
      const q = "${query}".toLowerCase();
      Notes.defaultAccount.notes().filter(n =>
        n.name().toLowerCase().includes(q) || n.body().toLowerCase().includes(q)
      ).slice(0, 20).map(n => JSON.stringify({title: n.name(), folder: n.container().name()})).join("\\n");
    `);
    return result.split("\n").filter(Boolean).map(l => JSON.parse(l));
  }
}

export { AppleNotesClient };
```

### Step 2: Batch Operations with Throttling
```typescript
async function batchCreateNotes(
  client: AppleNotesClient,
  notes: Array<{ title: string; body: string; folder?: string }>,
  delayMs: number = 500,
): Promise<string[]> {
  const ids: string[] = [];
  for (const note of notes) {
    const id = client.createNote(note.title, note.body, note.folder);
    ids.push(id);
    await new Promise(r => setTimeout(r, delayMs));
  }
  return ids;
}
```

## Output
- Type-safe JXA client wrapper for Node.js
- List, create, search operations via osascript
- Batch operations with throttling

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
