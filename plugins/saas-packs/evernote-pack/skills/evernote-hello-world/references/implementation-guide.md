# Evernote Hello World - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Create Entry File

```javascript
// hello-evernote.js
const Evernote = require('evernote');

// Initialize authenticated client
const client = new Evernote.Client({
  token: process.env.EVERNOTE_ACCESS_TOKEN,
  sandbox: true // Set to false for production
});
```

### Step 2: Understand ENML Format

Evernote uses ENML (Evernote Markup Language), a restricted subset of XHTML:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
  <h1>Note Title</h1>
  <p>This is a paragraph.</p>
  <div>Content goes here</div>
</en-note>
```

**Key ENML Rules:**
- Must include XML declaration and DOCTYPE
- Root element is `<en-note>`, not `<html>` or `<body>`
- All tags must be lowercase and properly closed
- No `<script>`, `<form>`, `<iframe>`, or event handlers
- Inline styles only (no `class` or `id` attributes)

### Step 3: Create Your First Note

```javascript
async function createHelloWorldNote() {
  const noteStore = client.getNoteStore();

  // Define ENML content (required format)
  const content = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
  <h1>Hello from Claude Code!</h1>
  <p>This is my first note created via the Evernote API.</p>
  <p>Created at: ${new Date().toISOString()}</p>
  <hr/>
  <div style="color: #666;">
    <en-todo checked="false"/> Learn Evernote API basics<br/>
    <en-todo checked="true"/> Install SDK<br/>
    <en-todo checked="true"/> Configure authentication<br/>
  </div>
</en-note>`;

  // Create note object
  const note = new Evernote.Types.Note();
  note.title = 'Hello World - Evernote API';
  note.content = content;

  // Optional: specify notebook (uses default if not set)
  // note.notebookGuid = 'your-notebook-guid';

  try {
    const createdNote = await noteStore.createNote(note);
    console.log('Note created successfully!');
    console.log('Note GUID:', createdNote.guid);
    console.log('Note Title:', createdNote.title);
    console.log('Created:', new Date(createdNote.created));
    return createdNote;
  } catch (error) {
    console.error('Failed to create note:', error);
    throw error;
  }
}

createHelloWorldNote();
```

### Step 4: Python Version

```python
from evernote.api.client import EvernoteClient
from evernote.edam.type.ttypes import Note
import os

client = EvernoteClient(
    token=os.environ['EVERNOTE_ACCESS_TOKEN'],
    sandbox=True
)

note_store = client.get_note_store()

content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
  <h1>Hello from Python!</h1>
  <p>This note was created using the Evernote Python SDK.</p>
</en-note>'''

note = Note()
note.title = 'Hello World - Python'
note.content = content

created_note = note_store.createNote(note)
print(f'Note created: {created_note.guid}')
```

### Step 5: List Notebooks

```javascript
async function listNotebooks() {
  const noteStore = client.getNoteStore();

  const notebooks = await noteStore.listNotebooks();
  console.log('Your notebooks:');

  notebooks.forEach(notebook => {
    console.log(`- ${notebook.name} (${notebook.guid})`);
    if (notebook.defaultNotebook) {
      console.log('  ^ Default notebook');
    }
  });

  return notebooks;
}
```

### Step 6: Retrieve a Note

```javascript
async function getNote(noteGuid) {
  const noteStore = client.getNoteStore();

  // Options: withContent, withResourcesData, withResourcesRecognition, withResourcesAlternateData
  const note = await noteStore.getNote(noteGuid, true, false, false, false);

  console.log('Title:', note.title);
  console.log('Content:', note.content);
  console.log('Tags:', note.tagGuids);

  return note;
}
```


## Complete Example

```javascript
// complete-hello.js
const Evernote = require('evernote');

async function main() {
  const client = new Evernote.Client({
    token: process.env.EVERNOTE_ACCESS_TOKEN,
    sandbox: true
  });

  const noteStore = client.getNoteStore();
  const userStore = client.getUserStore();

  // 1. Get user info
  const user = await userStore.getUser();
  console.log(`Hello, ${user.username}!`);

  // 2. List notebooks
  const notebooks = await noteStore.listNotebooks();
  console.log(`You have ${notebooks.length} notebooks`);

  // 3. Create a note
  const content = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
  <p>Hello, Evernote!</p>
</en-note>`;

  const note = new Evernote.Types.Note();
  note.title = 'My First API Note';
  note.content = content;

  const created = await noteStore.createNote(note);
  console.log(`Created note: ${created.guid}`);

  // 4. Read it back
  const fetched = await noteStore.getNote(created.guid, true, false, false, false);
  console.log('Note content retrieved successfully');
}

main().catch(console.error);
```


## ENML Quick Reference

```html
<!-- Allowed -->
<p>, <div>, <span>, <br/>, <hr/>
<h1>-<h6>, <b>, <i>, <u>, <strong>, <em>
<ul>, <ol>, <li>, <table>, <tr>, <td>
<a href="...">, <img src="...">
<en-todo checked="false"/>
<en-media type="image/png" hash="..."/>

<!-- NOT Allowed -->
<script>, <form>, <input>, <button>
<iframe>, <object>, <embed>
class="...", id="...", onclick="..."
```
