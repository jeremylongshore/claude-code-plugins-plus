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

## Performance Benchmarks
| Operation | 100 notes | 1000 notes | 10000 notes |
|-----------|----------|------------|-------------|
| List all | ~0.5s | ~3s | ~30s |
| Search by name | ~0.3s | ~2s | ~20s |
| Full-text search | ~1s | ~8s | ~80s |
| Create note | ~0.2s | ~0.2s | ~0.2s |
| Export all to JSON | ~1s | ~10s | ~100s |

## Optimization Strategies

### 1. Limit Results
```javascript
// BAD: Load all notes then slice
const all = Notes.defaultAccount.notes(); // Loads everything
const first10 = all.slice(0, 10);

// BETTER: Specify range (JXA supports this for some operations)
// Unfortunately JXA does not support server-side filtering
// Best approach: cache results locally
```

### 2. Local SQLite Cache
```bash
# Export to SQLite once, then query locally
osascript -l JavaScript scripts/export-to-sqlite.js
sqlite3 notes-cache.db "SELECT title FROM notes WHERE body LIKE '%project%'"
```

### 3. Incremental Sync
```typescript
// Only process notes modified since last sync
const lastSync = new Date(fs.readFileSync(".last-sync", "utf8"));
const modified = allNotes.filter(n => n.modificationDate() > lastSync);
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
