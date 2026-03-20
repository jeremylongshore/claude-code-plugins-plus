---
name: evernote-migration-deep-dive
description: |
  Deep dive into Evernote data migration strategies.
  Use when migrating to/from Evernote, bulk data transfers,
  or complex migration scenarios.
  Trigger with phrases like "migrate to evernote", "migrate from evernote",
  "evernote data transfer", "bulk evernote migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -5`

## Overview
Comprehensive guide for migrating data to and from Evernote, including ENEX export/import, bulk API operations, format conversions (ENML to Markdown, HTML to ENML), and data integrity verification.

## Prerequisites
- Understanding of Evernote data model (Notes, Notebooks, Tags, Resources)
- Source/target system access credentials
- Sufficient API quota for migration volume
- Backup strategy in place before starting

## Instructions

### Step 1: Migration Planning

Assess the migration scope: count notes, notebooks, tags, and total resource size. Estimate API call count and quota consumption. Plan for rate limits (add delays between operations).

```javascript
async function assessMigration(noteStore) {
  const notebooks = await noteStore.listNotebooks();
  const tags = await noteStore.listTags();
  let totalNotes = 0;

  for (const nb of notebooks) {
    const filter = new Evernote.NoteStore.NoteFilter({ notebookGuid: nb.guid });
    const spec = new Evernote.NoteStore.NotesMetadataResultSpec({});
    const result = await noteStore.findNotesMetadata(filter, 0, 1, spec);
    totalNotes += result.totalNotes;
  }

  return {
    notebooks: notebooks.length,
    tags: tags.length,
    totalNotes,
    estimatedApiCalls: totalNotes * 2 + notebooks.length + tags.length,
    estimatedTimeMinutes: Math.ceil((totalNotes * 2 * 200) / 60000) // 200ms per call
  };
}
```

### Step 2: Export from Evernote

Export notes in three formats: ENEX (Evernote's XML format, preserves everything including resources), JSON (structured data for programmatic use), or Markdown (human-readable, loses some formatting).

```javascript
async function exportToMarkdown(noteStore, noteGuid) {
  const note = await noteStore.getNote(noteGuid, true, true, false, false);
  const text = enmlToMarkdown(note.content);

  return {
    title: note.title,
    content: text,
    tags: note.tagNames || [],
    created: new Date(note.created).toISOString(),
    resources: (note.resources || []).map(r => ({
      filename: r.attributes.fileName,
      mime: r.mime,
      size: r.data.size
    }))
  };
}
```

### Step 3: Import to Evernote

Convert source data to ENML format, create notebooks to match source structure, and bulk-create notes with rate limit handling. Verify each import by comparing note counts and content hashes.

### Step 4: Migration Runner

Build a migration runner with progress tracking, checkpointing (resume from failure), and verification. Log every operation for audit trail.

For the full migration planner, ENEX parser, format converters, migration runner, and verification tools, see [Implementation Guide](references/implementation-guide.md).

## Output
- Migration assessment tool (note count, estimated time, quota needs)
- ENEX, JSON, and Markdown exporters
- ENML importer with format conversion
- Migration runner with progress tracking and checkpoint/resume
- Post-migration verification (count comparison, content hash check)

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `QUOTA_REACHED` | Upload quota exceeded during import | Wait for quota reset or upgrade account tier |
| `RATE_LIMIT_REACHED` | Too many API calls during bulk migration | Increase delay between operations, use checkpointing |
| `BAD_DATA_FORMAT` | Source content not valid ENML | Validate and sanitize content before import |
| Lost resources | Attachments not migrated | Verify resource hashes match after migration |

## Resources
- [Evernote Export Format (ENEX)](https://dev.evernote.com/doc/articles/enex.php)
- [ENML Reference](https://dev.evernote.com/doc/articles/enml.php)
- [API Reference](https://dev.evernote.com/doc/reference/)
- [Synchronization](https://dev.evernote.com/doc/articles/synchronization.php)

## Examples

**Export all notes to Markdown**: Iterate through all notebooks, export each note as a Markdown file with frontmatter (title, tags, date), save resources to `assets/` directory, preserving notebook-as-folder structure.

**Import from Notion**: Parse Notion export (Markdown + CSV), convert to ENML, create matching notebooks, and bulk-import with checkpoint/resume for large exports (10,000+ pages).
