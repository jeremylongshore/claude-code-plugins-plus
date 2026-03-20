---
name: evernote-core-workflow-a
description: |
  Execute Evernote primary workflow: Note Creation and Management.
  Use when creating notes, organizing content, managing notebooks,
  or implementing note-taking features.
  Trigger with phrases like "create evernote note", "evernote note workflow",
  "manage evernote notes", "evernote content".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Core Workflow A: Note Creation & Management

## Overview
Primary workflow for creating, organizing, and managing notes in Evernote. Covers CRUD operations, ENML formatting, notebook organization, and tag management.

## Prerequisites
- Completed `evernote-install-auth` setup
- Understanding of ENML format
- Valid access token configured

## Instructions

### Step 1: Note Creation Service

Build a `NoteService` class that wraps NoteStore operations. Key methods: `createNote()` with ENML wrapping, `createTextNote()` for plain text, `createChecklistNote()` for `<en-todo>` items. Always sanitize titles (max 255 chars, no newlines) and wrap content in the required ENML envelope.

```javascript
// Wrap raw HTML in required ENML envelope
function wrapInENML(content) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>${content}</en-note>`;
}

const note = new Evernote.Types.Note();
note.title = 'Meeting Notes';
note.content = wrapInENML('<p>Discussion points...</p>');
note.tagNames = ['meeting', 'team'];
const created = await noteStore.createNote(note);
```

### Step 2: Note Retrieval and Reading

Use `getNote(guid, withContent, withResources, withRecognition, withAltData)` to control response size. Extract plain text from ENML by stripping tags. Check for uncompleted todos with `/<en-todo\s+checked="false"/`.

### Step 3: Note Updates

Update notes by fetching metadata, modifying fields, and calling `noteStore.updateNote()`. Append content by inserting before the closing `</en-note>` tag. Add tags via `note.tagNames` array. Move notes between notebooks by changing `note.notebookGuid`.

### Step 4: Note Organization

Manage notebooks with `listNotebooks()`, `createNotebook()`, and `getDefaultNotebook()`. Use `notebook.stack` to group notebooks into stacks. Implement `ensureNotebook(name)` to find-or-create by name.

### Step 5: Complete Workflow Example

See [Implementation Guide](references/implementation-guide.md) for the full `NoteService`, `NotebookService`, and a combined workflow that creates meeting notes with checklists, appends content, and toggles todos.

## Output
- `NoteService` class with create, read, update, and delete operations
- ENML content formatting and validation helpers
- `NotebookService` for notebook CRUD and stack organization
- Tag management (add, remove, find-or-create)
- Checklist note support with `<en-todo>` elements

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `BAD_DATA_FORMAT` | Invalid ENML | Use `wrapInENML()` helper; remove forbidden elements (`<script>`, `<form>`) |
| `LIMIT_REACHED` | Too many notebooks (250 max) | Clean up unused notebooks before creating |
| `DATA_REQUIRED` | Missing title or content | Validate inputs before API call |
| `INVALID_USER` | Token expired | Re-authenticate user via OAuth flow |

## Resources
- [Creating Notes](https://dev.evernote.com/doc/articles/creating_notes.php)
- [ENML Reference](https://dev.evernote.com/doc/articles/enml.php)
- [Note Types Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
For search and retrieval workflows, see `evernote-core-workflow-b`.

## Examples

**Meeting notes workflow**: Create a note with attendees, discussion points, and `<en-todo>` action items in a "Work" notebook. Append follow-up items after the meeting. Tag with `meeting` and `team`.

**Bulk note import**: Read Markdown files from disk, convert to ENML using `htmlToENML()`, and create notes in a designated notebook with automatic tag assignment.
