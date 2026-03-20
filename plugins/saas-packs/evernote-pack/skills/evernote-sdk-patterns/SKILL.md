---
name: evernote-sdk-patterns
description: |
  Advanced Evernote SDK patterns and best practices.
  Use when implementing complex note operations, batch processing,
  search queries, or optimizing SDK usage.
  Trigger with phrases like "evernote sdk patterns", "evernote best practices",
  "evernote advanced", "evernote batch operations".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote SDK Patterns

## Overview
Production-ready patterns for working with the Evernote SDK, including search with NoteFilter, pagination, attachments, tags, error handling wrappers, and batch operations with rate limit handling.

## Prerequisites
- Completed `evernote-install-auth` and `evernote-hello-world`
- Understanding of Evernote data model (Notes, Notebooks, Tags, Resources)
- Familiarity with async/await and Promises

## Instructions

### Pattern 1: Search with NoteFilter

Use `NoteFilter` for query terms and sort order, paired with `NotesMetadataResultSpec` to select returned fields. This avoids fetching full note content when only metadata is needed.

```javascript
const filter = new Evernote.NoteStore.NoteFilter({
  words: 'tag:important notebook:Work',
  ascending: false,
  order: Evernote.Types.NoteSortOrder.UPDATED
});

const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
  includeTitle: true, includeUpdated: true,
  includeTagGuids: true, includeNotebookGuid: true
});

const result = await noteStore.findNotesMetadata(filter, 0, 100, spec);
```

### Pattern 2: Creating Notes with Attachments

Compute the MD5 hash of the file buffer, create a `Resource` with the binary data and MIME type, embed it in ENML with `<en-media type="..." hash="..."/>`, and attach it to the note.

```javascript
const hash = crypto.createHash('md5').update(fileBuffer).digest('hex');
const resource = new Evernote.Types.Resource();
resource.data = new Evernote.Types.Data();
resource.data.body = fileBuffer;
resource.mime = 'image/png';

const note = new Evernote.Types.Note();
note.title = 'Note with Attachment';
note.content = wrapInENML(`<en-media type="image/png" hash="${hash}"/>`);
note.resources = [resource];
await noteStore.createNote(note);
```

### Pattern 3: Error Handling Wrapper

Wrap API calls to distinguish `EDAMUserException` (client errors), `EDAMSystemException` (rate limits, maintenance), and `EDAMNotFoundException` (invalid GUIDs). Use `error.rateLimitDuration` for automatic retry delays.

### Pattern 4: Batch Operations

Process items sequentially with configurable delay between operations. On rate limit errors, wait for `rateLimitDuration` seconds then retry. Track progress with callbacks.

### Pattern 5: Tag and Notebook Management

Implement `getOrCreateTag()` and `getOrCreateNotebook()` for idempotent operations. Use `listTags()` / `listNotebooks()` to check existence before creating.

For all nine patterns with complete implementations, see [Implementation Guide](references/implementation-guide.md).

## Output
- Search patterns using `NoteFilter` and `NotesMetadataResultSpec`
- Async generator for paginated note retrieval
- Attachment creation with MD5 hash and MIME type
- Tag and notebook find-or-create utilities
- `EvernoteError` wrapper class with `isRateLimit`, `isNotFound`, `isInvalidData`
- Batch processor with rate limit retry and progress tracking

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `RATE_LIMIT_REACHED` | Too many API calls | Use `rateLimitDuration`, add delays between batch items |
| `BAD_DATA_FORMAT` | Invalid ENML | Validate with `wrapInENML()` before sending |
| `DATA_CONFLICT` | Concurrent modification | Refetch note metadata and retry update |
| `QUOTA_REACHED` | Account storage full | Check remaining quota via `user.accounting` |

## Resources
- [API Reference](https://dev.evernote.com/doc/reference/)
- [Search Grammar](https://dev.evernote.com/doc/articles/search_grammar.php)
- [Core Concepts](https://dev.evernote.com/doc/articles/core_concepts.php)
- [JavaScript SDK](https://github.com/Evernote/evernote-sdk-js)

## Next Steps
See `evernote-core-workflow-a` for note creation and management workflows.

## Examples

**Bulk tagging**: Search for all notes matching a query, then batch-add a tag to each result with 200ms delay between operations and automatic rate limit retry.

**Attachment upload**: Read a PDF from disk, compute its MD5 hash, create a note with the PDF as an `<en-media>` resource, and verify the upload via `getNote()` with `withResources: true`.
