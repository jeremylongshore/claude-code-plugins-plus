---
name: apple-notes-performance-tuning
description: |
  Optimize Apple Notes automation performance for large note collections.
  Trigger: "apple notes performance".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Performance Tuning

## Overview

Apple Notes automation performance degrades linearly with note count because JXA loads all note objects into memory when you access a collection. A vault with 10,000+ notes can take 30+ seconds for a simple list operation. The primary bottleneck is the Apple Events bridge between your script and Notes.app — every property access (name, body, date) is a separate IPC call. This guide covers caching strategies, incremental sync, batch optimization, and architectural patterns to keep automation responsive at scale.

## Performance Benchmarks

| Operation | 100 notes | 1,000 notes | 10,000 notes |
|-----------|----------|-------------|-------------|
| List all (names only) | ~0.5s | ~3s | ~30s |
| Search by name (`.whose()`) | ~0.3s | ~2s | ~20s |
| Full-text search (body scan) | ~1s | ~8s | ~80s |
| Create single note | ~0.2s | ~0.2s | ~0.2s |
| Export all to JSON | ~1s | ~10s | ~100s |
| Count notes only (`.length`) | ~0.1s | ~0.3s | ~1s |

## Strategy 1: Minimize Property Access

```javascript
// BAD: Each property access is a separate Apple Event IPC call
const Notes = Application("Notes");
const allNotes = Notes.defaultAccount.notes();
allNotes.forEach(n => {
  console.log(n.name());   // IPC call 1
  console.log(n.body());   // IPC call 2
  console.log(n.modificationDate()); // IPC call 3
});
// With 1000 notes = 3000 IPC calls

// GOOD: Batch extract in a single JXA evaluation
const data = Notes.defaultAccount.notes().map(n => ({
  title: n.name(),
  modified: n.modificationDate().toISOString(),
}));
// Single JXA evaluation, much faster for bulk reads
```

## Strategy 2: Local SQLite Cache

```bash
#!/bin/bash
# Export notes to SQLite for fast local queries
DB="$HOME/.notes-cache.db"
sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS notes (
  id TEXT PRIMARY KEY, title TEXT, body TEXT, folder TEXT,
  created TEXT, modified TEXT, indexed_at TEXT
);"

osascript -l JavaScript -e '
  const Notes = Application("Notes");
  Notes.defaultAccount.notes().map(n => JSON.stringify({
    id: n.id(), title: n.name(), body: n.plaintext(),
    folder: n.container().name(),
    created: n.creationDate().toISOString(),
    modified: n.modificationDate().toISOString()
  })).join("\n");
' | while IFS= read -r line; do
  echo "$line" | jq -r '[.id, .title, .body, .folder, .created, .modified, now | todate] | @csv' \
    | sqlite3 "$DB" ".import /dev/stdin notes"
done 2>/dev/null

# Now query locally (instant)
sqlite3 "$DB" "SELECT title FROM notes WHERE body LIKE '%project%' ORDER BY modified DESC LIMIT 10;"
```

## Strategy 3: Incremental Sync

```typescript
// src/sync/incremental.ts
import { execSync } from "child_process";
import { readFileSync, writeFileSync } from "fs";

const LAST_SYNC_FILE = ".notes-last-sync";

function getLastSync(): Date {
  try { return new Date(readFileSync(LAST_SYNC_FILE, "utf8").trim()); }
  catch { return new Date(0); } // First run: sync everything
}

function incrementalSync(): void {
  const lastSync = getLastSync();
  const allNotes = JSON.parse(execSync(
    `osascript -l JavaScript -e 'JSON.stringify(Application("Notes").defaultAccount.notes().map(n => ({id: n.id(), title: n.name(), modified: n.modificationDate().toISOString()})))'`,
    { encoding: "utf8" }
  ));

  const changed = allNotes.filter((n: any) => new Date(n.modified) > lastSync);
  console.log(`${changed.length} notes modified since ${lastSync.toISOString()}`);

  // Process only changed notes (fetch full body only for these)
  for (const note of changed) {
    console.log(`Syncing: ${note.title}`);
    // ... process individual note
  }

  writeFileSync(LAST_SYNC_FILE, new Date().toISOString());
}
```

## Strategy 4: Use `.whose()` for Filtered Queries

```javascript
// .whose() pushes filtering to Notes.app (faster than client-side filter)
const Notes = Application("Notes");

// Faster than loading all notes and filtering in JS
const recentNotes = Notes.defaultAccount.notes.whose({
  _match: [ObjectSpecifier().modificationDate, ">", new Date(Date.now() - 86400000)]
});

// Search by name (case-insensitive)
const matches = Notes.defaultAccount.notes.whose({
  name: { _contains: "project" }
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Script hangs for >60s | Too many notes with body() access | Use `.length` first to assess scale; use cache for large vaults |
| Memory spike during export | All note bodies loaded into JXA runtime | Process in batches; stream to file instead of building array |
| SQLite cache stale | Forgot to re-sync after edits | Run incremental sync on schedule via launchd |
| `.whose()` returns wrong results | Complex predicates not supported in JXA | Fall back to full load + JS filter for complex queries |
| iCloud sync slows writes | Each write triggers sync | Batch writes with 1s delay; use "On My Mac" for bulk import |

## Resources

- [JXA Performance Tips](https://github.com/JXA-Cookbook/JXA-Cookbook/wiki/Optimizing-JXA)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [SQLite Full-Text Search](https://www.sqlite.org/fts5.html)

## Next Steps

For handling rate limits during bulk operations, see `apple-notes-rate-limits`. For monitoring performance trends, see `apple-notes-observability`.
