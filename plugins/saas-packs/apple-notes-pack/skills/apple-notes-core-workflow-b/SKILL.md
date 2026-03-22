---
name: apple-notes-core-workflow-b
description: |
  Export and convert Apple Notes to Markdown, JSON, HTML, and SQLite.
  Use when backing up notes, exporting to other apps, converting HTML to Markdown,
  or building searchable note archives from Apple Notes.
  Trigger: "export apple notes", "apple notes to markdown", "backup apple notes",
  "apple notes to JSON", "convert apple notes".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation, export]
compatible-with: claude-code
---

# Apple Notes Core Workflow B — Export & Conversion

## Overview

Export Apple Notes to portable formats: Markdown, JSON, HTML files, and SQLite databases. Apple Notes stores content as HTML internally — these workflows convert it to developer-friendly formats.

## Instructions

### Step 1: Export All Notes to JSON

```bash
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const allNotes = Notes.defaultAccount.notes();
  const exported = allNotes.map(n => ({
    id: n.id(),
    title: n.name(),
    body: n.body(),
    folder: n.container().name(),
    created: n.creationDate().toISOString(),
    modified: n.modificationDate().toISOString(),
  }));
  JSON.stringify(exported, null, 2);
' > apple-notes-export.json

echo "Exported $(jq length apple-notes-export.json) notes to apple-notes-export.json"
```

### Step 2: Export Notes as Markdown Files

```bash
#!/bin/bash
# scripts/notes-to-markdown.sh
OUTPUT_DIR="${1:-./notes-export}"
mkdir -p "$OUTPUT_DIR"

osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const notes = Notes.defaultAccount.notes();
  notes.map(n => JSON.stringify({
    title: n.name(),
    body: n.body(),
    folder: n.container().name(),
  })).join("\n---SEPARATOR---\n");
' | while IFS= read -r line; do
  if [ "$line" = "---SEPARATOR---" ]; then continue; fi
  title=$(echo "$line" | jq -r '.title' 2>/dev/null)
  body=$(echo "$line" | jq -r '.body' 2>/dev/null)
  folder=$(echo "$line" | jq -r '.folder' 2>/dev/null)

  # Convert HTML to basic Markdown
  md_body=$(echo "$body" | sed 's/<h1>/# /g; s/<\/h1>//g; s/<h2>/## /g; s/<\/h2>//g; s/<p>//g; s/<\/p>/\n/g; s/<br>/\n/g; s/<li>/- /g; s/<\/li>//g; s/<[^>]*>//g')

  safe_title=$(echo "$title" | tr '/:' '-' | head -c 100)
  mkdir -p "$OUTPUT_DIR/$folder"
  echo -e "# $title\n\n$md_body" > "$OUTPUT_DIR/$folder/$safe_title.md"
done

echo "Export complete: $OUTPUT_DIR"
```

### Step 3: Export to SQLite Database

```bash
# Using apple-notes-to-sqlite (pip install apple-notes-to-sqlite)
pip install apple-notes-to-sqlite
apple-notes-to-sqlite export notes.db

# Or build your own with JXA + sqlite3
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const notes = Notes.defaultAccount.notes();
  const rows = notes.map(n =>
    `INSERT INTO notes (title, body, folder, created) VALUES (${JSON.stringify(n.name())}, ${JSON.stringify(n.body())}, ${JSON.stringify(n.container().name())}, ${JSON.stringify(n.creationDate().toISOString())});`
  ).join("\n");
  rows;
' > /tmp/notes-inserts.sql

sqlite3 notes.db << 'SQL'
CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT, body TEXT, folder TEXT, created TEXT);
.read /tmp/notes-inserts.sql
SELECT COUNT(*) || ' notes imported' FROM notes;
SQL
```

### Step 4: Full-Text Search on Exported Notes

```bash
# Search across all exported notes
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const query = "project plan";
  const results = Notes.defaultAccount.notes().filter(n => {
    const body = n.body().toLowerCase();
    const name = n.name().toLowerCase();
    return body.includes(query) || name.includes(query);
  });
  results.map(n => `${n.name()} (${n.container().name()})`).join("\n");
'
```

## Output

- JSON export of all notes with metadata
- Markdown files organized by folder
- SQLite database with full note content
- Full-text search across notes

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Slow export | Thousands of notes | Export in batches by folder |
| HTML artifacts in Markdown | Complex formatting | Use a proper HTML-to-MD library (turndown) |
| Missing attachments | Images not exported | Attachments need separate export path |
| Encoding issues | Unicode in note titles | Use safe filename sanitization |

## Resources

- [apple-notes-to-sqlite](https://github.com/dogsheep/apple-notes-to-sqlite)
- [AppleNotesExport](https://github.com/johansan/AppleNotesExport)

## Next Steps

For common errors, see `apple-notes-common-errors`.
