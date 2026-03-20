---
name: evernote-data-handling
description: |
  Best practices for handling Evernote data.
  Use when implementing data storage, processing notes,
  handling attachments, or ensuring data integrity.
  Trigger with phrases like "evernote data", "handle evernote notes",
  "evernote storage", "process evernote content".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Data Handling

## Overview
Best practices for handling Evernote data including ENML content processing, attachment management, local database sync, and ENEX export/import.

## Prerequisites
- Understanding of Evernote data model (Notes, Notebooks, Tags, Resources)
- Database for local storage (SQLite, PostgreSQL, etc.)
- File storage for attachments

## Instructions

### Step 1: Data Schema Design

Design a local database schema that mirrors Evernote's data model. Key tables: `notes` (guid, title, content, notebookGuid, created, updated, USN), `notebooks` (guid, name, stack), `tags` (guid, name), `resources` (guid, noteGuid, mime, hash, size). Track Update Sequence Numbers (USN) for incremental sync.

```sql
CREATE TABLE notes (
  guid TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT,
  notebook_guid TEXT REFERENCES notebooks(guid),
  created BIGINT,
  updated BIGINT,
  usn INTEGER DEFAULT 0
);
```

### Step 2: ENML Content Processing

Parse ENML to extract plain text (strip tags), convert to HTML (replace `<en-note>` with `<body>`, resolve `<en-media>` to `<img>`/`<a>` tags), or convert to Markdown. Validate ENML before sending to the API by checking for required declarations and forbidden elements.

```javascript
function enmlToPlainText(enml) {
  return enml
    .replace(/<\?xml[^>]*\?>/g, '')
    .replace(/<!DOCTYPE[^>]*>/g, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}
```

### Step 3: Resource (Attachment) Handling

Download resources via `noteStore.getResource(guid, withData, ...)`. Store binary data locally with the MD5 hash as filename. Track MIME types for proper content-type serving. Compute hashes for integrity verification.

### Step 4: Sync Data Manager

Implement incremental sync using `getSyncState()` to get the current server USN, then `getSyncChunk()` to fetch changes since your last sync. Process chunks in order: notebooks first, then tags, then notes, then resources.

```javascript
const syncState = await noteStore.getSyncState();
if (syncState.updateCount > lastSyncUSN) {
  const chunk = await noteStore.getSyncChunk(lastSyncUSN, 100, true);
  // Process chunk.notebooks, chunk.tags, chunk.notes, chunk.resources
}
```

### Step 5: Data Export

Export notes to ENEX (Evernote's XML export format), JSON, or Markdown. ENEX preserves the full note structure including resources and is compatible with Evernote import.

For the complete data schema, sync manager, ENML processor, and export implementations, see [Implementation Guide](references/implementation-guide.md).

## Output
- SQL schema for local Evernote data storage
- ENML-to-text and ENML-to-HTML converters
- Resource download and local storage manager
- Incremental sync engine using USN tracking
- ENEX, JSON, and Markdown export utilities

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `BAD_DATA_FORMAT` | Malformed ENML during update | Validate ENML with DTD check before API call |
| `QUOTA_REACHED` | Upload limit exceeded | Check `user.accounting.uploaded` before creating notes |
| `DATA_CONFLICT` | Note modified since last read | Refetch note by GUID and merge changes |
| Sync chunk gaps | Missed USN range | Request full sync from USN 0 |

## Resources
- [Evernote Data Model](https://dev.evernote.com/doc/articles/data_model.php)
- [ENML Reference](https://dev.evernote.com/doc/articles/enml.php)
- [Synchronization](https://dev.evernote.com/doc/articles/synchronization.php)
- [ENEX Export Format](https://dev.evernote.com/doc/articles/enex.php)

## Next Steps
For enterprise features, see `evernote-enterprise-rbac`.

## Examples

**Local mirror**: Sync all notes to a local SQLite database using incremental sync. Store resources on disk keyed by MD5 hash. Use the local mirror for full-text search without API calls.

**Markdown export**: Convert all notes in a notebook to Markdown files, preserving folder structure from notebook stacks, and saving attachments to an `assets/` directory.
