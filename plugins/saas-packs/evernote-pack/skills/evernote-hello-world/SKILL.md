---
name: evernote-hello-world
description: |
  Create a minimal working Evernote example.
  Use when starting a new Evernote integration, testing your setup,
  or learning basic Evernote API patterns.
  Trigger with phrases like "evernote hello world", "evernote example",
  "evernote quick start", "simple evernote code", "create first note".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Hello World

## Overview
Create your first Evernote note using the Cloud API, demonstrating ENML format and NoteStore operations.

## Prerequisites
- Completed `evernote-install-auth` setup
- Valid access token (OAuth or Developer Token for sandbox)
- Development environment ready

## Instructions

### Step 1: Create Entry File

Initialize an authenticated Evernote client. Use a Developer Token for sandbox or an OAuth access token for production.

```javascript
// hello-evernote.js
const Evernote = require('evernote');

const client = new Evernote.Client({
  token: process.env.EVERNOTE_ACCESS_TOKEN,
  sandbox: true // false for production
});
```

### Step 2: Understand ENML Format

Evernote uses ENML (Evernote Markup Language), a restricted XHTML subset. Every note must include the XML declaration, DOCTYPE, and `<en-note>` root element. Forbidden elements include `<script>`, `<form>`, `<iframe>`. Only inline styles are allowed (no `class` or `id` attributes).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
  <h1>Note Title</h1>
  <p>Content goes here</p>
  <en-todo checked="false"/> A task item
</en-note>
```

### Step 3: Create Your First Note

Build ENML content and call `noteStore.createNote()`. The returned object contains the `guid`, `title`, and `created` timestamp.

```javascript
async function createHelloWorldNote() {
  const noteStore = client.getNoteStore();

  const content = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
  <h1>Hello from Claude Code!</h1>
  <p>Created at: ${new Date().toISOString()}</p>
</en-note>`;

  const note = new Evernote.Types.Note();
  note.title = 'Hello World - Evernote API';
  note.content = content;

  const createdNote = await noteStore.createNote(note);
  console.log('Note GUID:', createdNote.guid);
  return createdNote;
}
```

### Step 4: List Notebooks and Retrieve Notes

Use `listNotebooks()` to enumerate notebooks and `getNote()` with boolean flags to control what data is returned (content, resources, recognition, alternate data).

```javascript
const noteStore = client.getNoteStore();

// List all notebooks
const notebooks = await noteStore.listNotebooks();
notebooks.forEach(nb => console.log(`- ${nb.name} (${nb.guid})`));

// Retrieve a note with content
const note = await noteStore.getNote(noteGuid, true, false, false, false);
console.log('Title:', note.title);
```

For the complete working example with Python SDK, todo lists, and a combined workflow, see [Implementation Guide](references/implementation-guide.md).

## Output
- Working code file with Evernote client initialization
- Successfully created note in your Evernote account
- Console output with note GUID and confirmation

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `EDAMUserException: BAD_DATA_FORMAT` | Invalid ENML content | Validate against ENML DTD; ensure XML declaration and DOCTYPE |
| `EDAMNotFoundException` | Note or notebook not found | Check GUID is correct and note is not in trash |
| `EDAMSystemException: RATE_LIMIT_REACHED` | Too many requests | Wait for `rateLimitDuration` seconds before retrying |
| `Missing DOCTYPE` | ENML missing required header | Add `<?xml ...?>` and `<!DOCTYPE ...>` before `<en-note>` |

## Resources
- [Creating Notes](https://dev.evernote.com/doc/articles/creating_notes.php)
- [ENML Reference](https://dev.evernote.com/doc/articles/enml.php)
- [Core Concepts](https://dev.evernote.com/doc/articles/core_concepts.php)
- [API Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
Proceed to `evernote-local-dev-loop` for development workflow setup.

## Examples

**Sandbox test**: Create a note using a Developer Token with `sandbox: true`, verify it appears in your sandbox account at `sandbox.evernote.com`.

**Production note**: Switch to OAuth access token, set `sandbox: false`, create a note in a specific notebook using `note.notebookGuid`.
